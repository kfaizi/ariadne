import csv
from pathlib import Path
import quantify

p = Path('/home/kian/Lab/output/')

def check_graph():
    with open('graph_results.csv', 'w', newline='') as sheet:
        fieldnames = ['file', 'is_intact', 'details']
        writer = csv.DictWriter(sheet, fieldnames=fieldnames)
        writer.writeheader()
        for i in p.iterdir():
            raw_result = quantify.make_graph(i)
            if raw_result == "Done!":
                intact = "y"
            else:
                intact = "n"
            writer.writerow({'file': f'{i.name}', 'is_intact': f'{intact}', 'details': f'{raw_result}'})

def file_renamer():
    p = Path('/home/kian/Lab/output/group1/')
    for i in p.iterdir():
        parts = i.stem.split("_")
        name = parts[2] + "_" + parts[3] + "_" + parts[4] + "_" + parts[0] + "_" + parts[1]

        prevpath = Path(i.stem).with_suffix('.txt')
        newpath = Path(name).with_suffix('.txt')
        
        prevpath.rename(newpath) # use with caution!

    