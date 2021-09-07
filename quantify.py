'''Parse graphs in custom .xyz format, and measure traits.
Points are stored in a tree using an undirected NetworkX graph.
Each node has a unique numerical identifier (node_num), and an attribute "pos": an (x,y) coordinate pair corresponding to its position in 2D space.
Each edge has an attribute "length": the Euclidean distance between the nodes it connects.
TO-DO:
Trait measurement
Time series
'''

import argparse
import networkx as nx
import math
from queue import Queue
from pareto_functions import pareto_front, random_tree
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
                            print(f"ERROR: Edge assignment failed: {parent}; {level}; {group_num}; {info}")
                            # return f"Edge assignment failed: {parent}; {level}; {group_num}; {info}"
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
                        print("ERROR: Edge assignment failed: terminal node.")
                        # return "Edge assignment failed: terminal node."
                node_num += 1
                group_num += 1
    #return "Done!" (used for csv creation)
    return G


def make_graph_alt(target):
    '''Construct a broken graph (without problematic edges).'''
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
                            print(f"Edge assignment failed: {parent}; {level}; {group_num}; {info}")
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
                        print("Edge assignment failed: terminal node.")
                node_num += 1
                group_num += 1
    return G

def save_plot(path, name, title):
    '''Plot a Pareto front and save to .jpg.'''

    G = make_graph(path)
    # check that graph is indeed a tree (acyclic, undirected, connected)
    assert nx.is_tree(G)

    mcosts, scosts, actual = pareto_front(G)
    randoms = random_tree(G)

    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.set_title(title)
    ax.set_xlabel("Total length", fontsize=15)
    ax.set_ylabel("Travel distance", fontsize=15)

    plt.plot(mcosts, scosts, marker='s', linestyle='-', markeredgecolor='black')
    plt.plot(actual[0], actual[1], marker='x', markersize=12)
    for i in randoms:
        plt.plot(i[0], i[1], marker='+', color='green', markersize=4)

    # plt.savefig(name, bbox_inches='tight', dpi=300)
    plt.show()


# path, name, title
# targets = [
#     ['/home/kian/Lab/9_20200205-214859_003_plantB_day13.txt', '9-B-13-rand.jpg', '+Fe_B_Day13'],
#     ['/home/kian/Lab/9_20200205-214859_003_plantE_day13.txt', '9-E-13-rand.jpg', '+Fe_E_Day13'],
#     ['/home/kian/Lab/13_20200205-214859_005_plantB_day12.txt', '13-B-12-rand.jpg', '-Fe_B_Day12'],
#     ['/home/kian/Lab/13_20200205-214859_005_plantE_day12.txt', '13-E-12-rand.jpg', '-Fe_E_Day12'],
#     ['/home/kian/Lab/25_20200205-215844_026_plantB_day14.txt', '25-B-14-rand.jpg', '+N_B_Day14'],
#     ['/home/kian/Lab/25_20200205-215844_026_plantD_day14.txt', '25-D-14-rand.jpg', '+N_D_Day14'],
#     ['/home/kian/Lab/29_20200205-215844_028_plantA_day14.txt', '29-A-14-rand.jpg', '-N_A_Day14'],
#     ['/home/kian/Lab/29_20200205-215844_028_plantB_day14.txt', '29-B-14-rand.jpg', '-N_B_Day14']
# ]

# for i in targets:
#     save_plot(i[0], i[1], i[2])

# save_plot('/Users/kianfaizi/projects/test-roots/BUGS/graph breaking and str/A/1_20200205-215035_009_plantA_day8.txt', 'test.jpg', 'test')

def show_skel(target):
    '''Plot a nx graph/skel from a .txt file.'''
    G = make_graph(target)
    layout = {} # dict of nodes:positions
    for i in G.nodes.data():
        node = i[0]
        pos = i[1]['pos']
        layout[node] = pos 
    nx.draw_networkx(G, pos=layout)
    plt.show()

show_skel('/Users/kianfaizi/projects/test-roots/BUGS/graph breaking and str/A/1_20200205-215035_009_plantA_day12.txt')


def analyze(target):
    '''Report basic root metrics for a given graph.'''
    G = make_graph(target)
    mcosts, scosts, actual = pareto_front(G)
    # total len
    print("Total length (material cost) of roots: ", mcosts)
    # transport cost
    print("Wiring/transport cost of roots: ", scosts)
    # PR len
    # the path from node 0 to a critical node which has the most nodes of degree >2 along it (most branching points)
    # examine graph_costs calculations for help

    # LR len

    # LR density + number
    # find all nodes of degree >2 (branching points)
    # map which are on PR (primary LRs) and so on

    # LR angles
    # how is it calculated? (relative to upper PR or lower PR?)
    # for each relevant branching point

    # think about dynamics/time-series

    # distance of each plant to pareto front

    # distance of center-of-mass of randoms to the pareto front

    # literally purchase a nice mouse for matt