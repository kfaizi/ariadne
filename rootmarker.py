"""GUI for segmenting RSA scans. Kian Faizi Feb-11-2020."""

# TO-DO:
# do we need backtracking? This will be inefficient (less important),
#   and might affect indexing or iterator position (more important)
# maybe swap 'end of GIF!' with a constant "day n_i/n" indicator
# dealing with multiple plants/trees
# build standalone executable when finished

# THINK ABOUT:
# add quick message when output created successfully
# standardize image scaling (nxn)
# show point coordinates on mouse hover?
# zoom/pan/rescale?

# note: if 'plus' cursor changes to a normal arrow, it's due to loss of focus
# fix by clicking on the top bar of the image window

import tkinter as tk
from tkinter.filedialog import askopenfilename
from PIL import Image, ImageTk, ImageSequence
from pathlib import Path

root = tk.Tk()  # not to be confused with other appearances of 'root' :)
w = tk.Canvas(root, cursor="plus", width=2000, height=2000)


class Node(object):
    def __init__(self, coords, shape_val):
        self.coords = coords  # (x,y) tuple
        self.relcoords = None  # (x,y) relative to root node
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
        self.day = 1  # initially

    def add_node(self, add):

        if tree.nodes:
            for n in tree.nodes:
                if n.is_selected:
                    add.depth = n.depth + 1
                    n.add_child(add)
        else:  # if no nodes yet assigned
            add.is_top = True
            add.depth = 0

        self.nodes.append(add)  # finally, add to tree (avoid self-assignment)
        # and since first element of nodes will always be root node:
        add.relcoords = (add.coords[0]-(tree.nodes[0].coords[0]), add.coords[1]-(tree.nodes[0].coords[1]))

    def make_file(self):
        """Output tree data to file."""
        # sort all nodes by depth for printing (stable)
        ordered_tree = sorted(self.nodes, key=lambda node: node.depth)

        # prepare output file
        output_name = f"day{self.day}_output.txt"
        output_path = Path("/Users/kianfaizi/Desktop/", output_name)

        with open(output_path, "a") as h:
            tracker = 0  # track depth changes to output correct level
            kidcount = 0  # track number of child nodes per level
            h.write(f"## Level: 0")
            h.write("\n")

            for i in range(len(ordered_tree)):
                curr = ordered_tree[i]

                if tracker != curr.depth:
                    h.write(f"## Level: {curr.depth}")
                    h.write("\n")
                    tracker = curr.depth
                    kidcount = 0

                h.write(f"{curr.relcoords[0]} {curr.relcoords[1]} 0;".rstrip("\n"))

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
                x = w.create_line(kid.coords[0], kid.coords[1], n.coords[0], n.coords[1], fill="white")
                tree.edges.append(x)
    else:
        for x in tree.edges:
            w.delete(x)
        tree.edges = []


def generate_file(event):
    """Output annotation results to a text file."""
    global tree
    tree.make_file()


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


def show_relcoords(event):
    """Display the (x,y) coordinates of the point clicked, relative to top."""
    for n in tree.nodes:  # check click proximity to existing points
        if ((abs(n.coords[0]-event.x)) < 10) and ((abs(n.coords[1]-event.y)) < 10):
            w.create_text(event.x, event.y, anchor="nw", text=f"{n.relcoords[0]},{n.relcoords[1]}", fill="white")
            return


def override(event):
    """Override proximity limit on node placement, to allow closer tags."""
    global prox_override, override_text

    if prox_override:
        prox_override = False
        w.itemconfig(override_text, state="hidden")
    else:
        prox_override = True
        if override_text:
            w.itemconfig(override_text, state="normal")
        else:
            override_text = w.create_text(10, 10, anchor="nw", text="override=ON", fill="white")
    w.pack()


def place_node(event):
    """Place or select points on click."""
    global prox_override

    w.focus_set()  # keep focus on the canvas (allows keybinds)
    w.config(cursor="plus")

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
    # first node shape_val is 2, because initial image is 1
    idx = w.create_oval(click_x, click_y, click_x+2, click_y+2, width=0, fill="red")
    point = Node((click_x, click_y), idx)
    tree.add_node(point)
    for n in tree.nodes:  # deselect all previous points
        n.is_selected = False
        w.itemconfig(n.shape_val, fill="white")
    point.is_selected = True
    w.itemconfig(point.shape_val, fill="red")


def next_day(event):
    """Show the next frame in the GIF."""
    global iterframes, frame_index, tree, frame_id, newpic, end_text

    try:
        # generate_file(event)  # before advancing, output data so far
        frame_index += 1
        tree.day = frame_index + 1
        newframe = iterframes[frame_index].resize((2000, 2000))
        newpic = ImageTk.PhotoImage(newframe)

        new_frame_id = w.create_image(0, 0, image=newpic, anchor="nw")
        w.delete(frame_id)
        w.tag_lower(new_frame_id)
        frame_id = new_frame_id

    except IndexError:  # end of GIF
        end_text = w.create_text(10, 25, anchor="nw", text="end of GIF!", fill="white")

    w.pack()


img = askopenfilename(parent=root, initialdir="./", title="Select a file")
img = Image.open(img)
iterframes = ImageSequence.Iterator(img)

img_shift = img.resize((2000, 2000))
frame = ImageTk.PhotoImage(img_shift)

frame_index = 0
frame_id = w.create_image(0, 0, image=frame, anchor="nw")

w.pack()
w.focus_force()  # fix cursor issue the first time

# keybinds
w.bind("<Button 1>", place_node)
w.bind("<Button 2>", select_parent)
w.bind("<Button 3>", show_relcoords)
w.bind("e", next_day)
# w.bind("q", previous_day)
w.bind("d", delete)
w.bind("a", select_all)
w.bind("g", generate_file)
w.bind("t", show_tree)
w.bind("r", override)

selected_all = False
prox_override = False
override_text = None  # prox override indicator
end_text = None  # end-of-GIF indicator

tree = Tree()
root.mainloop()
