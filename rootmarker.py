"""Test GUI script for annotating RSA scans. Kian Faizi Feb-11-2020."""

# TO-DO:
# show point coordinates on mouse hover
# take user input to name output file

# zoom/pan/rescale


import tkinter as tk
from tkinter.filedialog import askopenfilename
from PIL import Image, ImageTk
from queue import Queue

root = tk.Tk()  # not to be confused with other appearances of 'root' :)
w = tk.Canvas(root, width=1000, height=1000)


class Node(object):
    def __init__(self, coords, shape_val):
        self.coords = coords  # (x,y) tuple
        self.shape_val = shape_val  # canvas object ID
        self.is_selected = False
        self.is_top = False
        self.is_visited = False
        self.depth = None
        self.children = []

    def add_child(self, obj):
        global tree

        if (len(self.children) < 3):
            self.children.append(obj)
        else:
            print("All children already assigned to point", self)
            w.delete(obj.shape_val)


class Tree(object):
    def __init__(self):
        self.nodes = []
        self.edges = []

    def add_node(self, obj):
        for n in tree.nodes:
            if n.is_selected:
                n.add_child(obj)
        if not tree.nodes:  # if no nodes yet assigned
            obj.is_top = True
        self.nodes.append(obj)

    def make_file(self, root, output):
        """Traverse the tree breadth-first and output data to file."""
        q = Queue()
        q.put(root)
        root.depth = 0

        while not q.empty():  # assign depths; level order traversal
            curr = q.get()

            for i in range(len(curr.children)):
                kid = curr.children[i]
                kid.depth = curr.depth + 1
                q.put(kid)

        # sort all nodes by depth for printing
        ordered_tree = sorted(self.nodes, key=lambda node: node.depth)

        with open(output, "a") as h:
            tracker = root.depth
            kidcount = 0
            h.write(f"## Level: {root.depth}")
            h.write("\n")

            for i in range(len(ordered_tree)):
                curr = ordered_tree[i]

                if tracker != curr.depth:
                    h.write(f"## Level: {curr.depth}")
                    h.write("\n")
                    tracker = curr.depth
                    kidcount = 0

                h.write(f"{curr.coords[0]} {curr.coords[1]} 0;".rstrip("\n"))

                for i in range(len(curr.children)):
                    kid = curr.children[i]
                    h.write(f" [{kid.depth},{kidcount}]".rstrip("\n"))
                    kidcount += 1

                h.write("\n")


def show_tree(event):
    global tree

    if not tree.edges:
        for n in tree.nodes:
            for kid in n.children:
                x = w.create_line(kid.coords[0], kid.coords[1], n.coords[0], n.coords[1])
                tree.edges.append(x)
    else:
        for x in tree.edges:
            w.delete(x)
        tree.edges = []


def generate_file(event):
    global tree
    for n in tree.nodes:
        if n.is_top:
            tree.make_file(n, "/path/to/output.txt")


def delete(event):  # probably remove from final iteration
    """Remove selected nodes, including parent references."""
    global tree
    newtree = []

    for n in tree.nodes:
        new_children = []
        for kid in n.children:
            if not kid.is_selected:
                new_children.append(kid)
        n.children = new_children

    for n in tree.nodes:
        if n.is_selected:
            w.delete(n.shape_val)
        else:
            newtree.append(n)

    tree.nodes = newtree


def select_all(event):  # probably remove from final iteration
    """Select/deselect all nodes."""
    global tree
    global selected_all

    if not selected_all:
        for n in tree.nodes:
            n.is_selected = True
            w.itemconfig(n.shape_val, fill="red")
        selected_all = True
    else:
        for n in tree.nodes:
            n.is_selected = False
            w.itemconfig(n.shape_val, fill="white")
        selected_all = False


def select_parent(event):
    """Select the parent of the last placed point."""
    global tree

    for n in tree.nodes:
        for kid in n.children:
            if kid.is_selected:
                kid.is_selected = False
                w.itemconfig(kid.shape_val, fill="white")

                n.is_selected = True
                w.itemconfig(n.shape_val, fill="red")

                return


def override(event):
    """Override proximity limit on node placement, to allow closer tags."""
    global prox_override, text

    if prox_override:
        prox_override = False
        w.delete(text)
    else:
        prox_override = True
        text = w.create_text(10, 10, anchor="nw", text="override=ON", fill="white")


def place_node(event):
    """Place or select points on click."""
    global prox_override
    w.focus_set()  # keep focus on the canvas (allows keybinds)
    click_x = event.x
    click_y = event.y

    if not prox_override:
        for n in tree.nodes:  # check click proximity to existing points
            if ((abs(n.coords[0]-click_x)) < 10) and ((abs(n.coords[1]-click_y)) < 10):

                if not n.is_selected:  # to select a new point
                    for m in tree.nodes:  # first deselect all points
                        m.is_selected = False
                        w.itemconfig(m.shape_val, fill="white")
                    n.is_selected = True  # then select desired point
                    w.itemconfig(n.shape_val, fill="red")
                return

    # place a new point, selected by default
    # (note: for some reason, idx/shape_val starts at 2)
    idx = w.create_oval(click_x, click_y, click_x+2, click_y+2, width=0, fill="red")
    point = Node((click_x, click_y), idx)
    tree.add_node(point)
    for n in tree.nodes:  # deselect all previous points
        n.is_selected = False
        w.itemconfig(n.shape_val, fill="white")
    point.is_selected = True
    w.itemconfig(point.shape_val, fill="red")


img = askopenfilename(parent=root, initialdir="./", title="Select an image to annotate")
img = Image.open(img)
img = img.resize((1500, 1500))
pic = ImageTk.PhotoImage(img)
w.pack()
w.create_image(0, 0, image=pic, anchor="nw")

# keybinds
w.bind("<Button 1>", place_node)
w.bind("<Button 2>", select_parent)
w.bind("d", delete)
w.bind("a", select_all)
w.bind("m", generate_file)
w.bind("t", show_tree)
w.bind("r", override)

selected_all = False
prox_override = False

text = None

tree = Tree()
root.mainloop()
