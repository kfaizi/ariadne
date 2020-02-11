"""Test GUI app for annotating RSA scans. Kian Faizi Feb-11-2020."""
# so far can add or remove points w/ saved coordinates
# but no connection/child data
# no zoom/pan/rescale ability
# and no file output

import tkinter as tk
from tkinter.filedialog import askopenfilename
from PIL import Image, ImageTk

root = tk.Tk()
w = tk.Canvas(root, width=1000, height=1000)
history = dict()


def click(event):
    """Save x,y on click and place a point."""
    click_x = event.x
    click_y = event.y
    point = w.create_oval(click_x, click_y, click_x+2, click_y+2, width=0, fill='white')
    history[point] = (click_x, click_y)


def delete(event):
    """Remove placed points, starting with most recent."""
    recent = max(history)
    w.delete(recent)
    del history[recent]


img = askopenfilename(parent=root, initialdir="./", title='Select an image to annotate')
img = Image.open(img)
img = img.resize((1000, 1000))
pic = ImageTk.PhotoImage(img)
w.pack()
w.create_image(0, 0, image=pic, anchor="nw")

w.bind("<Button 1>", click)
w.bind("<Button 2>", delete)

root.mainloop()
