'''
ARIADNE

A GUI for segmenting root images from Arabidopsis seedlings grown on agar plates. 

Copyright 2020-2021 Kian Faizi.

TODO:
try:except for dialog errors?
easier selection of nearby points
'''

import tkinter as tk
from tkinter.filedialog import askopenfilename
from PIL import Image, ImageTk, ImageSequence
import quantify

import time

from pathlib import Path
from queue import Queue
from collections import deque
import copy

# TEST HISTORY DEQUE ACCURACY


class StartupUI:
    '''Startup window interface.'''
    def __init__(self, base):
        self.base = base
        self.base.geometry('350x200')

        # master frame
        self.frame = tk.Frame(self.base)
        self.frame.pack(side='top', fill='both', expand=True)

        # salutation
        self.title_frame = tk.Frame(self.frame)
        self.title_frame.pack()

        self.title_label = tk.Label(self.frame, text='Welcome to Ariadne')
        self.title_label.pack(side='top', fill='both', expand=True)

        # buttons
        self.trace_button = tk.Button(self.frame, text='Trace', command=self.to_trace)
        self.analyze_button = tk.Button(self.frame, text='Analyze', command=self.to_analyze)

        self.trace_button.pack(side='top', fill='both', expand=True)
        self.analyze_button.pack(side='bottom', fill='both', expand=True)
    
    def to_trace(self):
        '''Swap frames to tracing mode.'''
        self.frame.destroy()
        TracerUI(self.base)

    def to_analyze(self):
        '''Swap frames to analysis mode.'''
        self.frame.destroy()
        AnalyzerUI(self.base)



class TracerUI(tk.Frame):
    '''Tracing mode interface.'''
    def __init__(self, base):
        super().__init__(base)
        self.base = base
        self.base.geometry('750x600')
        self.base.title('Ariadne: Trace')

        # master frame
        self.frame = tk.Frame(self.base)
        self.frame.pack(side='top', fill='both', expand=True)

        # left-hand menu
        self.menu = tk.Frame(self.frame, width=175, bg='green')
        self.menu.pack(side='top', fill='both', expand=True)

        self.test_button = tk.Button(self.menu, text='Just a test')
        self.test_button.pack()

        # filename titlebar
        self.title_frame = tk.Frame(self.frame)
        self.title_label = tk.Label(self.title_frame, text='Now tracing file X')
        self.title_label.pack()

        # image canvas
        self.canvas = tk.Canvas(self.frame, width=600, height=700, bg='gray')

        # current tree
        self.tree = Tree() # instantiate first tree ## think about clearing/overwriting

        # useful flags
        self.selected_all = False # tracks whether all nodes are currently selected
        self.prox_override = False # tracks whether proximity override is on
        self.inserting = False # tracks whether insertion mode is on
        self.tree_flag = 'normal' # used for hiding/showing tree's edges
        self.colors = 0 # tracks LR color palette index

        # canvas scrollbars
        self.xsb_frame = tk.Frame(self.frame)
        self.ysb_frame = tk.Frame(self.frame)

        self.xsb = tk.Scrollbar(self.xsb_frame, orient='horizontal', command=self.canvas.xview)
        self.ysb = tk.Scrollbar(self.ysb_frame, orient='vertical', command=self.canvas.yview)
        self.xsb.pack(fill='x', expand=True)
        self.ysb.pack(fill='y', expand=True)

        self.canvas.configure(xscrollcommand=self.xsb.set, yscrollcommand=self.ysb.set, scrollregion=(0,0,7000,7000))
        self.canvas.curr_coords = (0,0) # for statusbar tracking

        # keybinds for canvas mouse panning (linux)
        self.canvas.bind("<Alt-ButtonPress-1>", self.scroll_start)
        self.canvas.bind("<Alt-B1-Motion>", self.scroll_move)
        
        # keybinds for canvas mouse panning (mac)
        self.canvas.bind("<Control-ButtonPress-1>", self.scroll_start)
        self.canvas.bind("<Control-B1-Motion>", self.scroll_move)

        # bottom statusbar
        self.statusbar_frame = tk.Frame(self.frame)
        self.statusbar = tk.Label(self.statusbar_frame, text='Statusbar here', bd=1, relief='sunken', anchor='w')
        self.statusbar.pack(fill='both', expand=True)

        # statusbar elements
        self.day_indicator = ''
        self.override_indicator = ''
        self.inserting_indicator = ''

        # keybinds for statusbar updating
        self.canvas.bind("<Motion>", self.motion_track)
        self.canvas.bind("<KeyRelease>", self.motion_track)

        # keybinds for gif pagination
        self.canvas.bind('e', self.next_day)
        self.canvas.bind('q', self.previous_day)

        # history and undo
        self.history = deque(maxlen=6) # gets updated on every add_node() or delete()
        self.canvas.bind('<Control-z>', self.undo)

        # miscellaneous keybinds
        self.canvas.bind("<Button 1>", self.place_node)
        self.canvas.bind('r', self.override)
        self.canvas.bind('i', self.insert)
        self.canvas.bind('a', self.select_all)
        self.canvas.bind('g', self.tree.make_file(self.path)) ## check this works
        self.canvas.bind('d', self.delete)
        self.canvas.bind('t', self.show_tree)


        # place widgets using grid
        self.menu.grid(row=0, column=0, rowspan=4, sticky='news')
        self.title_frame.grid(row=0, column=1, columnspan=2, sticky='ew')
        self.canvas.grid(row=1, column=1, sticky='news')
        self.statusbar_frame.grid(row=3, column=1, columnspan=2, sticky='ew')
        self.xsb_frame.grid(row=2, column=1, sticky='ew')
        self.ysb_frame.grid(row=1, column=2, sticky='ns')

        self.frame.grid_rowconfigure(1, weight=1)
        self.frame.grid_columnconfigure(1, weight=1)

        self.import_image()

    def scroll_start(self, event):
        '''Mouse panning start.'''
        self.canvas.focus_set() # allows canvas keybinds; put this in place_node() too
        self.canvas.scan_mark(event.x, event.y)

    def scroll_move(self, event):
        '''Mouse panning track.'''
        self.canvas.scan_dragto(event.x, event.y, gain=1)
    
    def motion_track(self, event):
        '''Mouse position reporting for the statusbar.'''
        if str(event.type) == 'Motion':
            # convert mouse position to canvas position
            self.canvas.curr_coords = (int(self.canvas.canvasx(event.x)), int(self.canvas.canvasy(event.y)))
        
        # statusbar contents (finish adding later)
        self.statusbar.config(text=f'{self.canvas.curr_coords}, {self.day_indicator}, {self.override_indicator}, {self.inserting_indicator}')

    def import_image(self):
        '''Query user for an input file and load it onto the canvas.'''
        self.path = askopenfilename(parent=self.base, initialdir='./', title='Select an image file:')
        self.file = Image.open(self.path)
        self.img = ImageTk.PhotoImage(self.file)

        # create gif iterator for pagination
        self.iterframes = ImageSequence.Iterator(self.file)
        self.frame_index = 0
        self.frame_id = self.canvas.create_image(0,0,image=self.img, anchor='nw')

    def change_frame(self, next_index):
        '''Move frames in the GIF.'''
        try:
            new_frame = self.iterframes[next_index]
            self.img = ImageTk.PhotoImage(new_frame)
            self.frame_id = self.canvas.create_image(0, 0, image=self.img, anchor='nw')

            self.frame_index = next_index
            self.day_indicator = f'Frame #{self.frame_index+1}'

            # finish adding later
            # tree.day = self.frame_index + 1

        except IndexError:
            self.day_indicator = 'End of GIF'

    def next_day(self, event):
        '''Show the next frame in the GIF.'''
        self.change_frame(self.frame_index+1)

    def previous_day(self, event):
        '''Show the previous frame in the GIF.'''
        self.change_frame(self.frame_index-1)

    def place_node(self, event):
        '''Place/select nodes on click.'''
        ## TODO error handling: graph components (no parent)
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        self.canvas.focus_set()

        # some guardrails for the selected_all flag
        if self.selected_all is True and len(self.tree.nodes) == 0:  # quietly change selected_all flag to False when no points exist (logically)
            self.select_all(event)
        elif self.selected_all is True and len(self.tree.nodes) > 0:
            print("Can't assign child to multiple nodes at once! Select just one and try again.")
            self.select_all(event)
            return

        # check click proximity to existing nodes
        if not self.prox_override:
            for n in self.tree.nodes:
                if ((abs(n.coords[0]-x)) < 10) and ((abs(n.coords[1]-y)) < 10):
                    if not n.is_selected:  # select a nearby unselected point
                        for m in self.tree.nodes:
                            m.deselect()
                        n.select()
                    return

        # place a new point and select it
        idx = self.canvas.create_oval(x, y, x+2, y+2, width=0, fill="red")
        point = Node((x, y), idx, self.canvas, self.tree)

        hologram, draw = self.tree.add_node(point, self.inserting)
        self.history.append(hologram) # save tree each time a node is to be added
        self.draw_edge(draw[0], draw[1])

        if self.inserting:
            self.redraw() # update edges following add_node() above
            for n in self.tree.nodes:  # deselect all other points
                n.deselect()
            self.insert(event)  # turn off insertion mode after placing new point
        else:
            for n in self.tree.nodes:
                if n.is_selected:
                    self.draw_edge(n, point)
                n.deselect()
   
        point.select()

        # turn off override mode after placing new point
        if self.prox_override:
            self.override(event)
    
    def override(self, event):
        '''Override proximity limit on node placement.'''
        if self.prox_override:
            self.prox_override = False
            self.override_indicator = ''
        else:
            self.prox_override = True
            self.override_indicator = 'override=ON'

    def insert(self, event):
        '''Insert a new middle node between 2 existing nodes.'''
        ## TODO comment this function better. also check this, but:
        # 1) select the parent for new node
        # 2) call this function
        # 3) place the new node
        if self.inserting:
            self.inserting = False
            self.inserting_indicator = ''
            if self.prox_override:
                self.override(event)
        else:
            selected_count = 0
            for n in self.tree.nodes:
                if n.is_selected:
                    if len(n.children) == 0:
                        print("Warning: can't insert at terminal point")
                        return
                    else:
                        selected_count += 1
            if selected_count > 1:
                print("Warning: can't insert with >1 point selected")
                return
            
            self.inserting = True
            self.inserting_indicator = 'inserting=ON'

            if not self.prox_override:
                self.override(event)
    
    def draw_edge(self, parent, child):
        '''Draw an edge between 2 nodes, and add it to the tree.'''
        ## TODO mid
        ## comment this better
        if child.is_PR:
            color = 'green'
        elif (parent.is_PR) and not (child.is_PR): # child is new LR
            color = self.get_color()
        else: # child is part of existing LR
            color = parent.pedge_color
        
        edge = self.canvas.create_line(parent.coords[0], parent.coords[1], child.coords[0], child.coords[1], fill=color, state=f'{self.tree_flag}')
        self.tree.edges.append(edge)
        child.pedge = edge
        child.pedge_color = color

    def get_color(self):
        '''Fetch a new LR color from the palette.'''
        palette = [ 
            # seaborn colorblind
            '#0173B2', # dark blue
            '#DE8F05', # orange
            '#029E73', # green
            '#D55E00', # red orange
            '#CC78BC', # violet
            '#CA9161', # tan
            '#FBAFE4', # pink
            '#ECE133', # yellow
            '#56B4E9', # light blue
        ]
            # 'green', # PR
            # 'red', # selected node
            # 'white', # unselected node
        
        pos = (self.colors - len(palette)) % len(palette)
        self.colors += 1
        return palette[pos] # next color

    def select_all(self, event):
        '''Select/deselect all nodes. Potentially hazardous.'''
        ## remove this, and any refs (e.g. in place_node)
        if not self.selected_all:
            for n in self.tree.nodes:
                n.select()
            self.selected_all = True
        else:
            for n in self.tree.nodes:
                n.deselect()
            self.selected_all = False
    
    def undo(self, event):
        '''Undo the last graph-altering action.'''
        ## comment this better
        try:
            previous = self.history.pop()
            for n in self.tree.nodes:
                self.canvas.delete(n.shape_val)
            for e in self.tree.edges:
                self.canvas.delete(e)
            self.tree.edges = []

            self.tree = previous

            for n in self.tree.nodes:
                x = n.coords[0]
                y = n.coords[1]
                if not n.is_selected:
                    n.shape_val = self.canvas.create_oval(x,y,x+2,y+2,width=0,fill="white")
                else:
                    n.shape_val = self.canvas.create_oval(x,y,x+2,y+2,width=0,fill="red")
            
            self.redraw()

        except IndexError as e: # end of history deque
            print(e)
            pass

    def redraw(self):
        '''Redraw the current tree's edges.'''
        # 1) delete existing tree's edges
        for e in self.tree.edges:
            self.canvas.delete(e)
        self.tree.edges = []

        # 2) redraw it based on new nodes
        for n in self.tree.nodes:
            for m in n.children:
                x = self.canvas.create_line(m.coords[0], m.coords[1], n.coords[0], n.coords[1], fill=m.pedge_color, state=f'{self.tree_flag}')
                self.tree.edges.append(x)

    def show_tree(self, event):
        '''Toggle visibility of tree edges.'''
        if self.tree.is_shown is False:
            self.tree_flag = 'normal'
            self.tree.is_shown = True
        else:
            self.tree_flag = 'hidden'
            self.tree.is_shown = False

        for e in self.tree.edges:
            self.canvas.itemconfig(e, state=f'{self.tree_flag}')

    def delete(self, event):
        '''Remove selected nodes, including parent references.'''
        ## TODO how does this behave if you delete a node with children?
        new_tree = []
        hologram = copy.deepcopy(self.tree)
        self.history.append(hologram) # save tree each time a node is to be deleted

        for n in self.tree.nodes:
            # first delete references to selected points in their parents
            for i in range(len(n.children)):
                if n.children[i].is_selected:
                    del n.children[i]

            # then remove the points themselves
            if n.is_selected:
                self.canvas.delete(n.shape_val)
            else:
                new_tree.append(n)
            
        self.tree.nodes = new_tree
        self.redraw()

class Node:
    '''An (x,y,0) point along a root.'''

    def __init__(self, coords, shape_val, canvas, tree):
        self.coords = coords  # (x,y) tuple
        self.relcoords = None  # (x,y) relative to root node
        self.shape_val = shape_val  # canvas object ID
        self.is_selected = False
        self.is_visited = False # for DFS; remember to clear it!
        self.depth = None # depth of node in the tree, relative to root
        self.children = []  ## WORKING ON THIS (TODO)
        self.is_PR = True  # primary root
        self.LR_index = None  # if lateral root, denote by index
        self.pedge = None # id of parent edge incident upon node
        self.pedge_color = "green"
        self.canvas = canvas # node's home canvas. careful with scopes and instances!
        self.tree = tree # node's home tree. ditto


############## TEST! must fix insertion logic for [children]

    def insert_child(self, obj): # when inserting is True
        # easy case (self has degree == 1): just insert
        if len(self.children) == 1:
            obj.children.append(self.children[0])  # new node becomes parent of old child
            del self.children[0]
            self.children.append(obj) # and becomes the new child

            if self.is_PR is False: # if inserting on an LR
                obj.is_PR = False

            # finally, shift everything downstream 1 level lower
            obj.children[0].depth += 1
            self.tree.DFS(obj.children[0])

        # hard case (self is a branching point with degree > 1): need more info
        # ask user to select the new child as well (sandwich)
        ### TODO

#########

    def add_child(self, obj): # when not inserting

        if len(self.children) == 0:
            if self.is_PR is False:  # if parent is an LR
                obj.is_PR = False
        else:
            obj.is_PR = False
        
        self.children.append(obj)


        # else: # if the selected node has 3 children, don't add the new node
        #     print("Error: all 3 children already assigned to point", self)
        #     w.delete(obj.shape_val)
## This is a problem! No return = oval deleted but node still added to tree!
# could break ternary assumptions! need to rectify

##################

    def select(self):
        self.is_selected = True
        self.canvas.itemconfig(self.shape_val, fill="red", outline="red", width=2)

    def deselect(self):
        self.is_selected = False
        self.canvas.itemconfig(self.shape_val, fill="white", outline="white", width=1)




class Tree:
    '''An acyclic, undirected, connected, hierarchical collection of nodes.'''
    def __init__(self):
        self.nodes = []
        self.edges = []
        self.day = 1  # track day of timeseries GIF
        self.plant = None  # ID of plant on plate (e.g. A-E, from left to right)
        self.is_shown = True # toggle display of edges
        self.top = None  # keep track of root node at top of tree


    def add_node(self, obj, inserting):
        hologram = copy.deepcopy(self) # save tree each time a node is to be added

        if self.nodes: # non-empty
            for n in self.nodes:
                if n.is_selected:
                    obj.depth = n.depth + 1  # child is one level lower
                    # since the first node will always be the root node,
                    # we calculate relcoords relative to it (nodes[0]):
                    obj.relcoords = ((obj.coords[0]-(self.nodes[0].coords[0])), (obj.coords[1]-(self.nodes[0].coords[1])))

                    if inserting is True:
                        n.insert_child(obj)
                        draw = (n, obj) # call draw_edge once back at the UI level in place_node()
                    else:
                        n.add_child(obj)

        
        else:  # if no nodes yet assigned
            obj.depth = 0
            obj.relcoords = (0, 0)
            self.top = obj

        # finally, add to tree (avoid self-assignment)
        self.nodes.append(obj)

        return hologram, draw


    def DFS(self, root):
        '''Walk tree depth-first and increment subtree depths +1. For insertion mode.'''
        root.is_visited = True
        for child in root.children:
            if child is not None and child.is_visited is False:
                child.depth += 1
                child.is_visited = True
                self.DFS(child)

        # reset is_visited flags when done!
        for node in self.nodes:
            node.is_visited = False

    def index_LRs(self, root):
        '''Walk tree breadth-first and assign indices to lateral roots.'''
        q = Queue()
        q.put(root)
        LR = 0

        while not q.empty():
            curr = q.get()
            # arbitrarily, we assign LR indices left-to-right (skipping the PR)
            # sort by x-coordinate
            children = sorted(curr.children, key=lambda x: x.relcoords[0])
            for n in children:
                n.LR_index = LR
                LR += 1
                q.put(n)

    def popup(self):
        '''Popup menu for plant ID assignment.'''
        top = tk.Toplevel()
        top.geometry('350x200')

        label = tk.Label(top, text="Please select a plant ID:")
        label.pack(side='top', fill='both', expand=True)
        
        v = tk.StringVar() # holds plant ID

        a = tk.Radiobutton(top, text='A', variable=v, value='A', bg='white', fg='black')
        a.pack()
        a.select() # default option for nicer aesthetics

        tk.Radiobutton(top, text='B', variable=v, value='B', bg='white', fg='black').pack()

        tk.Radiobutton(top, text='C', variable=v, value='C', bg='white', fg='black').pack()

        tk.Radiobutton(top, text='D', variable=v, value='D', bg='white', fg='black').pack()

        tk.Radiobutton(top, text='E', variable=v, value='E', bg='white', fg='black').pack()
        
        def updater():
            top.destroy()
            self.plant = v.get()

        ok = tk.Button(top, text='OK', command=updater)
        cancel = tk.Button(top, text='Cancel', command=top.destroy)

        ok.pack(side='top', fill='both', expand=True)
        cancel.pack(side='bottom', fill='both', expand=True)

        base.wait_window(top) # wait for a button to be pressed; check this still works ##


    def make_file(self, input_path):
        '''Output tree data to file.'''
        if self.plant is None: # get plant ID when called for the first time
            self.popup()
            if self.plant is None: # user didn't update ID (pressed cancel)
                return

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

        output_name = f"{source}_plant{self.plant}_day{self.day}.txt"
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

#### TODO make work with [children]; keep this order or do full BFS?


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






class AnalyzerUI(tk.Frame):
    '''Analysis mode interface.'''
    def __init__(self, base):
        super().__init__(base)
        self.base = base
        self.base.geometry('750x600')
        self.base.title('Ariadne: Analyze')

        # master frame
        self.frame = tk.Frame(self.base)
        self.frame.pack(side='top', fill='both', expand=True)

        # left-hand menu
        self.left_frame = tk.Frame(self.frame)
        self.left_frame.pack(side='left', fill='both', expand=True)

        self.load_button = tk.Button(self.left_frame, text='Load .txt file', command=self.import_txt)
        self.load_button.pack(side='top', fill='both', expand=True)

        # these buttons are hidden until later
        self.clear_button = tk.Button(self.left_frame, text='Clear', command=self.clear)
        self.analyze_button = tk.Button(self.left_frame, text='Generate report', command=self.generate_report)   
        self.save_button = tk.Button(self.left_frame, text='Save image', command=self.save_report)

        # right-hand output
        self.right_frame = tk.Frame(self.frame)
        self.right_frame.pack(side='right', fill='both', expand=True)

        self.output = tk.Label(self.right_frame, text=f'Results go here!')
        self.output.pack(side='top', fill='both', expand=True)

        # integrate functions from quantify.py

    def import_txt(self):
        '''Query user for an input file and load it into memory.'''
        self.path = askopenfilename(parent=self.base, initialdir='./', title='Select a .txt file:')
        self.results = quantify.make_graph(self.path)
        
        # listen for graph-creation errors and handle them if they arise
        # ...

        # spawn relevant buttons
        self.clear_button.pack(side='top', fill='both', expand=True)
        self.analyze_button.pack(side='top', fill='both', expand=True)

        # display output on right
        self.output.config(text=f'{self.results}')

    def generate_report(self):
        '''Compute RSA metrics and evaluate Pareto optimality.'''
        self.save_button.pack(side='top', fill='both', expand=True)

    def clear(self):
        '''Clean up a previously imported file.'''
        # take care of self.path, self.results, buttons, etc
        pass

    def save_report(self):
        '''Save an image of the Pareto plot.'''
        pass





if __name__ == "__main__":
    base = tk.Tk()
    base.title('Ariadne')
    StartupUI(base)
    base.mainloop()