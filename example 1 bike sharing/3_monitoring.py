import json
import networkx as nx
import numpy as np
import random
import time

random.seed(12)

with open('station_data.json', 'r') as file:
    station_dict = json.load(file)

i_id = [key for key, item in station_dict.items() if item['name'] == 'Grove St PATH'][0]
print("i_id:", i_id)
i_state = station_dict[i_id]['state']
G_dist = nx.read_gexf("distance_graph.gexf")
G_time = nx.read_gexf("time_graph/time_graph_0.gexf")

edges_from_i_out_dist = G_dist.out_edges(i_id, data=True)
edges_from_i_in_dist = G_dist.in_edges(i_id, data=True)
edges_from_i_out_time = G_time.out_edges(i_id, data=True)


# the id of agents that agent i_id can access the data
j_set_known_out_dist = [j for u, j, data in edges_from_i_out_dist if data['weight'] <= 2.5]
j_set_known_in_dist  = [u for u, j, data in edges_from_i_in_dist if data['weight'] <= 2.5]
j_set_known_out_time = [j for u, j, data in edges_from_i_out_time if data['weight'] <= 7]



############################################################################
# centralized monitoring for varphi_1
time_start_varphi1_c = time.time()
E = [5, float('inf')]
W = [0, 8]
j_set = [j for u, j, data in edges_from_i_out_time if data['weight'] <= W[1]]

state_list = []
for j in j_set:
    state_list.append(station_dict[j]['state'])

s_varphi1_c = []
for day in range(1, 32):
    s_varphi1_c_time = []
    for t in range(24):
        n_sat = sum([1 if state[str(day)][t][0] >= 8 else 0 for state in state_list])
        if i_state[str(day)][t][0] < 5 and n_sat <E[0]:
            s_varphi1_c_time.append(0)
        else:
            s_varphi1_c_time.append(1)
    s_varphi1_c.append(1 if sum(s_varphi1_c_time) == 24 else 0)
time_end_varphi1_c = time.time()
print("s_varphi1_c:", s_varphi1_c)

# distributed monitoring for varphi_1
time_start_varphi1_d = time.time()
state_list = []
for j in j_set:
    if j in j_set_known_out_time:
        state_list.append(station_dict[j]['state'])
    else:
        state_list.append({str(day): [[np.nan, np.nan, np.nan]] * 24 for day in range(1, 32)})

s_varphi1_d = []
for day in range(1, 32):
    s_varphi1_d_time = []
    for t in range(24):
        n_sat_list = [1 if state[str(day)][t][0] >= 8 else 0 if state[str(day)][t][0] < 8  else np.nan for state in state_list]
        n_sat = n_sat_list.count(1)
        n_negvio = n_sat_list.count(1) + n_sat_list.count(np.nan)

        s_graph = 0
        if n_sat >= E[0] and n_negvio <= E[1]:
            s_graph = 1
        elif n_negvio <= E[0] or n_sat >= E[1]:
            s_graph = 0
        else:
            s_graph = np.nan

        if i_state[str(day)][t][1] < 5 and s_graph == 0:
            s_varphi1_d_time.append(0)
        elif (i_state[str(day)][t][1] < 5 and s_graph == 1) or (i_state[str(day)][t][1] >= 5):
            s_varphi1_d_time.append(1)
        else:
            s_varphi1_d_time.append(np.nan)

    s_varphi1_d.append(1 if sum(s_varphi1_d_time) == 24 else 0)
time_end_varphi1_d = time.time()
print("s_varphi1_d:", s_varphi1_d)


############################################################################
# centralized monitoring for varphi_2
time_start_varphi2_c = time.time()
E = [0, 4]
W = [0, 2]
j_set = [j for u, j, data in edges_from_i_in_dist if data['weight'] <= W[1]]
state_list = []
for j in j_set:
    state_list.append(station_dict[j]['state'])

s_varphi2_c = []
for day in range(1, 32):
    s_varphi2_c_time = []
    for t in range(24):
        n_sat = sum([1 if state[str(day)][t][1] - state[str(day)][t][2] > 5 else 0 for state in state_list])
        if i_state[str(day)][t][1] > 15 and n_sat > E[1]:
            s_varphi2_c_time.append(0)
        else:
            s_varphi2_c_time.append(1)
    s_varphi2_c.append(1 if sum(s_varphi2_c_time) == 24 else 0)
time_end_varphi2_c = time.time()
print("s_varphi2_c:", s_varphi2_c)




# distributed monitoring for varphi_2
time_start_varphi2_d = time.time()
state_list = []
for j in j_set:
    if j in j_set_known_in_dist:
        state_list.append(station_dict[j]['state'])
    else:
        state_list.append({str(day): [[np.nan, np.nan, np.nan]] * 24 for day in range(1, 32)})

s_varphi2_d = []
for day in range(1, 32):
    s_varphi2_d_time = []
    for t in range(24):
        n_sat_list = [1 if state[str(day)][t][1] - state[str(day)][t][2] > 5 else 0 if state[str(day)][t][1] - state[str(day)][t][2] <= 5  else np.nan for state in state_list]
        n_sat = n_sat_list.count(1)
        n_negvio = n_sat_list.count(1) + n_sat_list.count(np.nan)

        s_graph = 0
        if n_sat >= E[0] and n_negvio <= E[1]:
            s_graph = 1
        elif n_negvio < E[0] or n_sat > E[1]:
            s_graph = 0
        else:
            s_graph = np.nan

        if i_state[str(day)][t][1] > 15 and s_graph == 0:
            s_varphi2_d_time.append(0)
        elif (i_state[str(day)][t][1] > 15 and s_graph == 1) or (i_state[str(day)][t][1] <= 15):
            s_varphi2_d_time.append(1)
        else:
            s_varphi2_d_time.append(np.nan)

    s_varphi2_d.append(1 if s_varphi2_d_time.count(1) == 24 else np.nan if s_varphi2_d_time.count(np.nan) >= 1 else 0)
time_end_varphi2_d = time.time()
print("s_varphi2_d:", s_varphi2_d)


############################################################################
# centralized monitoring for phi_1
time_start_phi1_c = time.time()
E = [3, float('inf')]
W = [0, 1]
V = random.sample(range(1, len(station_dict)), 30)

s_phi1_c = []
for day in range(1, 32):
    s_phi1_c_i = []
    for i in V:
        i_state = station_dict[str(i)]['state']
        edges_from_i_out_dist = G_dist.out_edges(str(i), data=True)
        j_set = [j for u, j, data in edges_from_i_out_dist if data['weight'] <= W[1]]
        state_list = []
        for j in j_set:
            state_list.append(station_dict[j]['state'])
        s_phi1_c_i_time = []
        for t in range(24):
            n_sat = sum([1 if state[str(day)][t][0] >= 8 else 0 for state in state_list])
            if n_sat >= E[0]:
                s_phi1_c_i_time.append(1)
            else:
                s_phi1_c_i_time.append(0)
        s_phi1_c_i.append(1 if sum(s_phi1_c_i_time) == 24 else 0)
    s_phi1_c.append(1 if sum(s_phi1_c_i) == len(V) else 0)
    # print("s_phi1_c_i:", s_phi1_c_i)
time_end_phi1_c = time.time()
print("s_phi1_c:", s_phi1_c)
        

############################################################################
# centralized monitoring for phi_2
time_start_phi2_c = time.time()
E = [3, float('inf')]
W = [0, 12]

s_phi2_c = []
for day in range(1, 32):
    s_phi2_c_i = []
    for i in V:
        i_state = station_dict[str(i)]['state']
        edges_from_i_out_time = G_time.out_edges(str(i), data=True)
        j_set = [j for u, j, data in edges_from_i_out_time if data['weight'] <= W[1]]
        state_list = []
        for j in j_set:
            state_list.append(station_dict[j]['state'])
        s_phi2_c_i_time = []
        for t in range(24):
            n_sat = sum([1 if state[str(day)][t][0] >= 4 else 0 for state in state_list])
            if i_state[str(day)][t][0] < 2 and n_sat < E[0]:
                s_phi2_c_i_time.append(0)
            else:
                s_phi2_c_i_time.append(1)
        s_phi2_c_i.append(1 if sum(s_phi2_c_i_time) == 24 else 0)
    s_phi2_c.append(1 if sum(s_phi2_c_i) == len(V) else 0)
    # print("s_phi1_c_i:", s_phi1_c_i)
time_end_phi2_c = time.time()
print("s_phi2_c:", s_phi1_c)
        

print("varphi_1 centralized: the number of satisfaction:", sum(s_varphi1_c))
print("varphi_2 centralized: the number of satisfaction:", sum(s_varphi2_c))
print("phi_1 centralized: the number of satisfaction:", sum(s_phi1_c))
print("phi_2 centralized: the number of satisfaction:", sum(s_phi1_c))


print("varphi_1 distributed: the number of satisfaction:", s_varphi1_d.count(1))
print("varphi_1 distributed: the number of violation:", s_varphi1_d.count(0))
print("varphi_1 distributed: the number of unknown:", s_varphi1_d.count(np.nan))
print("varphi_2 distributed: the number of satisfaction:", s_varphi2_d.count(1))
print("varphi_2 distributed: the number of violation:", s_varphi2_d.count(0))
print("varphi_2 distributed: the number of unknown:", s_varphi2_d.count(np.nan))


print("time, centralized, varphi_1:", (time_end_varphi1_c - time_start_varphi1_c)/31)
print("time, centralized, varphi_2:", (time_end_varphi2_c - time_start_varphi2_c)/31)
print("time, centralized, phi_1:", (time_end_phi1_c - time_start_phi1_c)/31)
print("time, centralized, phi_2:", (time_end_phi2_c - time_start_phi2_c)/31)
print("time, distributed, varphi_1:", (time_end_varphi1_d - time_start_varphi1_d)/31)
print("time, distributed, varphi_2:", (time_end_varphi2_d - time_start_varphi2_d)/31)
