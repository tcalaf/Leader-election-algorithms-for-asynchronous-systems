import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.animation import FuncAnimation
import pickle
import re

awaken = []

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
    # Read the file
    with open(file_path, 'r') as file:
        for line in file:
            # Parse the line into node1, node2, and weight
            node1, node2, weight = map(int, line.split())
            nodes.append(node1)
            nodes.append(node2)

            # Add an edge with the specified weight
            G.add_edge(node1, node2, weight=weight)

    nodes = list(set(nodes))
    pos = nx.spring_layout(G, seed = 100)

    return G, pos, nodes

# Function to update the plot for each frame
def update(frame):
    plt.clf()  # Clear the current plot

    f_self_awakened = 0
    sNode_awakened_by = -1
    f_awakened_by = 0

    #print(frame)
    timestamp, id, message, desc = graph_states_filtered[frame]
    #print(f"Timestamp: {timestamp}, id: {id}, message: {message}, desc: {desc}")

    if message == "SELF-AWAKENED":
        f_self_awakened = 1
    elif message.startswith('AWAKENED by'):
        f_awakened_by = 1
        sNode_awakened_by = -1
        pattern = r"AWAKENED by (\d+)"
        match = re.match(pattern, message)
        if match:
            sNode_awakened_by = int(match.group(1))


    labels = {}
    color_map = []
    for node in nodes:
        labels[int(node)] = str(node)
        if (f_self_awakened == 1 or f_awakened_by == 1) and str(node) == str(id):
            awaken.append(node)
        if node in awaken:
            color = "green"
        else:
            color = "0.75"
        if f_awakened_by == 1 and sNode_awakened_by != -1 and sNode_awakened_by == node:
            color = "yellow"
        G.nodes[node]["color"] = color

    nx.draw_networkx_nodes(G, pos, node_size=2000, node_color=[G.nodes[node]["color"] for node in G])
    nx.draw_networkx_labels(G, pos, labels, font_size=20, font_family='sans-serif')
    nx.draw_networkx_edges(G, pos, width = 3)
    edge_weights = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_weights, font_size=14)

    plt.axis('off')
    figure = plt.gcf()
    figure.set_size_inches(19.2, 10.8)
    
    # Show the timestamp as the title of the plot
    plt.title(f"Time: {timestamp}s, node: {id}, message: {message}, desc: {desc}")
    #print("")

def init_func():
    pass

if __name__=='__main__':
    # Create graph
    graph_edges_file = 'graph.txt'
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
    plt.savefig('images/graph_initial_state.png')
    plt.clf()


    # Read graph evolution from log
    log_file = 'log_file.log'
    graph_states = read_log_file(log_file)

    # Plot graph evolution
    #for graph_state in graph_states:
        #print(graph_state)

    # Filter for only SELF-AWAKENED messages
    graph_states_filtered = [graph_state for graph_state in graph_states \
    if graph_state[2] == "SELF-AWAKENED" or graph_state[2].startswith('AWAKENED by') ]
    
    #graph_states_filtered = filter(lambda x: x[2] == "SELF-AWAKENED", graph_states)
    #for graph_state in graph_states_filtered:
        #print(graph_state)
    
    fig = plt.gcf()
    fig.set_size_inches(19.2, 10.8)
    framesCount = len(graph_states_filtered)
    print(f"No. of frames: {framesCount}")
    animation = FuncAnimation(fig, update, frames=framesCount, interval=1000, init_func=init_func)

    output_file = 'images/graph_evolution.mp4'
    animation.save(output_file, writer='ffmpeg')
    #output_file = 'images/graph_evolution.gif'
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
    plt.savefig('images/graph_MST_verification.png')
    plt.clf()
