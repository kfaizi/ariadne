"""Test GUI script for annotating RSA scans. Kian Faizi Feb-11-2020."""
# so far can add or remove points w/ saved coordinates
# but no connection/child data
# no zoom/pan/rescale ability
# and no file output

import tkinter as tk
from tkinter.filedialog import askopenfilename
from PIL import Image, ImageTk

root = tk.Tk()
w = tk.Canvas(root, width=1000, height=1000)

tree = []  # temp 'tree' (list of nodes)

# class Tree(object):
#     def __init__(self):
#         self.nodes = []

#     def add_node(self, coord, shapeval):
#         node = Node(coord, shapeval)


class Node(object):
    def __init__(self, coords, shapeval):
        self.coords = coords  # (x,y) tuple
        self.children = []  # format [level, number] x n
        self.shapeval = shapeval  # canvas object ID
        self.is_selected = False
        self.leftNode = None
        self.middleNode = None
        self.rightNode = None

    def add_child(self, obj):
        self.children.append(obj)


def delete(event):
    """Remove selected nodes."""
    global tree
    newtree = []

    for node in tree:
        if node.is_selected:
            w.delete(node.shapeval)
        else:
            newtree.append(node)
    tree = newtree


def click(event):
    """Place or select points on click."""
    w.focus_set()  # keep focus on the canvas (allows keybinds)
    click_x = event.x
    click_y = event.y

    for node in tree:  # check click proximity to existing points
        if ((abs(node.coords[0]-click_x)) < 10) and ((abs(node.coords[1]-click_y)) < 10):
            if node.is_selected:  # deselect a point
                node.is_selected = False
                w.itemconfig(node.shapeval, fill="white")
            else:  # select a new point
                node.is_selected = True
                w.itemconfig(node.shapeval, fill="red")
            return

    # place a new point
    # (for some reason, shapevals start at 2)
    idx = w.create_oval(click_x, click_y, click_x+2, click_y+2, width=0, fill="white")
    point = Node((click_x, click_y), idx)
    tree.append(point)


img = askopenfilename(parent=root, initialdir="./", title="Select an image to annotate")
img = Image.open(img)
img = img.resize((1500, 1500))
pic = ImageTk.PhotoImage(img)
w.pack()
w.create_image(0, 0, image=pic, anchor="nw")

w.bind("<Button 1>", click)
w.bind("d", delete)

root.mainloop()
