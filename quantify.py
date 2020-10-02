'''Parse graphs in custom .xyz format, and measure traits.
Copyright 2020 Kian Faizi.

Points are stored in a tree using an undirected NetworkX graph.
Each node has a unique numerical identifier (node_num),
 and an attribute "pos": an (x,y) coordinate pair corresponding to its position in 2D space.
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

parser = argparse.ArgumentParser(description='select file')
parser.add_argument('-i', '--input', help='Full path to input file', required=True)
args = parser.parse_args()

def distance(p1, p2):
    '''Compute 2D Euclidian distance between two (x,y) points.'''
    return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)

G = nx.Graph()

# parse input file
with open(args.input, "r") as f:
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
                    if level == parent[1][0] and group_num == parent[1][1]: # check that the expected and actual positions of the child match
                        G.add_edge(node_num, parent[0], length = distance(G.nodes[node_num]['pos'], G.nodes[parent[0]]['pos']))
                    else:
                        print("Edge assignment failed!")
                        break
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
                    print("Edge assignment failed!")
                    break
            node_num += 1
            group_num += 1

# check that graph is indeed a tree (acyclic, undirected, connected)
assert nx.is_tree(G)