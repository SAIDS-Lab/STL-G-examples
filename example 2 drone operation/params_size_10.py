my_seed = 123456
drone_speed_first_half = [1 for _ in range(5)]
drone_speed_second_half = [0.5 for _ in range(5)]
drone_speeds = drone_speed_first_half + drone_speed_second_half
setting = {
    "map_size": (45, 45),
    "horizon": 90,
    "drone_speeds": drone_speeds,  # Speeds of the 5 drones,
    "epsilon": 1
}
distance_factor = 0.1 # per mile
sensing_threshold = 10