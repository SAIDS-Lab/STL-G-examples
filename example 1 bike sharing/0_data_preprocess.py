import pandas as pd
import folium
import numpy as np

file_path = 'raw_data.csv'  
raw_data = pd.read_csv(file_path)
# Only keep the 'classic_bike' and drop the 'ride_id' and 'member_casual' columns
raw_data = raw_data[raw_data['rideable_type'] == 'classic_bike']
our_data = raw_data.drop(columns=['ride_id', 'member_casual'])
our_data.to_csv('our_data.csv', index=False)

# Filter for unique start_station_name entries with their lat/lng
unique_station_names = pd.concat([our_data['start_station_name'], our_data['end_station_name']]).dropna().unique()

station_dict = {}
for station_id, station in enumerate(unique_station_names, start=1):
    if station in our_data['start_station_name'].values:
        station_info = our_data[our_data['start_station_name'] == station].iloc[0][['start_lat', 'start_lng']]
    elif station in our_data['end_station_name'].values:
        station_info = our_data[our_data['end_station_name'] == station].iloc[0][['end_lat', 'end_lng']]

    station_dict[station_id] = {
        'name': station, 
        'lat': station_info['start_lat'] if station in our_data['start_station_name'].values else station_info['end_lat'],
        'lng': station_info['start_lng'] if station in our_data['start_station_name'].values else station_info['end_lng']
    }


average_lat = np.mean([station_info['lat'] for station_info in station_dict.values()])
average_lng = np.mean([station_info['lng'] for station_info in station_dict.values()])

# Initialize a map centered around the average coordinates of all stations
map_center = [average_lat, average_lng]
station_map = folium.Map(location=map_center, zoom_start=14)


# Add a marker for each station
for item in station_dict:
    folium.Marker(
        location=[station_dict[item]['lat'], station_dict[item]['lng']],
        popup=station_dict[item]['name'],
        icon=folium.Icon(color='blue', icon='bicycle', prefix='fa', icon_size=(26, 26), shadow=False)
    ).add_to(station_map)

# Save or display the map
station_map.save("start_stations_map.html")

