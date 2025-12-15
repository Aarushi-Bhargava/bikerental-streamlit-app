#from helpers import all
from helpers import *
import streamlit as st

#for map
import folium
from streamlit_folium import folium_static

#all data is from City of Toronto's official website (BikeShare)
station_url = 'https://tor.publicbikesystem.net/ube/gbfs/v1/en/station_status'
latlon_url = 'https://tor.publicbikesystem.net/ube/gbfs/v1/en/station_information'

st.title('Toronto Bike Share Station Status')
st.markdown('This dashboard tracks bike availability at each bike share station in Toronto in real time.')

data_df = query_station_status(station_url) #get stations status
latlon_df = get_station_latlon(latlon_url)
data = join_latlon(data_df, latlon_df)

#to visualize+display the table on the web
# st.dataframe(data)

col1, col2, col3 = st.columns(3) #for ui

with col1: 
#metrics displayed on the top
    st.metric(label = 'Bikes Available Now', value = sum(data['num_bikes_available']))
    st.metric(label = 'E-Bikes Available Now', value = sum(data['ebike']))

with col2:
    st.metric(label = 'Stations with Available Bikes', value = len(data[data['num_bikes_available'] > 0])) #getting the count of the number of rows where bikes avail are > 0
    st.metric(label = 'Stations with Available E-Bikes', value = len(data[data['ebike'] > 0]))

with col3:
    st.metric(label = 'Stations with Empty Docks', value = len(data[data['num_docks_available'] > 0]))

#initializing variables for user input and state
iamhere = 0
iamhere_return = 0
findmeabike = False
findmeadock = False
input_bike_modes = []

#sidebar (using input widgets)
with st.sidebar:
    bike_method = st.selectbox(
        "Are you looking to rent or return a bike?",
        ('Rent', 'Return')
    )
    if bike_method == 'Rent':
        input_bike_modes = st.multiselect(
            'What kind of bike(s) are you looking to rent?',
            ['ebike', 'mechanical']
        )
        st.header('Where are you located?')
        input_street = st.text_input('Street', "")
        input_city = st.text_input('City', 'Toronto')
        input_country = st.text_input('Country', 'Canada')

        findmeabike = st.button('Find me a bike!', type='primary')

        #when user clicks on the above button
        #covering edge cases
        if findmeabike:
            #without inputting any info, need to remind to input info
            if input_street != "": 
                iamhere = geocode(input_street + " " + input_city + " " + input_country) #concatenate a string wtih info of street, city, country, and return lat and lon
                if iamhere == "":
                    st.subheader(':red[Input address not valid!]')
            else:
                st.subheader(':red[Input address not valid!]')

    elif bike_method == 'Return':
        st.subheader('Where are you located?')
        input_street_return = st.text_input('Street', "")
        input_city_return = st.text_input('City', 'Toronto')
        input_country_return = st.text_input('Country', 'Canada')
        
        findmeadock = st.button('Find me a dock!', type='primary')
        
        if findmeadock:
            if input_street_return != "": 
                iamhere_return = geocode(input_street_return + " " + input_city_return + " " + input_country_return) #concatenate a string wtih info of street, city, country, and return lat and lon
                if iamhere_return == "":
                    st.subheader(':red[Input address not valid!]')
            else:
                st.subheader(':red[Input address not valid!]')


#initial map setup
if bike_method == "Rent" and findmeabike == False:
    #map created with folium
    center = [43.65306613746548, -79.38815311015] #coordinates for toronto
    m = folium.Map(location=center, zoom_start=12, tiles='cartodbpositron') #map with grey background

    #add dot markers for each station and labels when clicked on each
    for _, row in data.iterrows():
        marker_color = get_marker_color(row['num_bikes_available'])
        folium.CircleMarker(
            location = [row['lat'], row['lon']],
            radius = 2,
            color = marker_color,
            fill = True,
            fill_color = marker_color,
            popup = folium.Popup
                                (
                                    f"Station ID: {row['station_id']}<br>"
                                    f"Total Bikes Available Here: {row['num_bikes_available']}<br>"
                                    f"Mechanical Bikes Available Here: {row['mechanical']}<br>"
                                    f"E-Bikes Available Here: {row['ebike']}<br>"
                                )
        ).add_to(m)

    folium_static(m)

if bike_method == "Return" and findmeadock == False:
    #map created with folium
    center = [43.65306613746548, -79.38815311015] #coordinates for toronto
    m = folium.Map(location=center, zoom_start=12, tiles='cartodbpositron') #map with grey background

    #add dot markers for each station and labels when clicked on each
    for _, row in data.iterrows():
        marker_color = get_marker_color(row['num_bikes_available'])
        folium.CircleMarker(
            location = [row['lat'], row['lon']],
            radius = 2,
            color = marker_color,
            fill = True,
            fill_color = marker_color,
            popup = folium.Popup
                                (
                                    f"Station ID: {row['station_id']}<br>"
                                    f"Total Bikes Available Here: {row['num_bikes_available']}<br>"
                                    f"Mechanical Bikes Available Here: {row['mechanical']}<br>"
                                    f"E-Bikes Available Here: {row['ebike']}<br>"
                                )
        ).add_to(m)

    folium_static(m)

#logic for finding a bike
if findmeabike:    
    if input_street != "":
        
        if iamhere != "":
            chosen_station = get_bike_availability(iamhere, data, input_bike_modes)  #get bike availability (id, lat, lon)
            center = iamhere  #center the map on user's location
            
            #creating a new map (so map #2)
            m1 = folium.Map(location=center, zoom_start=16, tiles='cartodbpositron')  #create a detailed map
            
            for _, row in data.iterrows():
                marker_color = get_marker_color(row['num_bikes_available'])
                folium.CircleMarker(
                    location=[row['lat'], row['lon']],
                    radius=2,
                    color=marker_color,
                    fill=True,
                    fill_color=marker_color,
                    fill_opacity=0.7,
                    popup=folium.Popup(f"Station ID: {row['station_id']}<br>"
                                       f"Total Bikes Available: {row['num_bikes_available']}<br>"
                                       f"Mechanical Bike Available: {row['mechanical']}<br>"
                                       f"eBike Available: {row['ebike']}", max_width=300)
                ).add_to(m1)
            
            folium.Marker(
                location=iamhere,
                popup="You are here.",
                icon=folium.Icon(color="blue", icon="person", prefix="fa")
            ).add_to(m1)
            
            folium.Marker(
                location=(chosen_station[1], chosen_station[2]),
                popup="Rent your bike here.",
                icon=folium.Icon(color="red", icon="bicycle", prefix="fa")
            ).add_to(m1)
            
            coordinates, duration = run_osrm(chosen_station, iamhere)  #get route coordinates and duration
            
            folium.PolyLine(
                locations=coordinates,
                color="blue",
                weight=5,
                tooltip="it'll take you {} to get here.".format(duration),
            ).add_to(m1)
            
            folium_static(m1)  #display the map in the Streamlit app
            
            #adding a new metric to column 3
            with col3:
                st.metric(label=":green[Driving time to station (min)]", value=duration)  # Display travel time

#logic for finding a dock
if findmeadock:
    if input_street_return != "":

        if iamhere_return != "":

            chosen_station = get_dock_availability(iamhere_return, data) 
            center = iamhere_return 
            
            m1 = folium.Map(location=center, zoom_start=16, tiles='cartodbpositron')  
            
            for _, row in data.iterrows():
                marker_color = get_marker_color(row['num_bikes_available'])  
                folium.CircleMarker(
                    location=[row['lat'], row['lon']],
                    radius=2,
                    color=marker_color,
                    fill=True,
                    fill_color=marker_color,
                    fill_opacity=0.7,
                    popup=folium.Popup(f"Station ID: {row['station_id']}<br>"
                                       f"Total Bikes Available: {row['num_bikes_available']}<br>"
                                       f"Mechanical Bike Available: {row['mechanical']}<br>"
                                       f"eBike Available: {row['ebike']}", max_width=300)
                ).add_to(m1)
            
            folium.Marker(
                location=iamhere_return,
                popup="You are here.",
                icon=folium.Icon(color="blue", icon="person", prefix="fa")
            ).add_to(m1)
            
            folium.Marker(
                location=(chosen_station[1], chosen_station[2]),
                popup="Return your bike here.",
                icon=folium.Icon(color="red", icon="bicycle", prefix="fa")
            ).add_to(m1)
            
            coordinates, duration = run_osrm(chosen_station, iamhere_return)  # Get route coordinates and duration
            
            folium.PolyLine(
                locations=coordinates,
                color="blue",
                weight=5,
                tooltip="it'll take you {} to get here.".format(duration),
            ).add_to(m1)
            
            folium_static(m1) #display the map in the Streamlit app
            
            with col3:
                st.metric(label=":green[Driving time to station (min)]", value=duration)  # Display travel time