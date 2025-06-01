from generate_synthetic_data import euclidean_distance
import json
import random
import params_size_500 as params  # Import the parameters from the params file. Change this to the appropriate params file for your simulation.
import time

random.seed(params.my_seed)

class MAS:
    def __init__(self, trajectories):
        self.trajectories = trajectories
        self.agents = [key for key in trajectories.keys()]
        print("Generating distance graphs...")
        self.distance_graphs = [self.generate_distance_graph(tau) for tau in range(params.setting["horizon"])]
        # Generate topology.
        print("Constructing topology...")
        topology = []
        n = len(self.agents)
        half = n // 2
        for i in self.agents:
            for j in self.agents:
                if i != j and ((i < half and j < half) or (i >= half and j >= half)):
                    topology.append((i, j))
        print("Generating communication and sensing graphs...")
        communication_graph = self.generate_communication_graph(topology)
        self.communication_graphs = [communication_graph for _ in range(params.setting["horizon"])]
        print("Generating sensing graphs...")
        self.sensing_graphs = [self.generate_sensing_graph(tau, topology) for tau in range(params.setting["horizon"])]
    
    def generate_distance_graph(self, tau):
        # Generate a graph of distances between all pairs of points.
        distance_graph = {}
        for i in self.agents:
            for j in self.agents:
                if i != j:
                    distance_graph[(i, j)] = euclidean_distance(self.trajectories[i][tau], self.trajectories[j][tau])
        return distance_graph

    def generate_communication_graph(self, topology):
        # Generate a graph of communication between all pairs of points.
        communication_graph = {}
        for (i, j) in topology:
            communication_graph[(i, j)] = 1
        return communication_graph

    def generate_sensing_graph(self, tau, topology):
        # Generate a graph of sensing between all pairs of points.
        sensing_graph = {}
        for (i, j) in topology:
            if self.distance_graphs[tau][(i, j)] <= params.sensing_threshold:
                sensing_graph[(i, j)] = 1
        return sensing_graph


def report_true_false_indices(boolean_list):
    true_indices = [index for index, value in enumerate(boolean_list) if value is True]
    false_indices = [index for index, value in enumerate(boolean_list) if value is False]
    return {"True Indices": true_indices, "False Indices": false_indices, "Number of True": len(true_indices), "Number of False": len(false_indices)}
    

def monitor_varphi_3(mas, ego_agent, current_time, global_range = 2, safe_range = 3):
    inner_monitoring_results = dict()
    for tau in range(current_time, current_time + global_range + 1):
        # Figure out the number of neighbors that are at least 3 away from the ego agent.
        neighbors = 0
        for agent in mas.agents:
            if agent != ego_agent:
                if mas.distance_graphs[tau][(ego_agent, agent)] >= safe_range:
                    neighbors += 1
        if neighbors == len(mas.agents) - 1:
            inner_monitoring_results[tau] = True
        else:
            inner_monitoring_results[tau] = False
    # Now, monitor the outer specification.
    outer_logic = True
    for i in range(current_time, current_time + global_range + 1):
        outer_logic = outer_logic and inner_monitoring_results[i]
    return outer_logic

def monitor_varphi_4(mas, ego_agent, current_time, eventually_range = 2):
    inner_sensing_monitoring_results = dict()
    for tau in range(current_time, current_time + eventually_range + 1):
        # Figure out the number of neighbors that are at least 3 away from the ego agent.
        neighbors = 0
        for agent in mas.agents:
            if agent != ego_agent:
                if (ego_agent, agent) in mas.sensing_graphs[tau]:
                    neighbors += 1
        if neighbors >= 1 and neighbors <= len(mas.agents) - 1:
            inner_sensing_monitoring_results[tau] = True
        else:
            inner_sensing_monitoring_results[tau] = False
    inner_communication_monitoring_results = dict()
    for tau in range(current_time, current_time + eventually_range + 1):
        # Figure out the number of neighbors that are at least 3 away from the ego agent.
        neighbors = 0
        for agent in mas.agents:
            if agent != ego_agent:
                if (ego_agent, agent) in mas.communication_graphs[tau]:
                    neighbors += 1
        if neighbors >= 1 and neighbors <= len(mas.agents) - 1:
            inner_communication_monitoring_results[tau] = True
        else:
            inner_communication_monitoring_results[tau] = False
    # Now, monitor the and specification.
    and_monitoring_results = dict()
    for tau in range(current_time, current_time + eventually_range + 1):
        and_monitoring_results[tau] = inner_sensing_monitoring_results[tau] and inner_communication_monitoring_results[tau]
    # Now, monitor the outer specification.
    outer_logic = False
    for i in range(current_time, current_time + eventually_range + 1):
        outer_logic = outer_logic or and_monitoring_results[i]
    return outer_logic

def monitor_phi_3(mas, current_time, global_range = 2, safe_range = 3):
    inner_monitoring_results = dict()
    for ego_agent in mas.agents:
        inner_monitoring_results[ego_agent] = dict()
        for tau in range(current_time, current_time + global_range + 1):
            neighbors = 0
            for agent in mas.agents:
                if agent != ego_agent:
                    if mas.distance_graphs[tau][(ego_agent, agent)] >= safe_range:
                        neighbors += 1
            if neighbors == len(mas.agents) - 1:
                inner_monitoring_results[ego_agent][tau] = True
            else:
                inner_monitoring_results[ego_agent][tau] = False
    # Compute the and results.
    and_monitoring_results = dict()
    for tau in range(current_time, current_time + global_range + 1):
        and_monitoring_results[tau] = True
        for ego_agent in mas.agents:
            and_monitoring_results[tau] = and_monitoring_results[tau] and inner_monitoring_results[ego_agent][tau]
    # outer results.
    outer_logic = True
    for i in range(current_time, current_time + global_range + 1):
        outer_logic = outer_logic and and_monitoring_results[i]
    return outer_logic


def monitor_phi_4(mas, current_time, ego_agent, global_range = 2):
    # Compute the predicate results.
    predicate_results = dict()
    for tau in range(current_time, current_time + global_range + 1):
        predicate_results[tau] = dict()
        for agent in mas.agents:
            predicate_results[tau][agent] = euclidean_distance(mas.trajectories[ego_agent][tau], mas.trajectories[agent][tau]) <= 10
    # Compute the not results.
    not_results = dict()
    for tau in range(current_time, current_time + global_range + 1):
        not_results[tau] = dict()
        for agent in mas.agents:
            not_results[tau][agent] = not predicate_results[tau][agent]
    # Compute the sensing results.
    sensing_results = dict()
    for tau in range(current_time, current_time + global_range + 1):
        sensing_results[tau] = dict()
        for agent in mas.agents:
            sensing_results[tau][agent] = (ego_agent, agent) in mas.sensing_graphs[tau]
    # Compute the communication results.
    communication_results = dict()
    for tau in range(current_time, current_time + global_range + 1):
        communication_results[tau] = dict()
        for agent in mas.agents:
            communication_results[tau][agent] = (ego_agent, agent) in mas.communication_graphs[tau]
    # Compute the inner or results.
    inner_or_results = dict()
    for tau in range(current_time, current_time + global_range + 1):
        inner_or_results[tau] = dict()
        for agent in mas.agents:
            inner_or_results[tau][agent] = sensing_results[tau][agent] or communication_results[tau][agent]
    # Compute the outer or results.
    outer_or_results = dict()
    for tau in range(current_time, current_time + global_range + 1):
        outer_or_results[tau] = dict()
        for agent in mas.agents:
            outer_or_results[tau][agent] = not_results[tau][agent] or inner_or_results[tau][agent]
    # Compute the and results.
    and_results = dict()
    for tau in range(current_time, current_time + global_range + 1):
        and_results[tau] = True
        for agent in mas.agents:
            if agent != ego_agent:
                and_results[tau] = and_results[tau] and outer_or_results[tau][agent]
    # Compute the outer logic
    outer_logic = True
    for i in range(current_time, current_time + global_range + 1):
        outer_logic = outer_logic and and_results[i]
    return outer_logic


if __name__ == '__main__':
    # Load the simulation data. # Change the file here to reflect the simulation data you want to use.
    with open("simulation_data_size_500.json", "r") as f:
        data = json.load(f)
    print("Loading data...")
    map, trajectories = data["map_info"], data["drone_trajectories"]
    # Convert all keys in trajectories to intgers.
    trajectories = {int(key): trajectories[key] for key in trajectories.keys()}
    print("Constructing MAS...")
    mas = MAS(trajectories)
    monitoring_range = 80
    ego_agent = 0

    # Compute the monitoring results for specification varphi_3 on agent 1.
    monitoring_results_varphi_3 = []
    monitoring_time_varphi_3 = []
    monitoring_results_varphi_4 = []
    monitoring_time_varphi_4 = []
    monitoring_results_phi_3 = []
    monitoring_time_phi_3 = []
    monitoring_results_phi_4 = []
    monitoring_time_phi_4 = []
    print("Monitoring specifications...")
    for t in range(monitoring_range + 1):
        varphi_3_time = time.perf_counter()
        monitoring_results_varphi_3.append(monitor_varphi_3(mas, ego_agent, t))
        monitoring_time_varphi_3.append((time.perf_counter() - varphi_3_time) * 1000)
        varphi_4_time = time.perf_counter()
        monitoring_results_varphi_4.append(monitor_varphi_4(mas, ego_agent, t))
        monitoring_time_varphi_4.append((time.perf_counter() - varphi_4_time) * 1000)
        phi_3_time = time.perf_counter()
        monitoring_results_phi_3.append(monitor_phi_3(mas, t))
        monitoring_time_phi_3.append((time.perf_counter() - phi_3_time) * 1000)
        phi_4_time = time.perf_counter()
        monitoring_results_phi_4.append(monitor_phi_4(mas, t, ego_agent))
        monitoring_time_phi_4.append((time.perf_counter() - phi_4_time) * 1000)
    
    # Report the monitoring results.
    print("results for varphi 3:")
    print(report_true_false_indices(monitoring_results_varphi_3))
    print("average time for varphi 3 (ms):")
    print(sum(monitoring_time_varphi_3) / len(monitoring_time_varphi_3))
    print()

    print("results for varphi 4:")
    print(report_true_false_indices(monitoring_results_varphi_4))
    print("average time for varphi 4 (ms):")
    print(sum(monitoring_time_varphi_4) / len(monitoring_time_varphi_4))
    print()

    print("results for phi 3:")
    print(report_true_false_indices(monitoring_results_phi_3))
    print("average time for phi 3 (ms):")
    print(sum(monitoring_time_phi_3) / len(monitoring_time_phi_3))
    print()

    print("results for phi 4:")
    print(report_true_false_indices(monitoring_results_phi_4))
    print("average time for phi 4 (ms):")
    print(sum(monitoring_time_phi_4) / len(monitoring_time_phi_4))
    print()

    # Save the results.
    with open("monitoring_results_size_500.txt", "w") as f: # Change the file name to reflect the size of the simulation.
        f.write("results for varphi 3:\n")
        f.write(str(report_true_false_indices(monitoring_results_varphi_3)) + "\n")
        f.write("average time for varphi 3 (ms): " + str(sum(monitoring_time_varphi_3) / len(monitoring_time_varphi_3)) + "\n\n")

        f.write("results for varphi 4:\n")
        f.write(str(report_true_false_indices(monitoring_results_varphi_4)) + "\n")
        f.write("average time for varphi 4 (ms): " + str(sum(monitoring_time_varphi_4) / len(monitoring_time_varphi_4)) + "\n\n")

        f.write("results for phi 3:\n")
        f.write(str(report_true_false_indices(monitoring_results_phi_3)) + "\n")
        f.write("average time for phi 3 (ms): " + str(sum(monitoring_time_phi_3) / len(monitoring_time_phi_3)) + "\n\n")

        f.write("results for phi 4:\n")
        f.write(str(report_true_false_indices(monitoring_results_phi_4)) + "\n")
        f.write("average time for phi 4 (ms): " + str(sum(monitoring_time_phi_4) / len(monitoring_time_phi_4)) + "\n\n")