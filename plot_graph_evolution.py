import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.animation import FuncAnimation
import pickle
import re
from enum import Enum

class Color(Enum):
    SLEEP = "#808080"
    F_0 = "#008000"
        #AWAKENED_BY = "#FFFF00"
    EDGE_OFF = "#000000"
    EDGE_ON = "#00FFFF"
    EDGE_BRANCH_ONE_SIDE = "#FF69B4"
    EDGE_BRANCH_TWO_SIDES = "#800080"
    EDGE_CORE = "#FFFF00"
    EDGE_REJECTED_ONE_SIDE = "#DCDCDC"
    EDGE_REJECTED_TWO_SIDES = "#F5F5F5"
    F_1 = "#F51313"
    F_2 = "#0000FF"
    F_3 = "#00FFFF"
    F_4 = "#FF00FF"
    F_5 = "#800000"
    F_6 = "#808000"
    F_7 = "#008080"
    F_8 = "#800080"
    F_9 = "#00008"
    F_10 = "#FFFACD"

fragmentOfNode = {}

fragmentColor = {
    "-1": Color.SLEEP.value,
    "0": Color.F_0.value
}
maxFragmentLevel = 0
edgeColor = {}
edgeWeight = {}

fragmentCount = 0

nodeLeader = {}

def extract_vars(line):
    # [128.000000] [host2] [INITIATE from 3] (2 <-- Initiate -- 3) : {Level = 1, Fragment id = 4, State = NodeState.FIND}"
    pattern = r"\[(\d+\.\d+)\] \[host(\d+)\] \[(.*?)\] \(.*\) \: \{(.*)\}"
    match = re.match(pattern, line)
    if match:
        timestamp = float(match.group(1))
        id = int(match.group(2))
        message = match.group(3)
        payload = match.group(4)
        return (timestamp, id, message, payload)
    else:
        return None

def read_log_file(log_file):
    graph_states = []
    with open(log_file, 'r') as file:
        for line in file:
            extracted_tuple = extract_vars(line)
            if extracted_tuple is not None: 
                graph_states.append(extracted_tuple)
                #print(f"Timestamp: {extracted_tuple[0]}, id: {extracted_tuple[1]}, message: {extracted_tuple[2]}, payload: {extracted_tuple[3]}")
    return graph_states

def load_graph(file_path):
    # Create an empty graph
    G = nx.Graph()

    nodes = []
    edges = []
    # Read the file
    with open(file_path, 'r') as file:
        for line in file:
            # Parse the line into node1, node2, and weight
            node1, node2, weight = map(int, line.split())
            nodes.append(node1)
            nodes.append(node2)

            # Add an edge with the specified weight
            G.add_edge(node1, node2, weight=weight)

            global edgeColor
            global edgeWeight
            if node1 < node2:
                edgeColor[str(node1) + str(node2)] = Color.EDGE_OFF.value
                edgeWeight[str(node1) + str(node2)] = weight
            else:
                edgeColor[str(node2) + str(node1)] = Color.EDGE_OFF.value
                edgeWeight[str(node2) + str(node1)] = weight


    nodes = list(set(nodes))

    global fragmentOfNode
    global nodeLeader
    for node in nodes:
        fragmentOfNode[str(node)] = -1
        nodeLeader[str(node)] = -1

    pos = nx.spring_layout(G, seed = 100)

    return G, pos, nodes

# Function to update the plot for each frame
def update(frame):
    plt.clf()  # Clear the current plot

    f_self_awakened = 0
    sNode_awakened_by = -1
    f_awakened_by = 0
    f_connect_to = 0
    f_initiate_to = 0
    f_initiate_from = 0
    f_branch_to = 0
    f_comm = 0
    dNode_to = -1
    timestamp, id, message, payload = graph_states_filtered[frame]

    if message == "SELF-AWAKENED":
        f_self_awakened = 1
        fragmentOfNode[str(id)] = 0
    elif message.startswith('AWAKENED by'):
        f_awakened_by = 1
        fragmentOfNode[str(id)] = 0
        sNode_awakened_by = -1
        pattern = r"AWAKENED by (\d+)"
        match = re.match(pattern, message)
        if match:
            sNode_awakened_by = int(match.group(1))
    elif message.startswith('CONNECT to ') or  message.startswith('INITIATE to ') or message.startswith('REPORT to ') or message.startswith('TEST to ') or message.startswith('ACCEPT to ') or message.startswith('REJECT to ') or message.startswith('CHANGE_ROOT to '):
        pattern = r".* to (\d+)"
        match = re.match(pattern, message)
        if match:
            f_comm = 1
            dNode_to = int(match.group(1))
    #     f_connect_to = 1
    #     dNode_connect_to = -1
    #     pattern = r"CONNECT to (\d+)"
    #     match = re.match(pattern, message)
    #     if match:
    #         dNode_connect_to = int(match.group(1))
    # elif message.startswith('INITIATE to '):
    #     f_initiate_to = 1
    #     dNode_initiate_to = -1
    #     pattern = r"INITIATE to (\d+)"
    #     match = re.match(pattern, message)
    #     if match:
    #         dNode_initiate_to = int(match.group(1))
    elif message.startswith('INITIATE from '):
#[128.000000] [host2] [INITIATE from 3] (2 <-- Initiate -- 3) : {Level = 1, Fragment id = 4, State = NodeState.FIND}
        f_initiate_from = 1

        sNode_initiate_from = -1
        pattern = r"INITIATE from (\d+)"
        match = re.match(pattern, message)
        if match:
            sNode_initiate_from = int(match.group(1))

        fragmentLevel = -1
        f_change_core_color = 0
        pattern = r".*Level = (\d+).*"
        match = re.match(pattern, payload)
        if match:
            fragmentLevel = int(match.group(1))
            global maxFragmentLevel
            if fragmentLevel > maxFragmentLevel:
                f_change_core_color = 1
                maxFragmentLevel = fragmentLevel

        fragmentId = -1
        pattern = r".*Fragment id = (\d+).*"
        match = re.match(pattern, payload)
        if match:
            fragmentId = int(match.group(1))
            fragmentOfNode[str(id)] = fragmentId
            if fragmentColor.get(str(fragmentId)) is None:
                global fragmentCount
                fragmentCount += 1
                colorCode = getattr(Color, f"F_{fragmentCount}")
                fragmentColor[str(fragmentId)] = colorCode.value

            if id < sNode_initiate_from:
                s = id
                d = sNode_initiate_from
            else:
                s = sNode_initiate_from
                d = id
            if edgeWeight[str(s) + str(d)] == fragmentId:
                if f_change_core_color and Color.EDGE_CORE.value in edgeColor.values():
                    for e in edgeColor:
                        if edgeColor[e] == Color.EDGE_CORE.value:
                            edgeColor[e] = Color.EDGE_BRANCH_TWO_SIDES.value
                edgeColor[str(s) + str(d)] = Color.EDGE_CORE.value

    elif message.startswith('BRANCH to '):
        f_branch_to = 1
        dNode_branch_to = -1
        pattern = r"BRANCH to (\d+)"
        match = re.match(pattern, message)
        if match:
            dNode_branch_to = int(match.group(1))
            if id < dNode_branch_to:
                s = id
                d = dNode_branch_to
            else:
                s = dNode_branch_to
                d = id

            if edgeColor.get(str(s) + str(d)) == Color.EDGE_OFF.value:
                edgeColor[str(s) + str(d)] = Color.EDGE_BRANCH_ONE_SIDE.value
            elif edgeColor.get(str(s) + str(d)) == Color.EDGE_BRANCH_ONE_SIDE.value:
                edgeColor[str(s) + str(d)] = Color.EDGE_BRANCH_TWO_SIDES.value

    elif message.startswith('REJECTED to '):
        dNode_rejected_to = -1
        pattern = r"REJECTED to (\d+)"
        match = re.match(pattern, message)
        if match:
            dNode_rejected_to = int(match.group(1))
            if id < dNode_rejected_to:
                s = id
                d = dNode_rejected_to
            else:
                s = dNode_rejected_to
                d = id

            if edgeColor.get(str(s) + str(d)) == Color.EDGE_OFF.value:
                edgeColor[str(s) + str(d)] = Color.EDGE_REJECTED_ONE_SIDE.value
            elif edgeColor.get(str(s) + str(d)) == Color.EDGE_REJECTED_ONE_SIDE.value:
                edgeColor[str(s) + str(d)] = Color.EDGE_REJECTED_TWO_SIDES.value

    elif message.startswith('FINISHED with '):
        pattern = r"FINISHED with leader (\d+)"
        match = re.match(pattern, message)
        if match:
            leader = int(match.group(1))
            nodeLeader[str(id)] = leader


    labels = {}
    color_map = []
    for node in nodes:
        if nodeLeader[str(node)] != -1:
            labels[int(node)] = str(node) + "(" + str(nodeLeader[str(node)]) + ")"
        else: 
            labels[int(node)] = str(node)
        G.nodes[node]["color"] = fragmentColor[str(fragmentOfNode[str(node)])]

    edges = G.edges()
    for u, v in edges:
        if u < v:
            G[u][v]["color"] = edgeColor[str(u) + str(v)]
        else:
            G[v][u]["color"] = edgeColor[str(v) + str(u)] 

    if f_comm == 1 and dNode_to != -1:
        if id < dNode_to:
            G[id][dNode_to]["color"] = Color.EDGE_ON.value
        else:
            G[dNode_to][id]["color"] = Color.EDGE_ON.value  
    #if f_connect_to == 1 and dNode_connect_to != -1:
        #if id < dNode_connect_to:
            #G[id][dNode_connect_to]["color"] = Color.EDGE_ON.value
        #else:
            #G[dNode_connect_to][id]["color"] = Color.EDGE_ON.value

    #elif f_initiate_to == 1 and dNode_initiate_to != -1:
        #if id < dNode_initiate_to:
            #G[id][dNode_initiate_to]["color"] = Color.EDGE_ON.value
        #else:
            #G[dNode_initiate_to][id]["color"] = Color.EDGE_ON.value

    nx.draw_networkx_nodes(G, pos, node_size=2000, node_color=[G.nodes[node]["color"] for node in G])
    nx.draw_networkx_labels(G, pos, labels, font_size=20, font_family='sans-serif')
    nx.draw_networkx_edges(G, pos, edge_color=[G[u][v]["color"] for u,v in edges], width = 3)
    #nx.draw_networkx_edges(G, pos, edge_color=Color.EDGE_OFF.value, width = 3)
    edge_weights = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_weights, font_size=14)

    plt.axis('off')
    figure = plt.gcf()
    figure.set_size_inches(19.2, 10.8)
    
    # Show the timestamp as the title of the plot
    #plt.title(f"Time: {timestamp}s, node: {id}, message: {message}, payload: {payload}", fontsize=20)
    if f_initiate_from:
        plt.title(f"Time: {timestamp}s, node: {id}, message: {message}, Fragment Id: {fragmentOfNode[str(id)]}", fontsize=20)
    else:
        plt.title(f"Time: {timestamp}s, node: {id}, message: {message}", fontsize=20)

    #print("")

def init_func():
    pass

if __name__=='__main__':
    # Create graph
    graph_edges_file = 'in/graph.txt'
    G, pos, nodes = load_graph(graph_edges_file)

    # Create config for initial graph plot
    edge_weights = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_nodes(G, pos, node_color='0.75', node_size=2000)
    labels = {}
    for node_name in nodes:
        labels[int(node_name)] = str(node_name)
    nx.draw_networkx_labels(G, pos, labels, font_size=20, font_family='sans-serif')
    nx.draw_networkx_edges(G, pos, width = 3)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_weights, font_size=14)
    plt.axis('off')
    figure = plt.gcf()
    figure.set_size_inches(19.2, 10.8)
    plt.savefig('out/graph_initial_state.png')
    plt.clf()


    # Read graph evolution from log
    log_file = 'out/log_file.log'
    graph_states = read_log_file(log_file)

    # Filter only for SELF-AWAKENED, AWAKENED by, INITIATE from, 
    #graph_states_filtered = [graph_state for graph_state in graph_states \
    #if graph_state[2] == "SELF-AWAKENED" or graph_state[2].startswith('AWAKENED by') or graph_state[2].startswith('INITIATE from') \
    #or graph_state[2].startswith('BRANCH to')]

    graph_states_filtered = graph_states

    # Plot graph evolution
    #for graph_state in graph_states_filtered:
        #print(graph_state)

    fig = plt.gcf()
    fig.set_size_inches(19.2, 10.8)
    framesCount = len(graph_states_filtered)
    print(f"No. of frames: {framesCount}")
    animation = FuncAnimation(fig, update, frames=framesCount, interval=1000, init_func=init_func)

    output_file = 'out/graph_evolution.mp4'
    animation.save(output_file, writer='ffmpeg')

    plt.clf()
    # Create mst verification graph
    G = nx.minimum_spanning_tree(G)

    # Create config for mst graph plot
    edge_weights = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_nodes(G, pos, node_color='0.75', node_size=2000)
    labels = {}
    for node_name in nodes:
        labels[int(node_name)] = str(node_name)
    nx.draw_networkx_labels(G, pos, labels, font_size=20, font_family='sans-serif')
    nx.draw_networkx_edges(G, pos, width = 3)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_weights, font_size=14)
    plt.axis('off')
    figure = plt.gcf()
    figure.set_size_inches(19.2, 10.8)
    plt.savefig('out/graph_MST_verification.png')
    plt.clf()
