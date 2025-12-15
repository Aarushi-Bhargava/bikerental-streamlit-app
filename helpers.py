import urllib #to open data from a website (url)
import json #to read json data
import pandas as pd #to work with tables (rows and columns)
import folium #for creating interactive maps
import datetime as dt #to work with dates & times
from geopy.distance import geodesic #for calculating distances between coordinates
from geopy.geocoders import Nominatim #for geocoding addresses (convert an address to lat/long)
import streamlit as st #for creating web apps
import requests #for making HTTP requests

@st.cache_data #decorator, cache the output to improve runtime performance

#to prevent geopy.exc.GeocoderUnavailable (too many fast api requests or nominatim reaching limit)
def geocode(address):
    
    geolocator = Nominatim(
        user_agent="bikerental_streamlit_app",
        timeout=10
    )
    location = geolocator.geocode(address)
    
    if location is None:
        return None
    
    return (location.latitude, location.longitude)

#this function takes a URL and returns a clean table of bike stations
def query_station_status(url):
    #go the url and open it
    with urllib.request.urlopen(url) as data_url:
        data = json.loads(data_url.read().decode()) #read the data and convert from json to a python dictionary (key --> value structure)

    df = pd.DataFrame(data['data']['stations']) #extracts the 'stations' list and converts it to dataframe
    #only keep station where bikes can be returned, where biks can be returned
    df = df[df.is_renting == 1] #filtering out stations that are not renting
    df = df[df.is_returning == 1] #filtering out stations that are not returning

    df = df.drop_duplicates(['station_id', 'last_reported']) #remove duplicate records

    df = df.dropna(subset=['last_reported']) #drop rows where last_reported is missing (NaN) before converting below

    df.last_reported = df.last_reported.map(lambda x: dt.datetime.utcfromtimestamp(x)) #convert unix timestamp returend by API (seconds since 1970) to human readable date time #what api?

    df['time'] = data['last_updated'] #add the last updated time to the dataframe
    df.time = df.time.map(lambda x: dt.datetime.utcfromtimestamp(x)) #convert unix timestamp to human readable date time

    df = df.set_index('time') #set the index of the dataframe to the time column
    df.index = df.index.tz_localize('UTC') #set the timezone to UTC

    df = pd.concat([df, df['num_bikes_available_types'].apply(pd.Series)], axis=1) #expand the nested dictionary in 'num_bikes_available_types' into separate columns 'ebike' and 'mechanical'

    return df #return the cleaned dataframe

#this function gets the station lat and long from a given URL: downloads station info, extracts lat and long, returns a table
def get_station_latlon(url):
    with urllib.request.urlopen(url) as data_url: #go to URL and open it
        latlon = json.loads(data_url.read().decode()) #read and decode the json data
    latlon = pd.DataFrame(latlon['data']['stations']) #convert the data to df

    return latlon #return the dataframe with lat and lon

#this function creates the main dataframe that this project uses
#this function joins the two dataframes: station status and station lat/lon
#combines availability data (df1) and location data (df2)
def join_latlon(df1, df2):
    #match rows where station_id is the same in both dataframes
    df = df1.merge(df2[['station_id', 'lat', 'lon']],
                   how='left',
                   on='station_id') #merge the two dataframes on station_id, keeping all records from df1
    
    return df #return the merged dataframe

#this function determines marker color (dot) based on the number of bikes available
def get_marker_color(num_bikes_available):
    if num_bikes_available > 3:
        return 'green'
    elif 0 < num_bikes_available <= 3:
        return 'yellow'
    else:
        return 'red'
    
#this function geocodes an address to lat/lon using Nominatim
def geocode(address):
    geolocator = Nominatim(user_agent="clicked-demo") #create a geolocator object
    location = geolocator.geocode(address) #geocode the address
    if location is None:
        return ''
    else:
        return (location.latitude, location.longitude)
    
#this function gets bike availability near a location
def get_bike_availability(latlon, df, input_bike_modes): #input_bike_modes is a list that comes from user input (whether user chose none or only ebike or only mechanical or ebike and mechanical)
    """Calculate distance from each station to the user and return a single station id, lat, lon"""
    if len(input_bike_modes) == 0 or len(input_bike_modes) == 2: #if user selected nothing (num of items in input_bike_modes list will be 0) or if user selected both (num of items in input_bike_modes list will be 2) 
        i = 0 #loop counter
        df['distance'] = '' #created a new column in df
        while i < len(df):
            #row number 'i' and column 'distance'        lat of station 'i', long of station 'i'
            df.loc[i, 'distance'] = geodesic(latlon, (df['lat'][i], df['lon'][i])).km #calculate distance to each station
            #geodisc(A, B) real world earth distance
            i = i +1

        #filtering out stations (removing useless ones)
        #only keeping rows where the below conditions are true
        df = df.loc[(df['ebike'] > 0) | (df['mechanical'] > 0)] #remove station with no available ebikes or no available mechanical bikes
        chosen_station = []

        #finds the row in the df where the value of 'distance' column is the smallest. it then extracts the values from the 'station_id', 'lat', and 'lon' columns of that row and appends them to the chosen_station list.
        #give me the row where the distance is the smallest from my location
        #iloc[0] means only taking the first row, in case there are ties
        chosen_station.append(df[df['distance'] == min(df['distance'])]['station_id'].iloc[0])
        chosen_station.append(df[df['distance'] == min(df['distance'])]['lat'].iloc[0])
        chosen_station.append(df[df['distance'] == min(df['distance'])]['lon'].iloc[0])

    else: #if user selects either ebike OR mechanical
        i = 0
        df['distance'] = ''
        while i < len(df):
            df.loc[i, 'distance'] = geodesic(latlon, (df['lat'][i], df['lon'][i])).km #calculate distance to each station
            i = i +1
        
        df = df.loc[df[input_bike_modes[0]] > 0] #only keep stattions with at least one of the selected bike mode
        chosen_station = []
        chosen_station.append(df[df['distance'] == min(df['distance'])]['station_id'].iloc[0])
        chosen_station.append(df[df['distance'] == min(df['distance'])]['lat'].iloc[0])
        chosen_station.append(df[df['distance'] == min(df['distance'])]['lon'].iloc[0])
        
    return chosen_station #return the chosen station, sends back [station_id, lat, lon]

def get_dock_availability(latlon, df):
    """Calculate distnace from each station to the user and return a single station id, lat, lon"""

    i = 0
    df['distance'] = ''
    while i < len(df):
        df.loc[i, 'distance'] = geodesic(latlon, (df['lat'][i], df['lon'][i])).km #calculation distance to each station
        i = i +1

    df = df.loc[df['num_docks_available'] > 0] #remove stations without available docks

    chosen_station = []
    chosen_station.append(df[df['distance'] == min(df['distance'])]['station_id'].iloc[0])
    chosen_station.append(df[df['distance'] == min(df['distance'])]['lat'].iloc[0])
    chosen_station.append(df[df['distance'] == min(df['distance'])]['lon'].iloc[0])

    return chosen_station #returns the chosen station list which contains the station_id, lat, lon of the closest station with available docks

#this function handles 'how do i get from where i am to the chosen bike station?' then calls a routing service (OSRM), gets the path as a series of GPS points, gets travel time, and returns both
#osrm = open source routing machine, can talk to it using an HTTP API
def run_osrm(chosen_station, iamhere):
    
    # "{},{}".format(lat, lon)
    # iamhere = (lat, lon)
    # chosen_station = [station_id, lat, lon]

    #osrm expects lon, lat

    #first element (0) of iamhere list is lat, second element (1) is lon
    start = "{},{}".format(iamhere[1], iamhere[0]) #format the start coordinates
    
    #first element (0) of chosen_list is station_id, second element (1) is lat, third element (2) is lon
    end = "{},{}".format(chosen_station[2], chosen_station[1]) #format the end coordinates

    #building the api url: i want driving directions from start to end as GeoJSON (map-friendly)
    url = 'http://router.project-osrm.org/route/v1/driving/{};{}?geometries=geojson'.format(start, end) #create the OSRM API URL

    #making the request, the API call
    headers = {'Content-type': 'application/json'}
    r = requests.get(url, headers=headers) #sends an HTTP GET request, OSRM server receives it, server computes the route, server sends JSON back
    print("Calling API ...:", r.status_code) #for debugging (200=success, 400=bad request, 500=server error)

    routejson = r.json() #parse the json response, converting json to a python dictionary
    coordinates = []
    i = 0

    #list of routes, taking the best one, path shape, list of points
    lst = routejson['routes'][0]['geometry']['coordinates']
    while i < len(lst):
        #from OSRM we get (lon (0), lat (1)) but mapping libraries expect (lat (1), lon (0))
        coordinates.append([lst[i][1], lst[i][0]]) #flipping the OSRM given coordinates
        i = i +1
    duration = round(routejson['routes'][0]['duration'] / 60, 1) #convert duration to minutes

    return coordinates, duration #return the coordinates and duration
