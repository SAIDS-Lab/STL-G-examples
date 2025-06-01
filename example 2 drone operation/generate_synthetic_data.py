import numpy as np
import random
import params_size_500 as params  # Adjust the import based on your params file for different monitoring setting.
import math
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.animation as animation
import matplotlib.image as mpimg
from itertools import combinations
import json

random.seed(params.my_seed)

# Function to calculate Euclidean distance
def euclidean_distance(loc1, loc2):
    return math.sqrt((loc1[0] - loc2[0])**2 + (loc1[1] - loc2[1])**2)

# Function to generate random station locations
def generate_random_stations(map_size, num_stations):
    return [(random.randint(0, map_size[0] - 1), random.randint(0, map_size[1] - 1)) for _ in range(num_stations)]

def simulate_wildfire():
    map_size = params.setting["map_size"]
    horizon = params.setting["horizon"]
    drone_speeds = params.setting["drone_speeds"]
    num_drones = len(drone_speeds)

    station_locations = generate_random_stations(map_size, num_drones)
    params.setting["station_locations"] = station_locations

    wildfire_map = np.zeros(map_size, dtype=int)
    map_info = [wildfire_map.copy()]

    drones = [{"location": station_locations[i], "station_location": station_locations[i], 
               "available": True, "returning": False, "fire_location": None, 
               "extinguish_countdown": 0, "speed": speed}
              for i, speed in enumerate(drone_speeds)]
    drone_trajectories = {i: [station_locations[i]] for i in range(num_drones)}

    targeted_fires = set()

    def ignite_random_fire():
        x = random.randint(0, map_size[0] - 1)
        y = random.randint(0, map_size[1] - 1)
        if wildfire_map[x, y] == 0:
            wildfire_map[x, y] = 1

    def move_towards(drone, target):
        dx, dy = target[0] - drone["location"][0], target[1] - drone["location"][1]
        distance = euclidean_distance(drone["location"], target)
        if distance <= drone["speed"]:
            drone["location"] = target
        else:
            factor = drone["speed"] / distance
            new_x = drone["location"][0] + factor * dx
            new_y = drone["location"][1] + factor * dy
            drone["location"] = (new_x, new_y)

    def dispatch_drone():
        fire_locations = np.argwhere(wildfire_map == 1)
        if fire_locations.size == 0:
            return
        for i, drone in enumerate(drones):
            if drone["available"]:
                nearest_fire = None
                min_distance = float("inf")
                for fire in fire_locations:
                    fire_location = tuple(fire)
                    if fire_location not in targeted_fires:
                        distance = euclidean_distance(drone["location"], fire_location)
                        if distance < min_distance:
                            min_distance = distance
                            nearest_fire = fire_location
                
                if nearest_fire is not None:
                    drone["fire_location"] = nearest_fire
                    drone["available"] = False
                    targeted_fires.add(nearest_fire)
                    break

    for time_step in range(horizon):
        if random.random() < 0.05:
            ignite_random_fire()

        for i, drone in enumerate(drones):
            if not drone["available"]:
                if drone["extinguish_countdown"] > 0:
                    drone["extinguish_countdown"] -= 1
                    if drone["extinguish_countdown"] == 0:
                        fire_x, fire_y = drone["fire_location"]
                        wildfire_map[fire_x, fire_y] = 0
                        drone["returning"] = True
                        targeted_fires.discard((fire_x, fire_y))

                elif drone["returning"]:
                    if euclidean_distance(drone["location"], drone["station_location"]) <= drone["speed"]:
                        drone["location"] = drone["station_location"]
                        drone["available"] = True
                        drone["returning"] = False
                        drone["fire_location"] = None
                    else:
                        move_towards(drone, drone["station_location"])

                else:
                    target = drone["fire_location"]
                    if euclidean_distance(drone["location"], target) <= drone["speed"]:
                        drone["location"] = target
                        drone["extinguish_countdown"] = 5
                    else:
                        move_towards(drone, target)

            drone_trajectories[i].append(drone["location"])

        dispatch_drone()
        map_info.append(wildfire_map.copy())

    return map_info, drone_trajectories

def animate_wildfire(map_info, drone_trajectories):
    plt.rcParams["font.family"] = "Times New Roman"
    plt.rcParams["font.size"] = 14  # Increase the default font size

    background_img = mpimg.imread("map.png")
    
    fig, axs = plt.subplots(2, 2, figsize=(12, 10))
    ax_left = axs[0, 0]
    ax_right = axs[0, 1]
    ax_d_left = axs[1, 0]
    ax_d_right = axs[1, 1]

    # Load and display background images
    ax_left.imshow(background_img, extent=(0, map_info[0].shape[1], 0, map_info[0].shape[0]), zorder=1)
    ax_right.imshow(background_img, extent=(0, map_info[0].shape[1], 0, map_info[0].shape[0]), zorder=1)
    ax_d_left.imshow(background_img, extent=(0, map_info[0].shape[1], 0, map_info[0].shape[0]), zorder=1)
    ax_d_right.imshow(background_img, extent=(0, map_info[0].shape[1], 0, map_info[0].shape[0]), zorder=1)

    # Set titles with larger font sizes
    ax_left.set_title("(a) Animation Frame", fontsize=16)
    ax_right.set_title("(b) Distance Graph (unit = 0.1 mile(s))", fontsize=16)
    ax_d_left.set_title("(c) Communication Graph", fontsize=16)
    ax_d_right.set_title(f"(d) Sensing Graph (sensor threshold = {params.sensing_threshold * params.distance_factor} mile(s))", fontsize=16)

    cmap = mcolors.ListedColormap(["white", "red"])
    bounds = [0, 0.5, 1]
    norm = mcolors.BoundaryNorm(bounds, cmap.N)
    
    # Display initial fire maps on each subplot
    fire_plot_left = ax_left.imshow(map_info[0], cmap=cmap, norm=norm, interpolation="nearest", alpha=0.3, zorder=2)
    fire_plot_right = ax_right.imshow(map_info[0], cmap=cmap, norm=norm, interpolation="nearest", alpha=0.3, zorder=2)
    fire_plot_d_left = ax_d_left.imshow(map_info[0], cmap=cmap, norm=norm, interpolation="nearest", alpha=0.3, zorder=2)
    fire_plot_d_right = ax_d_right.imshow(map_info[0], cmap=cmap, norm=norm, interpolation="nearest", alpha=0.3, zorder=2)

    # Plot stations on each subplot
    house_img = mpimg.imread("house.jpg")
    for station_location in params.setting["station_locations"]:
        for ax in [ax_left, ax_right, ax_d_left, ax_d_right]:
            ax.imshow(house_img, extent=(station_location[1] - 1, station_location[1] + 1,
                                         station_location[0] - 1, station_location[0] + 1), zorder=3)

    drone_colors = plt.get_cmap("tab10")
    drone_plots = {
        ax: [
            ax.plot([], [], "o", color=drone_colors(i / len(drone_trajectories)), markersize=6, label=f"Drone {i + 1}")[0]
            for i in range(len(drone_trajectories))
        ]
        for ax in [ax_left, ax_right, ax_d_left, ax_d_right]
    }

    # Thicker lines for all edges in distance, communication, and sensing plots
    distance_lines, distance_texts = [], []
    for (i, j) in combinations(range(len(drone_trajectories)), 2):
        line, = ax_right.plot([], [], ":", color="gray", lw=1.5, zorder=2)
        distance_lines.append(line)
        text = ax_right.text(0, 0, '', color="black", fontsize=10)
        distance_texts.append(text)

    communication_lines, communication_texts = [], []
    communication_topology = []
    n = len(drone_trajectories)
    half = n // 2
    for i in range(n):
        for j in range(n):
            if (i != j and ((i < half and j < half) or (i >= half and j >= half))) and (j, i) not in communication_topology:
                communication_topology.append((i, j))
    for (i, j) in communication_topology:
        line, = ax_d_left.plot([], [], "-", color="blue", lw=1.5, zorder=2)
        communication_lines.append(line)
        text = ax_d_left.text(0, 0, '1', color="blue", fontsize=10)
        communication_texts.append(text)

    sensing_lines, sensing_texts = [], []
    sensing_topology = []
    n = len(drone_trajectories)
    half = n // 2
    for i in range(n):
        for j in range(n):
            if (i != j and ((i < half and j < half) or (i >= half and j >= half))) and (j, i) not in sensing_topology:
                sensing_topology.append((i, j))
    for (i, j) in sensing_topology:
        line, = ax_d_right.plot([], [], "-", color="green", lw=1.5, zorder=2)
        sensing_lines.append(line)
        text = ax_d_right.text(0, 0, '1', color="green", fontsize=10)
        sensing_texts.append(text)

    def update(frame):
        fire_plot_left.set_data(map_info[frame])
        fire_plot_right.set_data(map_info[frame])
        fire_plot_d_left.set_data(map_info[frame])
        fire_plot_d_right.set_data(map_info[frame])

        for ax in [ax_left, ax_right, ax_d_left, ax_d_right]:
            for i, drone_plot in enumerate(drone_plots[ax]):
                if frame < len(drone_trajectories[i]):
                    drone_location = drone_trajectories[i][frame]
                    if isinstance(drone_location, tuple):
                        drone_plot.set_data([drone_location[1]], [drone_location[0]])

        for (i, j), line, text in zip(combinations(range(len(drone_trajectories)), 2), distance_lines, distance_texts):
            loc_i, loc_j = drone_trajectories[i][frame], drone_trajectories[j][frame]
            if isinstance(loc_i, tuple) and isinstance(loc_j, tuple):
                line.set_data([loc_i[1], loc_j[1]], [loc_i[0], loc_j[0]])
                distance = euclidean_distance(loc_i, loc_j)
                text.set_position(((loc_i[1] + loc_j[1]) / 2, (loc_i[0] + loc_j[0]) / 2))
                text.set_text(f"{distance:.2f}")

        for (i, j), line, text in zip(communication_topology, communication_lines, communication_texts):
            loc_i, loc_j = drone_trajectories[i][frame], drone_trajectories[j][frame]
            if isinstance(loc_i, tuple) and isinstance(loc_j, tuple):
                line.set_data([loc_i[1], loc_j[1]], [loc_i[0], loc_j[0]])
                text.set_position(((loc_i[1] + loc_j[1]) / 2, (loc_i[0] + loc_j[0]) / 2))

        for (i, j), line, text in zip(sensing_topology, sensing_lines, sensing_texts):
            loc_i, loc_j = drone_trajectories[i][frame], drone_trajectories[j][frame]
            if isinstance(loc_i, tuple) and isinstance(loc_j, tuple):
                distance = euclidean_distance(loc_i, loc_j)
                if distance <= params.sensing_threshold:
                    line.set_data([loc_i[1], loc_j[1]], [loc_i[0], loc_j[0]])
                    text.set_position(((loc_i[1] + loc_j[1]) / 2, (loc_i[0] + loc_j[0]) / 2))
                    text.set_text('1')
                else:
                    line.set_data([], [])
                    text.set_text('')

        return sum(drone_plots.values(), []) + distance_lines + distance_texts + communication_lines + communication_texts + sensing_lines + sensing_texts

    # Adjust spacing between subplots and reduce figure margins further
    plt.tight_layout()
    # Create legend with Times New Roman font
    handles = [plt.Line2D([0], [0], marker='o', color='w', label=f"Drone {i + 1}", markersize=6, markerfacecolor=drone_colors(i / len(drone_trajectories))) for i in range(len(drone_trajectories))]
    fig.legend(handles=handles, loc="center right", title="Drones", title_fontsize='14', fontsize='12')

    ani = animation.FuncAnimation(fig, update, frames=len(map_info), interval=200, blit=False)
    ani.save("wildfire_simulation_size_500.gif", writer="pillow", fps=5) # Change the filename as needed

map_info, drone_trajectories = simulate_wildfire()

save_animation = False
if save_animation:
    animate_wildfire(map_info, drone_trajectories)
save_data = True
if save_data:
    float_trajectories = {k: [[float(x) for x in loc] for loc in v] for k, v in drone_trajectories.items()}
    float_map_info = [map_info[i].tolist() for i in range(len(map_info))]
    with open("simulation_data_size_500.json", "w") as f:
        json.dump({"map_info": float_map_info, "drone_trajectories": float_trajectories}, f)

