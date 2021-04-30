'''Parse graphs in custom .xyz format, and measure traits.
Copyright 2020 Kian Faizi.
Points are stored in a tree using an undirected NetworkX graph.
Each node has a unique numerical identifier (node_num), and an attribute "pos": an (x,y) coordinate pair corresponding to its position in 2D space.
Each edge has an attribute "length": the Euclidean distance between the nodes it connects.
TO-DO:
Mark terminal points (degree == 1)
Trait measurement
Time series?
Plot graphs for visual inspection?
'''

import argparse
import networkx as nx
import math
from queue import Queue
from pareto_functions import pareto_front
import matplotlib.pyplot as plt

# parser = argparse.ArgumentParser(description='select file')
# parser.add_argument('-i', '--input', help='Full path to input file', required=True)
# args = parser.parse_args()

def distance(p1, p2):
    '''Compute 2D Euclidian distance between two (x,y) points.'''
    return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)

def make_graph(target):
    '''Construct graph from file and check for errors.'''
    G = nx.Graph()
    with open(target, "r") as f: # parse input file
        q = Queue()
        node_num = 1 # label nodes with unique identifiers
        for line in f:
            if line.startswith("##"): # Level heading
                group_num = 0 # count nodes per level, and reset on level change, to match hierarchy info from tuples
                level = int(line.rstrip().split(": ")[1])
                continue
            else:
                info = line.rstrip().split("; ")
                if len(info) > 1: # node has degree > 1
                    coords = tuple(int(float(i)) for i in info[0].split())[0:2] # change output coords from floats to ints
                    G.add_node(node_num, pos = coords)
                    if not q.empty():
                        parent = q.get()
                        # print(parent, level, group_num, info)
                        if level == parent[1][0] and group_num == parent[1][1]: # check that the expected and actual positions of the child match
                            G.add_edge(node_num, parent[0], length = distance(G.nodes[node_num]['pos'], G.nodes[parent[0]]['pos']))
                        else:
                            return f"Edge assignment failed: {parent}; {level}; {group_num}; {info}"
                            #return G
                    # place all descendants of the current node in the queue for processing in future rounds
                    children = info[1].split()
                    for child in children:
                        q.put((node_num, list(map(int, child.strip('[]').split(','))))) # converts each child object from list of strings to list of ints
                else: # terminal node (degree == 1)
                    coords = tuple(int(float(i)) for i in info[0].rstrip(";").split())[0:2]
                    G.add_node(node_num, pos = coords)
                    children = None
                    parent = q.get()
                    if level == parent[1][0] and group_num == parent[1][1]:
                        G.add_edge(node_num, parent[0], length = distance(G.nodes[node_num]['pos'], G.nodes[parent[0]]['pos']))
                    else:
                        return "Edge assignment failed: terminal node."
                node_num += 1
                group_num += 1
    #return "Done!" (used for csv creation)
    return G
    
def show_skel(target):
    '''Plot a nx graph/skel from a .txt file'''
    G = make_graph(target)
    layout = {} # dict of nodes:positions
    for i in G.nodes.data():
        node = i[0]
        pos = i[1]['pos']
        layout[node] = pos 
    print(layout)
    nx.draw_networkx(G, pos=layout)
    plt.show()

#show_skel('/home/kian/Lab/output/96_set1_day13_20200329-140102_024_plantE_day8.txt')
print(make_graph('/home/kian/Lab/analysis/96_set1_day13_20200329-140102_024_plantDAY8_TEST_no_insert_day8.txt'))


# # check that graph is indeed a tree (acyclic, undirected, connected)
# assert nx.is_tree(G)

# mcosts, scosts, actual = pareto_front(G)

# plt.plot(mcosts, scosts, 'ro')
# plt.plot(actual[0], actual[1], 'go')
# plt.show()

# fig, ax = plt.subplots()
# ax.scatter()
# ax.set_xlabel("mcosts", fontsize=15)
# ax.set_ylabel("scosts", fontsize=15)
# ax.set_title("test pareto front")
# ax.grid(True)
# fig.tight_layout()
# plt.show()

# for mcost, scost in zip(mcosts, scosts):
#     print(mcost, scost)