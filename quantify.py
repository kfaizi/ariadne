'''Parse graphs in custom .xyz format, and measure traits.
Copyright 2020 Kian Faizi.

TO-DO:
Trait measurement
Time-series data
'''

# import argparse
import networkx as nx
import math
import matplotlib.pyplot as plt
from queue import Queue

# parser = argparse.ArgumentParser(description='select file')
# parser.add_argument('-i', '--input', help='path to input file', required=True)
# args = parser.parse_args()

# add logic for completing paths later

def distance(p1, p2):
    '''Compute 2D Euclidian distance between two (x,y) points.'''
    return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)

G = nx.Graph()

with open("/home/kian/Lab/62_20200218-131149_004_plantB_day14.txt", "r") as f:
    q = Queue()
    node_num = 1 # label nodes
    for line in f:
        if line.startswith("##"): # Level heading
            group_num = 0 # count nodes per level. reset on level change
            level = int(line.rstrip().split(": ")[1])
            continue
        else:
            info = line.rstrip().split("; ")
            if len(info) > 1:
                coords = tuple(int(float(i)) for i in info[0].split())[0:2] # change output coords from floats to ints
                G.add_node(node_num, pos = coords)
                if not q.empty(): # skip first node
                    parent = q.get()
                    if level == parent[1][0] and group_num == parent[1][1]:
                        G.add_edge(node_num, parent[0], length = distance(G.nodes[node_num]['pos'], G.nodes[parent[0]]['pos']))
                    else:
                        print("Edge assignment failed!")
                        break
                children = info[1].split()
                for child in children:
                    q.put((node_num, list(map(int, child.strip('[]').split(','))))) # converts each 'child' object from list of strings to list of ints
            else: # terminal node
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