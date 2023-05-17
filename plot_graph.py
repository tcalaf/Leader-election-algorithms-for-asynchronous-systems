import networkx as nx
import matplotlib.pyplot as plt


def plot_weighted_graph():
    G = nx.Graph()

    node_list = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']

    for node in node_list:
        G.add_node(node)

    pos = nx.spring_layout(G) 
    nx.draw_networkx_nodes(G, pos, node_color='0.75', node_size=3100)

    labels = {}
    for node_name in node_list:
        labels[str(node_name)] = str(node_name)

    nx.draw_networkx_labels(G, pos, labels, font_size=12, font_family='sans-serif')

    G.add_edge(node_list[0], node_list[1], weight=3)
    G.add_edge(node_list[0], node_list[5], weight=2)
    G.add_edge(node_list[1], node_list[2], weight=17)
    G.add_edge(node_list[1], node_list[3], weight=16)
    G.add_edge(node_list[2], node_list[3], weight=8)
    G.add_edge(node_list[2], node_list[8], weight=18)
    G.add_edge(node_list[3], node_list[4], weight=11)
    G.add_edge(node_list[3], node_list[8], weight=4)
    G.add_edge(node_list[4], node_list[5], weight=1)
    G.add_edge(node_list[4], node_list[6], weight=6)
    G.add_edge(node_list[4], node_list[7], weight=5)
    G.add_edge(node_list[4], node_list[8], weight=10)
    G.add_edge(node_list[5], node_list[6], weight=7)
    G.add_edge(node_list[6], node_list[7], weight=15)
    G.add_edge(node_list[7], node_list[8], weight=12)
    G.add_edge(node_list[7], node_list[9], weight=13)
    G.add_edge(node_list[8], node_list[9], weight=9)
 

    nx.draw_networkx_edges(G, pos, edgelist = G.edges(), width = 5)
 
    #Plot the graph
    plt.axis('off')


    #plt.draw()
    plt.show()

if __name__=='__main__':
    plot_weighted_graph()