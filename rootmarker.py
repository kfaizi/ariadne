"""GUI for segmenting RSA scans. Kian Faizi Feb-11-2020.

-Assumes root = ternary tree
-Can't make changes to tree when stepping back; if you goof, you restart
-Can't 'insert' node anywhere other than along mid children (OK for us,
since no secondary LRs will emerge on our time scale)
-If 'plus' cursor changes to normal arrow, it's due to loss of focus;
fix it by clicking on the top bar of the image/canvas window

TO-DO:
Mark multiple plants/plate
  eg keybind 'next plant' func to instantiate new tree

Refactor nested conditionals (states?)
Hide relcoords on re-click
Cycle through nearby points when selecting:
- Add flag when visited
- Cycle thru (False)
- Reset when a new point is placed or deleted, or if all are selected
add quick message when output created successfully
standardize image scaling (nxn). Basically normalize relcoords by dimensions
zoom/pan/rescale
Scroll to select points?
"""


import tkinter as tk
from tkinter.filedialog import askopenfilename
from PIL import Image, ImageTk, ImageSequence
from pathlib import Path


root = tk.Tk()  # not to be confused with other appearances of 'root' :)
w_width = 250
w_height = 250
w = tk.Canvas(root, cursor="plus", width=w_width, height=w_height)


class Node(object):
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
        self.first = None  # to track the order L/R children were added in

    def add_child(self, obj):
        global tree

        if inserting:
            obj.mid = self.mid  # new point becomes parent of old child
            self.mid = obj  # and becomes the new child

            # finally, we shift everything downstream a level lower:
            obj.mid.depth += 1
            # treating obj.mid as the root node, walk subtree to update depths
            tree.DFS(obj.mid)

        else:
            numkids = (3 - [self.left, self.mid, self.right].count(None))

            if numkids == 0:
                self.mid = obj

            elif numkids == 1:  # added to enable capturing first direction
                if (self.coords[0] - obj.coords[0]) > 0:  # child is on left
                    self.left = obj
                    self.first = "left"
                elif (self.coords[0] - obj.coords[0]) < 0:  # child is on right
                    self.right = obj
                    self.first = "right"
                else:
                    # ambiguity: both points have same x-coordinates
                    # add user input to manually mark L/R?
                    pass

            elif numkids < 3:
                if (self.coords[0] - obj.coords[0]) > 0:  # child is on left
                    self.left = obj
                elif (self.coords[0] - obj.coords[0]) < 0:  # child is on right
                    self.right = obj
                else:
                    # again, ambiguity
                    # add user input to manually mark L/R?
                    pass
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
    def __init__(self):
        self.nodes = []
        self.edges = []
        self.day = 1  # initially
        self.is_shown = False

    def add_node(self, obj):
        global tree_flag

        if tree.nodes:
            for n in tree.nodes:
                if n.is_selected:
                    obj.depth = n.depth + 1  # child is one level lower
                    # since first element of nodes will always be root node:
                    obj.relcoords = ((obj.coords[0]-(tree.nodes[0].coords[0]))/w_width, (obj.coords[1]-(tree.nodes[0].coords[1]))/w_height)
                    n.add_child(obj)
        else:  # if no nodes yet assigned
            obj.depth = 0
            obj.relcoords = (0, 0)
        # finally, add to tree (avoid self-assignment)
        self.nodes.append(obj)

        if inserting:
            # silly method, fix this later. for now:
            # 1) delete existing tree
            for line in tree.edges:
                w.delete(line)
            tree.edges = []

            # 2) then redraw it based on new nodes post-insertion
            for n in tree.nodes:
                if n.left is not None:
                    x = w.create_line(n.left.coords[0], n.left.coords[1], n.coords[0], n.coords[1], fill="white", state=f"{tree_flag}")
                    tree.edges.append(x)
                if n.mid is not None:
                    x = w.create_line(n.mid.coords[0], n.mid.coords[1], n.coords[0], n.coords[1], fill="white", state=f"{tree_flag}")
                    tree.edges.append(x)
                if n.right is not None:
                    x = w.create_line(n.right.coords[0], n.right.coords[1], n.coords[0], n.coords[1], fill="white", state=f"{tree_flag}")
                    tree.edges.append(x)


    def DFS(self, root):
        root.is_visited = True
        for neighbor in (root.left, root.mid, root.right):
            if neighbor is not None and neighbor.is_visited is False:
                neighbor.depth += 1
                tree.DFS(neighbor)

    def make_file(self):
        """Output tree data to file."""
        # sort all nodes by depth for printing (stable)
        ordered_tree = sorted(self.nodes, key=lambda node: node.depth)

        # prepare output file
        output_name = f"day{self.day}_output.txt"
        output_path = Path("/Users/kianfaizi/Desktop/", output_name)

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


                ## assigning child array indices by order of addition.
                # since listsort was stable, this is necessary to make
                #  the indices monotonic
                if curr.mid is not None:  # mid is always first
                    h.write(f" [{curr.mid.depth},{kidcount}]".rstrip("\n"))
                    kidcount += 1
                if curr.first == "left":
                    h.write(f" [{curr.left.depth},{kidcount}]".rstrip("\n"))
                    kidcount += 1
                    if curr.right is not None:
                        h.write(f" [{curr.right.depth},{kidcount}]".rstrip("\n"))
                        kidcount += 1
                elif curr.first == "right":
                    h.write(f" [{curr.right.depth},{kidcount}]".rstrip("\n"))
                    kidcount += 1
                    if curr.left is not None:
                        h.write(f" [{curr.left.depth},{kidcount}]".rstrip("\n"))
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
    tree.make_file()


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
            x = w.create_line(n.left.coords[0], n.left.coords[1], n.coords[0], n.coords[1], fill="white", state=f"{tree_flag}")
            tree.edges.append(x)
        if n.mid is not None:
            x = w.create_line(n.mid.coords[0], n.mid.coords[1], n.coords[0], n.coords[1], fill="white", state=f"{tree_flag}")
            tree.edges.append(x)
        if n.right is not None:
            x = w.create_line(n.right.coords[0], n.right.coords[1], n.coords[0], n.coords[1], fill="white", state=f"{tree_flag}")
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
    for n in tree.nodes:  # check click proximity to existing points
        if ((abs(n.coords[0]-event.x)) < 10) and ((abs(n.coords[1]-event.y)) < 10):
            w.create_text(event.x, event.y, anchor="nw", text=f"{n.relcoords[0]},{n.relcoords[1]}", fill="white")
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
    w.pack()


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

    w.pack()


def place_node(event):
    """Place or select points on click."""
    global prox_override, tree, tree_flag

    w.focus_set()  # keep focus on the canvas (allows keybinds)
    w.config(cursor="plus")

    if selected_all is True and len(tree.nodes) == 0:  # quietly change selected_all flag to False when no points exist (logically)
        select_all(event)
    elif selected_all is True and len(tree.nodes) > 0:
        print("Can't assign child to multiple nodes at once! Select just one and try again.")
        select_all(event)
        return

    if inserting:  # choose the new point to be inserted
        idx = w.create_oval(event.x, event.y, event.x+2, event.y+2, width=0, fill="white")
        point = Node((event.x, event.y), idx)

        # for insertion mode only, we draw lines in add_child()
        tree.add_node(point)

        for n in tree.nodes:  # deselect all other points
            n.deselect()
        point.select()

        insert(event)  # turn off insertion mode after placing new point

        return

    if not prox_override:
        for n in tree.nodes:  # check click proximity to existing points
            if ((abs(n.coords[0]-event.x)) < 10) and ((abs(n.coords[1]-event.y)) < 10):

                if not n.is_selected:  # select an unselected point
                    for m in tree.nodes:  # first deselect all points
                        m.deselect()
                    n.select()  # then select chosen point
                return

    # place a new point, selected by default
    # first node shape_val is 2, because initial image is 1
    idx = w.create_oval(event.x, event.y, event.x+2, event.y+2, width=0, fill="red")
    point = Node((event.x, event.y), idx)
    tree.add_node(point)

    for n in tree.nodes:  # draw new line, and deselect all other points
        if n.is_selected:  # then n is parent
            x = w.create_line(point.coords[0], point.coords[1], n.coords[0], n.coords[1], fill="white", state=f"{tree_flag}")
            tree.edges.append(x)
        n.deselect()

    point.select()


def next_day(event):
    """Show the next frame in the GIF."""
    global iterframes, frame_index, tree, frame_id, newpic, start_text, end_text

    try:
        newframe = iterframes[frame_index+1].resize((w_width, w_height))
        newpic = ImageTk.PhotoImage(newframe)

        new_frame_id = w.create_image(0, 0, image=newpic, anchor="nw")
        w.delete(frame_id)
        w.tag_lower(new_frame_id)
        frame_id = new_frame_id

        frame_index += 1
        tree.day = frame_index + 1

        w.delete(start_text)
        start_text = None

    except IndexError:  # end of GIF
        if end_text is None:
            end_text = w.create_text(10, 25, anchor="nw", text="end of GIF!", fill="white")

    w.pack()


def previous_day(event):
    """Show the previous frame in the GIF."""
    global iterframes, frame_index, tree, frame_id, newpic, start_text, end_text

    try:
        newframe = iterframes[frame_index-1].resize((w_width, w_height))
        newpic = ImageTk.PhotoImage(newframe)

        new_frame_id = w.create_image(0, 0, image=newpic, anchor="nw")
        w.delete(frame_id)
        w.tag_lower(new_frame_id)
        frame_id = new_frame_id

        frame_index -= 1
        tree.day = frame_index + 1

        w.delete(end_text)
        end_text = None

    except IndexError:  # start of GIF
        if start_text is None:
            start_text = w.create_text(10, 25, anchor="nw", text="start of GIF!", fill="white")

    w.pack()


img = askopenfilename(parent=root, initialdir="./", title="Select a file")
img = Image.open(img)
iterframes = ImageSequence.Iterator(img)

img_shift = img.resize((w_width, w_height))
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
w.bind("q", previous_day)
w.bind("d", delete)
w.bind("a", select_all)
w.bind("g", generate_file)
w.bind("t", show_tree)
w.bind("r", override)
w.bind("i", insert)

selected_all = False
prox_override = False
override_text = None  # prox override indicator
inserting = False
inserting_text = None  # insertion mode indicator
start_text = None  # start-of-GIF-indicator
end_text = None  # end-of-GIF indicator
tree_flag = "hidden"

tree = Tree()
root.mainloop()
