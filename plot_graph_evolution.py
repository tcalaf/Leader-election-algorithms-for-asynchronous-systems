import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.animation import FuncAnimation
import pickle
import re
from enum import Enum

awaken = []
fragments = []

class Color(Enum):
    SLEEP = "#808080"
    AWAKEN = "#008000"
        #AWAKENED_BY = "#FFFF00"
    EDGE_OFF = "#000000"
    EDGE_ON = "#FF7F50"
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

def getColorByFragmentNo(fragmentNo):
    color = "Color.F_" + str(fragmentNo)
    return color

def extract_vars(line):
    pattern = r"\[(\d+\.\d+)\] \[host(\d+)] \[(.*?)\] \((.*)\)"
    match = re.match(pattern, line)
    if match:
        timestamp = float(match.group(1))
        id = int(match.group(2))
        message = match.group(3)
        desc = match.group(4)
        return (timestamp, id, message, desc)
    else:
        return None

def read_log_file(log_file):
    graph_states = []
    with open(log_file, 'r') as file:
        for line in file:
            extracted_tuple = extract_vars(line)
            if extracted_tuple is not None: 
                graph_states.append(extracted_tuple)
                #print(f"Timestamp: {extracted_tuple[0]}, id: {extracted_tuple[1]}, message: {extracted_tuple[2]}, desc: {extracted_tuple[3]}")
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
            edges.append(edges)

    nodes = list(set(nodes))
    pos = nx.spring_layout(G, seed = 100)

    return G, pos, nodes, edges

# Function to update the plot for each frame
def update(frame):
    plt.clf()  # Clear the current plot

    f_self_awakened = 0
    sNode_awakened_by = -1
    f_awakened_by = 0
    f_connect_to = 0
    f_initiate_to = 0

    timestamp, id, message, desc = graph_states[frame]

    if message == "SELF-AWAKENED":
        f_self_awakened = 1
    elif message.startswith('AWAKENED by'):
        f_awakened_by = 1
        sNode_awakened_by = -1
        pattern = r"AWAKENED by (\d+)"
        match = re.match(pattern, message)
        if match:
            sNode_awakened_by = int(match.group(1))
    elif message.startswith('CONNECT to '):
        f_connect_to = 1
        dNode_connect_to = -1
        pattern = r"CONNECT to (\d+)"
        match = re.match(pattern, message)
        if match:
            dNode_connect_to = int(match.group(1))
    elif message.startswith('INITIATE to '):
        f_initiate_to = 1
        dNode_initiate_to = -1
        pattern = r"INITIATE to (\d+)"
        match = re.match(pattern, message)
        if match:
            dNode_initiate_to = int(match.group(1))

    labels = {}
    color_map = []
    for node in nodes:
        labels[int(node)] = str(node)
        if (f_self_awakened == 1 or f_awakened_by == 1) and str(node) == str(id):
            awaken.append(node)
        if node in awaken:
            color = Color.AWAKEN.value
        else:
            color = Color.SLEEP.value
        #if f_awakened_by == 1 and sNode_awakened_by != -1 and sNode_awakened_by == node:
            #color = Color.AWAKENED_BY.value
        G.nodes[node]["color"] = color

    edges = G.edges()
    for u, v in edges:
        if f_connect_to == 1 and dNode_connect_to != -1:
            if id < dNode_connect_to:
                G[id][dNode_connect_to]["color"] = Color.EDGE_ON.value
            else:
                G[dNode_connect_to][id]["color"] = Color.EDGE_ON.value

        elif f_initiate_to == 1 and dNode_initiate_to != -1:
            if id < dNode_initiate_to:
                G[id][dNode_initiate_to]["color"] = Color.EDGE_ON.value
            else:
                G[dNode_initiate_to][id]["color"] = Color.EDGE_ON.value

        else:    
            G[u][v]["color"] = Color.EDGE_OFF.value

    nx.draw_networkx_nodes(G, pos, node_size=2000, node_color=[G.nodes[node]["color"] for node in G])
    nx.draw_networkx_labels(G, pos, labels, font_size=20, font_family='sans-serif')
    nx.draw_networkx_edges(G, pos, edge_color=[G[u][v]["color"] for u,v in edges], width = 3)
    edge_weights = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_weights, font_size=14)

    plt.axis('off')
    figure = plt.gcf()
    figure.set_size_inches(19.2, 10.8)
    
    # Show the timestamp as the title of the plot
    plt.title(f"Time: {timestamp}s, node: {id}, message: {message}, desc: {desc}", fontsize=20)

    #print("")

def init_func():
    pass

if __name__=='__main__':
    # Create graph
    graph_edges_file = 'in/graph.txt'
    G, pos, nodes, edges = load_graph(graph_edges_file)

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

    # Plot graph evolution
    #for graph_state in graph_states:
        #print(graph_state)

    fig = plt.gcf()
    fig.set_size_inches(19.2, 10.8)
    framesCount = len(graph_states)
    print(f"No. of frames: {framesCount}")
    animation = FuncAnimation(fig, update, frames=framesCount, interval=1000, init_func=init_func)

    output_file = 'out/graph_evolution.mp4'
    animation.save(output_file, writer='ffmpeg')
    #output_file = 'out/graph_evolution.gif'
    #animation.save(output_file, writer='ffmpeg')

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
