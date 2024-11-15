import pandas as pd
from collections import defaultdict
import json

with open('station_data_basic.json', 'r') as file:
    station_dict = json.load(file)

file_path = 'our_data.csv'  
our_data = pd.read_csv(file_path)

unique_station_names = pd.concat([our_data['start_station_name'], our_data['end_station_name']]).unique()

# #########################################################################################
# this part is used to decide the initial number of bikes at each station
our_data['started_at'] = pd.to_datetime(our_data['started_at'])
our_data['ended_at'] = pd.to_datetime(our_data['ended_at'])

# Filter for trips on October 1, 2024
oct_1_data = our_data[(our_data['started_at'].dt.date == pd.to_datetime('2024-10-01').date()) &
             (our_data['ended_at'].dt.date == pd.to_datetime('2024-10-01').date())]

# Extract hour for start and end times
oct_1_data['start_hour'] = oct_1_data['started_at'].dt.hour
oct_1_data['end_hour'] = oct_1_data['ended_at'].dt.hour

# Dictionary to store hourly deficits for each station
station_hourly_balance = defaultdict(lambda: [0] * 24)

# Calculate hourly net bike changes for each station
for _, row in oct_1_data.iterrows():
    start_station = row['start_station_name']
    end_station = row['end_station_name']
    start_hour = row['start_hour']
    end_hour = row['end_hour']
    
    # Each start decreases the count at the start station for the hour
    station_hourly_balance[start_station][start_hour] -= 1
    
    # Each end increases the count at the end station for the hour
    station_hourly_balance[end_station][end_hour] += 1

# Calculate minimum bikes needed at midnight for each station
min_bikes_required = {}
for station, hourly_changes in station_hourly_balance.items():
    current_balance = 0
    min_required = 0
    for hour_change in hourly_changes:
        current_balance += hour_change
        min_required = min(min_required, current_balance)
    
    # Minimum required at midnight to keep non-negative balance
    min_bikes_required[station] = max(0, -min_required)

# Convert to DataFrame and save
min_bikes_df = pd.DataFrame(list(min_bikes_required.items()), columns=['Station', 'Min_Bikes_Required'])
min_bikes_df.to_csv('min_bikes_required_hourly.csv', index=False)


# #########################################################################################











import pandas as pd

# Parse the date columns
our_data['started_at'] = pd.to_datetime(our_data['started_at'])
our_data['ended_at'] = pd.to_datetime(our_data['ended_at'])

# Initialize a dictionary to store hourly data for each day in October
all_data = {}

# Loop through each day in October
for day in range(1, 32):  # 1 to 31 for October
    # Define the current date
    current_date = pd.Timestamp(f'2024-10-{day:02d}')
    
    # Filter data for the current date
    daily_data = our_data[
        (our_data['started_at'].dt.date == current_date.date()) |
        (our_data['ended_at'].dt.date == current_date.date())
    ]
    
    # Initialize dictionaries to store hourly counts for this day
    start_counts = {}
    end_counts = {}
    
    # Loop through each hour of the day
    for hour in range(24):
        start_time = current_date + pd.Timedelta(hours=hour)
        end_time = start_time + pd.Timedelta(hours=1)

        # Filter data for bikes that start and end within the hour
        start_hourly = daily_data[(daily_data['started_at'] >= start_time) & (daily_data['started_at'] < end_time)]
        start_counts[hour] = start_hourly['start_station_name'].value_counts().to_dict()

        end_hourly = daily_data[(daily_data['ended_at'] >= start_time) & (daily_data['ended_at'] < end_time)]
        end_counts[hour] = end_hourly['end_station_name'].value_counts().to_dict()

    # Convert start and end counts for the day into DataFrames
    start_counts_df = pd.DataFrame(start_counts).fillna(0).astype(int)
    end_counts_df = pd.DataFrame(end_counts).fillna(0).astype(int)

    # Merge start and end counts into a single DataFrame with suffixes
    daily_merged_df = pd.merge(
        start_counts_df, end_counts_df, left_index=True, right_index=True, suffixes=('_start', '_end')
    )
    
    # Store the day's DataFrame in all_data dictionary with the date as key
    all_data[current_date.date()] = daily_merged_df

# Combine all daily DataFrames into one large DataFrame with a multi-level index
combined_df = pd.concat(all_data, names=['Date', 'Station'])
combined_df.to_csv('october_hourly_bike_counts.csv')





def get_bike_counts(all_data, day, station, hour):
    current_date = pd.Timestamp(f'2024-10-{day:02d}')
    daily_data = all_data[current_date.date()]

    start_col = f'{hour}_start'
    end_col = f'{hour}_end'
    
    start_count = daily_data.at[station, start_col] if station in daily_data.index else 0
    end_count = daily_data.at[station, end_col] if station in daily_data.index else 0
    
    return int(start_count), int(end_count)

# station = 'Hoboken Terminal - River St & Hudson Pl'  # 查询站点名称
# hour = 9  # 查询9点的出发和结束计数
# start_count, end_count = get_bike_counts(all_data, 1, station, hour)
# print(start_count, end_count)


# Initialize state dictionary for each station with initial bike count
# Create a dictionary of initial bike counts based on Min_Bikes_Required
initial_state = {}
for index, row in min_bikes_df.iterrows():
    station = row['Station']
    min_bikes_required = row['Min_Bikes_Required']
    # Set initial bike count based on the min bikes required
    initial_state[station] = 10 if min_bikes_required <= 8 else 20

for station in unique_station_names:
    if station not in initial_state:
        initial_state[station] = 10



station_states = {}

for station, initial_bikes in initial_state.items():
    # Start each station's sequence with the initial state [n_0, 0, 0]
    station_states[station] = {}
    for day in range(1, 32):
        station_states[station][day] = [[initial_bikes, start_counts.get(0, {}).get(station, 0), end_counts.get(0, {}).get(station, 0)]]


for station in station_states.keys():
    for day in range(1, 32):
        for hour in range(1, 24):
            # Get the current state (previous hour's values)
            current_state = station_states[station][day][-1]  # [n_t, n_t^{in}, n_t^{out}]
            
            start_count, end_count = get_bike_counts(all_data, day, station, hour)
            
            # Calculate n_{t+1}
            n_next = current_state[0] + current_state[1] - current_state[2]
            
            # Append new state [n_{t+1}, n_t^{in}, n_t^{out}] to the station's sequence
            station_states[station][day].append([n_next, start_count, end_count])
        

# # Flatten the state data into a list of rows for each station-hour pair
# rows = []
# for station, states in station_states.items():
#     for hour, state in enumerate(states):
#         rows.append([station, hour] + state)  # [station, hour, n_t, n_t^{in}, n_t^{out}]

for station_id, station_data in station_dict.items():
    station_name = station_data['name']
    # Add initial_bikes based on Min_Bikes_Required logic
    station_dict[station_id]['state'] = station_states.get(station_name) 



with open('station_data.json', 'w') as file:
    json.dump(station_dict, file)



# print("station_dict name:", station_dict)
