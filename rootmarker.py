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
history = {}


def click(event):
    """On click, save (x,y) and place a point, or select an existing one."""
    click_x = event.x
    click_y = event.y

    for k, v in history.items():  # check proximity to existing points
        if (abs(v[0] - click_x < 10)) and (abs(v[1] - click_y) < 10):
            return  # this avoids placing a new point
    # add logic to mark as parent
    # Need keybind to override (eg for emergent LRs)
    # instead of dict parsing, use TST for proximity search?

    # for some reason, the keys (point #) start at 2:
    point = w.create_oval(click_x, click_y, click_x+2, click_y+2, width=0, fill="white")
    history[point] = (click_x, click_y)


def delete(event):
    """Remove a placed point, starting with most recent."""
    try:
        recent = max(history)
        w.delete(recent)
        del history[recent]
    except Exception:
        print("No remaining points to delete.")


img = askopenfilename(parent=root, initialdir="./", title="Select an image to annotate")
img = Image.open(img)
img = img.resize((1000, 1000))
pic = ImageTk.PhotoImage(img)
w.pack()
w.create_image(0, 0, image=pic, anchor="nw")

w.bind("<Button 1>", click)
w.bind("<Button 2>", delete)

root.mainloop()
