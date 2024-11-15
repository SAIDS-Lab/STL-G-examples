import pandas as pd
import googlemaps
import networkx as nx
import json
import datetime

file_path = 'our_data.csv'  
our_data = pd.read_csv(file_path)

# obtain the basic station data and save it as a json file. 
# The basic information includes station id, station name, latitude, and longitude
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

print(f"The total number of stations is: {len(station_dict)}")

with open('station_data_basic.json', 'w') as file:
    json.dump(station_dict, file)


# set up Google Maps API client
API_KEY = 'you need to put your own API key here'
gmaps = googlemaps.Client(key=API_KEY)

def get_walking_distance(lat1, lng1, lat2, lng2):
    origin = (lat1, lng1)
    destination = (lat2, lng2)
    
    # Request walking distance between two points
    result = gmaps.distance_matrix(origins=[origin], destinations=[destination], mode='walking')
    
    # Extract walking distance (in meters)
    distance = result['rows'][0]['elements'][0]['distance']['value']/ 1000 * 0.621371 # unit: miles
    return round(distance, 1)




def get_hourly_times(lat1, lng1, lat2, lng2):
    origin = (lat1, lng1)
    destination = (lat2, lng2)
    hourly_times = []

    # Generate transit times for each hour
    for hour in [0]:
        # Set the departure time to each hour of the current day
        departure_time = datetime.datetime.now().replace(year=2024, month=11, day=15, hour=hour, minute=0, second=0, microsecond=0)

        
        # Make the API request
        result_transit = gmaps.distance_matrix(
            origins=[origin],
            destinations=[destination],
            mode='transit',
            departure_time=departure_time
        )

        result_walking = gmaps.distance_matrix(
            origins=[origin],
            destinations=[destination],
            mode='walking',
            departure_time=departure_time
        )


        # Extract transit time in minutes
        transit_time = result_transit['rows'][0]['elements'][0]['duration']['value'] / 60  # in minutes
        walking_time = result_walking['rows'][0]['elements'][0]['duration']['value'] / 60  # in minutes
        hourly_times.append({
            'hour': hour,
            'transit_time': round(transit_time, 1),
            'walking_time': round(walking_time, 1)
        })

    return hourly_times



# # Example usage
# lat1, lng1 = 37.7749, -122.4194  # Replace with your origin coordinates
# lat2, lng2 = 37.7849, -122.4094  # Replace with your destination coordinates

# transit_times = get_hourly_transit_times(lat1, lng1, lat2, lng2)
# for item in transit_times:
#     print(f"Hour: {item['hour']}, Transit Time: {item['transit_time_minutes']} minutes")





# G_dist = nx.DiGraph()

# # add nodes
# for station_id, station_info in station_dict.items():
#     G_dist.add_node(station_id, lat=station_info['lat'], lng=station_info['lng'])

# # add edges and weights
# # i = 0
# for station_id_1, info_1 in station_dict.items():
#     for station_id_2, info_2 in station_dict.items():
#         # i = i + 1
#         # if i > 10:
#         #     break
#         if station_id_1 != station_id_2: # to avoid self loop
#             lat1, lng1 = info_1['lat'], info_1['lng']
#             lat2, lng2 = info_2['lat'], info_2['lng']
#             walking_distance = get_walking_distance(lat1, lng1, lat2, lng2)
#             G_dist.add_edge(station_id_1, station_id_2, weight=walking_distance)

# print(f"Number of nodes: {len(G_dist.nodes)}")
# print(f"Number of edges: {len(G_dist.edges)}")

# nx.write_gexf(G_dist, "distance_graph.gexf")






for hour in [0]:
    print(hour)
    G_time = nx.MultiDiGraph()

    # add nodes
    for station_id, station_info in station_dict.items():
        G_time.add_node(station_id, lat=station_info['lat'], lng=station_info['lng'])

    # add edges and weights
    i = 0
    for station_id_1, info_1 in station_dict.items():
        for station_id_2, info_2 in station_dict.items():
            i = i + 1
            if i%1000 == 0:
                print(i)
            if station_id_1 != station_id_2: # to avoid self loop
                lat1, lng1 = info_1['lat'], info_1['lng']
                lat2, lng2 = info_2['lat'], info_2['lng']
                hourly_times = get_hourly_times(lat1, lng1, lat2, lng2)
                G_time.add_edge(station_id_1, station_id_2, key='transit', weight=hourly_times[hour]['transit_time'])
                G_time.add_edge(station_id_1, station_id_2, key='walking', weight=hourly_times[hour]['walking_time'])


    nx.write_gexf(G_time, f"time_graph/time_graph_{hour}.gexf")




