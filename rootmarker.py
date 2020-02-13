"""Test GUI script for annotating RSA scans. Kian Faizi Feb-11-2020."""
# no zoom/pan/rescale ability
# and no file output

import tkinter as tk
from tkinter.filedialog import askopenfilename
from PIL import Image, ImageTk

root = tk.Tk()
w = tk.Canvas(root, width=1000, height=1000)


class Node(object):
    def __init__(self, coords, shape_val):
        self.coords = coords  # (x,y) tuple
        self.shape_val = shape_val  # canvas object ID
        self.is_selected = False
        self.children = []

    def add_child(self, obj):
        if (len(self.children) < 3):
            self.children.append(obj)
        else:
            print("Too many children assigned to point", self)


class Tree(object):
    def __init__(self):
        self.nodes = []

    def add_node(self, obj):
        for n in tree.nodes:
            if n.is_selected:
                n.add_child(obj)
        self.nodes.append(obj)  # last -- to avoid assigning child to itself


tree = Tree()


def delete(event):
    """Remove selected nodes."""
    global tree
    newtree = []

    for n in tree.nodes:
        if n.is_selected:
            w.delete(n.shape_val)
        else:
            newtree.append(n)
    tree.nodes = newtree


def clear_all(event):
    """Deselect all selected nodes."""
    global tree
    for n in tree.nodes:
        n.is_selected = False
        w.itemconfig(n.shape_val, fill="white")


def select_all(event):
    """Select all nodes."""
    global tree
    for n in tree.nodes:
        n.is_selected = True
        w.itemconfig(n.shape_val, fill="red")


def click(event):
    """Place or select points on click."""
    w.focus_set()  # keep focus on the canvas (allows keybinds)
    click_x = event.x
    click_y = event.y

    for n in tree.nodes:  # check click proximity to existing points
        if ((abs(n.coords[0]-click_x)) < 10) and ((abs(n.coords[1]-click_y)) < 10):
            if n.is_selected:  # deselect a point
                n.is_selected = False
                w.itemconfig(n.shape_val, fill="white")
            else:  # select a new point
                n.is_selected = True
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

w.bind("<Button 1>", click)
w.bind("d", delete)
w.bind("c", clear_all)
w.bind("a", select_all)

root.mainloop()
