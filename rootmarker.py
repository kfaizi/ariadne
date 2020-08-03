"""GUI for segmenting RSA scans. Copyright 2020 Kian Faizi.

TO-DO:
n-nary tree
better UI (sticky visible indicators)
Mark multiple plants/plate
try:except for dialog errors?
refactor nested conditionals (states?)
hide relcoords on second-click
easier selection of nearby points
add message when output created successfully?
"""

import tkinter as tk
from tkinter.filedialog import askopenfilename
from PIL import Image, ImageTk, ImageSequence
from pathlib import Path
from queue import Queue
from collections import deque
import pytest


class Application(tk.Canvas):
    """The GUI interface."""

    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.width = w_width
        self.height = w_height

    def display_tooltips(self):
        pass


class Node(object):
    """An (x,y,0) point along a root."""

    def __init__(self, coords, shape_val):
        self.coords = coords  # (x,y) tuple
        self.relcoords = None  # (x,y) relative to root node
        self.shape_val = shape_val  # canvas object ID
        self.is_selected = False
        self.is_visited = False
        self.depth = None
        self.left = None
        self.mid = None
        self.right = None
        self.index = 2  # if the node is a left child, 0; right, 1; mid, 2
        self.is_PR = True  # primary root
        self.LR_index = None  # if lateral root, denote by index

    def add_child(self, obj):  # where obj is the node being added
        global tree

        if inserting:
            obj.mid = self.mid  # new node becomes parent of old child
            self.mid = obj  # and becomes the new child

            if self.is_PR is False:  # if inserting on an LR
                obj.is_PR = False

            # finally, shift everything downstream 1 level lower
            obj.mid.depth += 1
            tree.DFS(obj.mid)  # update depths for subtree with root = obj.mid

        else:
            numkids = (3 - [self.left, self.mid, self.right].count(None))

            if numkids == 0:
                self.mid = obj
                if self.is_PR is False:  # if parent is an LR
                    obj.is_PR = False

            elif numkids < 3:
                if (self.coords[0] - obj.coords[0]) > 0:  # child is on left
                    self.left = obj
                    obj.index = 0

                elif (self.coords[0] - obj.coords[0]) < 0:  # child is on right
                    self.right = obj
                    obj.index = 1

                else:
                    # ambiguity! undefined behavior
                    # add user input to manually mark L/R?
                    print("Something went wrong.")  # placeholder only

                obj.is_PR = False

            else:
                print("Error: all 3 children already assigned to point", self)
                w.delete(obj.shape_val)

    def select(self):
        self.is_selected = True
        w.itemconfig(self.shape_val, fill="red", outline="red", width=2)

    def deselect(self):
        self.is_selected = False
        w.itemconfig(self.shape_val, fill="white", outline="white", width=0)


class Tree(object):
    """A hierarchical collection of nodes."""

    def __init__(self):
        self.nodes = []
        self.edges = []
        self.day = 1  # day (frame) of timeseries (GIF)
        self.plant = "A"  # ID of plant on plate (A-E, from left to right)
        self.is_shown = False
        self.top = None  # node object at top of tree (root node)

    def add_node(self, obj):
        global tree_flag

        if self.nodes:
            for n in self.nodes:
                if n.is_selected:
                    obj.depth = n.depth + 1  # child is one level lower
                    # since the first node will always be the root node,
                    # we calculate relcoords relative to it (nodes[0]):
                    # note: can normalize by w_width/w_height here!
                    obj.relcoords = ((obj.coords[0]-(self.nodes[0].coords[0])), (obj.coords[1]-(self.nodes[0].coords[1])))
                    n.add_child(obj)
        else:  # if no nodes yet assigned
            obj.depth = 0
            obj.relcoords = (0, 0)
            self.top = obj
        # finally, add to tree (avoid self-assignment)
        self.nodes.append(obj)

        if inserting:
            # silly method, improve this later. for now:
            # 1) delete existing tree
            for line in self.edges:
                w.delete(line)
            self.edges = []

            # 2) then redraw it based on new nodes post-insertion
            for n in self.nodes:
                if n.left is not None:
                    x = w.create_line(n.left.coords[0], n.left.coords[1], n.coords[0], n.coords[1], fill="green", state=f"{tree_flag}")
                    self.edges.append(x)
                if n.right is not None:
                    x = w.create_line(n.right.coords[0], n.right.coords[1], n.coords[0], n.coords[1], fill="green", state=f"{tree_flag}")
                    self.edges.append(x)
                if n.mid is not None:
                    x = w.create_line(n.mid.coords[0], n.mid.coords[1], n.coords[0], n.coords[1], fill="green", state=f"{tree_flag}")
                    self.edges.append(x)

    def DFS(self, root):
        root.is_visited = True
        for child in (root.left, root.mid, root.right):
            if child is not None and child.is_visited is False:
                child.depth += 1
                self.DFS(child)

    def index_LRs(self, root):
        """Walk the tree breadth-first and assign indices to lateral roots."""
        q = Queue()
        q.put(root)
        LR = 0

        while not q.empty():
            curr = q.get()

            # LR_index is assigned Left-Right, skipping the PR
            if curr.left is not None:
                curr.left.LR_index = LR
                LR += 1
                q.put(curr.left)
            if curr.right is not None:
                curr.right.LR_index = LR
                LR += 1
                q.put(curr.right)
            if curr.mid is not None:
                if curr.mid.is_PR is False:
                    curr.mid.LR_index = curr.LR_index
                q.put(curr.mid)

    def make_file(self, input_path):
        """Output tree data to file."""
        self.index_LRs(self.top)
        # sort all nodes by ascending LR index, with PR (LR_index = None) last
        # this works because False < True, and tuples are sorted element-wise
        ordered_tree = sorted(self.nodes, key=lambda node: (node.LR_index is None, node.LR_index))
        # then sort by depth
        ordered_tree = sorted(ordered_tree, key=lambda node: node.depth)

        # prepare output file
        source = Path(input_path.replace(" ","")).stem  # input name, no spaces
        
        # need this for first unit test; fix
        #source = input_path.stem
        
        
        output_name = f"day{self.day}_plant{self.plant}_{source}.txt" # hardcoded ID :(
        repo_path = Path("./").resolve()
        output_path = repo_path.parent / output_name

        with open(output_path, "a") as h:
            tracker = 0  # track depth changes to output correct level
            kidcount = 0
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

                # children ordered Left-Right-Mid, since LRs indexed Left-Right
                if curr.left is not None:
                    h.write(f" [{curr.left.depth},{kidcount}]".rstrip("\n"))
                    kidcount += 1

                if curr.right is not None:
                    h.write(f" [{curr.right.depth},{kidcount}]".rstrip("\n"))
                    kidcount += 1

                if curr.mid is not None:
                    h.write(f" [{curr.mid.depth},{kidcount}]".rstrip("\n"))
                    kidcount += 1

                h.write("\n")


def show_tree(event):
    global tree, tree_flag

    if tree.is_shown is False:
        tree_flag = "normal"
        tree.is_shown = True
    else:
        tree_flag = "hidden"
        tree.is_shown = False

    for line in tree.edges:
        w.itemconfig(line, state=f"{tree_flag}")


def generate_file(event):
    """Output annotation results to a text file."""
    global tree
    tree.make_file(imgpath)


def delete(event):  # probably remove from final iteration
    """Remove selected nodes, including parent references."""
    global tree, tree_flag
    newtree = []

    ### REFACTOR ###

    for n in tree.nodes:  # first, delete any references to selected point
        if n.left is not None:
            if n.left.is_selected:
                n.left = None
        if n.mid is not None:
            if n.mid.is_selected:
                n.mid = None
        if n.right is not None:
            if n.right.is_selected:
                n.right = None

        # now, check the points themselves
        if n.is_selected:
            w.delete(n.shape_val)
        else:
            newtree.append(n)

    tree.nodes = newtree

    # silly method, fix this later. for now:
    # 1) delete existing tree

    for line in tree.edges:
        w.delete(line)
    tree.edges = []

    # 2) then redraw it based on new nodes post-deletion
    for n in tree.nodes:
        if n.left is not None:
            x = w.create_line(n.left.coords[0], n.left.coords[1], n.coords[0], n.coords[1], fill="green", state=f"{tree_flag}")
            tree.edges.append(x)
        if n.mid is not None:
            x = w.create_line(n.mid.coords[0], n.mid.coords[1], n.coords[0], n.coords[1], fill="green", state=f"{tree_flag}")
            tree.edges.append(x)
        if n.right is not None:
            x = w.create_line(n.right.coords[0], n.right.coords[1], n.coords[0], n.coords[1], fill="green", state=f"{tree_flag}")
            tree.edges.append(x)


def select_all(event):  # probably remove from final iteration
    """Select/deselect all nodes."""
    global tree, selected_all

    if not selected_all:
        for n in tree.nodes:
            n.select()
        selected_all = True
    else:
        for n in tree.nodes:
            n.deselect()
        selected_all = False


def select_parent(event):
    """Select the parent of the last placed point."""
    global tree

    ### REFACTOR ###

    for n in tree.nodes:
        if n.left is not None:
            if n.left.is_selected:
                n.left.deselect()
                n.select()
                return

        if n.mid is not None:
            if n.mid.is_selected:
                n.mid.deselect()
                n.select()
                return

        if n.right is not None:
            if n.right.is_selected:
                n.right.deselect()
                n.select()
                return


def show_relcoords(event):
    """Display the (x,y) coordinates of the point clicked, relative to top."""
    x = w.canvasx(event.x)
    y = w.canvasy(event.y)
    for n in tree.nodes:  # check click proximity to existing points
        if ((abs(n.coords[0]-x)) < 10) and ((abs(n.coords[1]-y)) < 10):
            w.create_text(x, y, anchor="nw", text=f"{n.relcoords[0]},{n.relcoords[1]}", fill="white")
            return


def override(event):
    """Override proximity limit on node placement, to allow closer tags."""
    global prox_override, override_text

    if prox_override:
        prox_override = False
        w.delete(override_text)
    else:
        prox_override = True
        override_text = w.create_text(10, 10, anchor="nw", text="override=ON", fill="white")


def insert(event):
    """Insert a new 'mid' node between 2 existing ones."""
    # select the parent for your new node, then call this function.
    # then place the new node.

    global inserting, inserting_text

    if inserting:
        inserting = False
        w.delete(inserting_text)
    else:
        selected_count = 0
        for n in tree.nodes:
            if n.is_selected:
                if (3-[n.left, n.mid, n.right].count(None)) == 0:  # no children
                    print("Error: can't insert at terminal point")
                    return
                else:
                    selected_count += 1
        if selected_count > 1:
            print("Error: can't insert with more than one point selected")
            return

        inserting = True
        inserting_text = w.create_text(10, 40, anchor="nw", text="insertion_mode=ON", fill="white")


def place_node(event):
    """Place or select points on click."""
    global prox_override, tree, tree_flag

    x = w.canvasx(event.x)
    y = w.canvasy(event.y)
    w.focus_set()  # keep focus on the canvas (allows keybinds)

    if selected_all is True and len(tree.nodes) == 0:  # quietly change selected_all flag to False when no points exist (logically)
        select_all(event)
    elif selected_all is True and len(tree.nodes) > 0:
        print("Can't assign child to multiple nodes at once! Select just one and try again.")
        select_all(event)
        return

    if inserting:  # choose the new point to be inserted
        idx = w.create_oval(x, y, x+2, y+2, width=0, fill="white")
        point = Node((x, y), idx)

        # for insertion mode only, we draw lines in add_child()
        tree.add_node(point)

        for n in tree.nodes:  # deselect all other points
            n.deselect()
        point.select()

        insert(event)  # turn off insertion mode after placing new point

        return

    if not prox_override:
        for n in tree.nodes:  # check click proximity to existing points
            if ((abs(n.coords[0]-x)) < 10) and ((abs(n.coords[1]-y)) < 10):

                if not n.is_selected:  # select an unselected point
                    for m in tree.nodes:  # first deselect all points
                        m.deselect()
                    n.select()  # then select chosen point
                return

    # place a new point, selected by default
    # first node shape_val is 2, because initial image is 1
    idx = w.create_oval(x, y, x+2, y+2, width=0, fill="red")
    point = Node((x, y), idx)
    tree.add_node(point)

    for n in tree.nodes:  # draw new line, and deselect all other points
        if n.is_selected:  # then n is parent
            line = w.create_line(point.coords[0], point.coords[1], n.coords[0], n.coords[1], fill="green", state=f"{tree_flag}")
            tree.edges.append(line)
        n.deselect()

    point.select()


def next_day(event):
    """Show the next frame in the GIF."""
    global iterframes, frame_index, tree, frame_id, newpic, day_indicator

    try:
        newframe = iterframes[frame_index+1].resize((w_width, w_height))
        newpic = ImageTk.PhotoImage(newframe)

        new_frame_id = w.create_image(0, 0, image=newpic, anchor="nw")
        w.delete(frame_id)
        w.tag_lower(new_frame_id)
        frame_id = new_frame_id

        frame_index += 1
        tree.day = frame_index + 1
        
        w.delete(day_indicator)
        day_indicator = w.create_text(10, 25, anchor="nw", text=f"Frame #{frame_index+1}", fill="white")

    except IndexError:  # end of GIF
        w.delete(day_indicator)
        day_indicator = w.create_text(10, 25, anchor="nw", text="end of GIF!", fill="white")


def previous_day(event):
    """Show the previous frame in the GIF."""
    global iterframes, frame_index, tree, frame_id, newpic, day_indicator

    try:
        newframe = iterframes[frame_index-1].resize((w_width, w_height))
        newpic = ImageTk.PhotoImage(newframe)

        new_frame_id = w.create_image(0, 0, image=newpic, anchor="nw")
        w.delete(frame_id)
        w.tag_lower(new_frame_id)
        frame_id = new_frame_id

        frame_index -= 1
        tree.day = frame_index + 1

        w.delete(day_indicator)
        day_indicator = w.create_text(10, 25, anchor="nw", text=f"Frame #{frame_index+1}", fill="white")

    except IndexError:  # start of GIF
        w.delete(day_indicator)
        day_indicator = w.create_text(10, 25, anchor="nw", text="start of GIF!", fill="white")


class Application(tk.Frame):
    """Panning from https://stackoverflow.com/questions/20645532/move-a-tkinter-canvas-with-mouse"""
    def __init__(self, master):
        super().__init__(master)
        self.canvas = tk.Canvas(self, width=w_width, height=w_height, bg="gray")
        self.xsb = tk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.ysb = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.ysb.set, xscrollcommand=self.xsb.set)
        self.canvas.configure(scrollregion=(0, 0, 8000, 8000))

        self.xsb.grid(row=1, column=0, sticky="ew")
        self.ysb.grid(row=0, column=1, sticky="ns")
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # This is what enables scrolling with the mouse:
        self.canvas.bind("<Alt-ButtonPress-1>", self.scroll_start)
        self.canvas.bind("<Alt-B1-Motion>", self.scroll_move)

    def scroll_start(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def scroll_move(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

# scan_dragto(x,y): scrolls widget contents relative to scanning anchor.
# contents are moved 10x the distance between anchor and given position.
# scan_mark(x,y): sets scanning anchor.

history = deque(maxlen = 3)

selected_all = False
prox_override = False
override_text = None  # prox override indicator
inserting = False
inserting_text = None  # insertion mode indicator
day_indicator = None
tree_flag = "hidden"

base = tk.Tk()  # by Tk convention this is "root"; avoiding ambiguity
tree = Tree()  # instantiate first tree

if __name__ == "__main__":
    w_width = 6608
    w_height = 6614
    app = Application(base)
    w = app.canvas

    imgpath = askopenfilename(parent=base, initialdir="./", title="Select a file")
    img = Image.open(imgpath)
    iterframes = ImageSequence.Iterator(img)

    img_shift = img.resize((w_width, w_height))
    frame = ImageTk.PhotoImage(img_shift)

    frame_index = 0
    frame_id = w.create_image(0, 0, image=frame, anchor="nw")

    app.pack()
    w.focus_force()  # fix cursor issue the first time

    # keybinds
    w.bind("<Button 1>", place_node)
    w.bind("<Button 2>", show_relcoords)
    w.bind("e", next_day)
    w.bind("q", previous_day)
    w.bind("d", delete)
    w.bind("a", select_all)
    w.bind("g", generate_file)
    w.bind("t", show_tree)
    w.bind("r", override)
    w.bind("i", insert)

    #####
    # def motion_track(event):
    #     x,y = event.x, event.y
    #     print(f"{x}, {y}")
    #     print(f"Canvas stuff: {w.canvasx(x)}, {w.canvasy(y)}")

    # w.bind("<Motion>", motion_track)
    #######

    base.mainloop()