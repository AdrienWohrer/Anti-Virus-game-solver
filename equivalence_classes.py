'''
Given a set of tiles and orientations, count the number of equivalence classes for their positions (two positions being 'equivalent' if one can move from one to the other).
'''

import matplotlib.pyplot as plt

from antivirus_solver import Antivirus
from problem_creator import place_tile

##################################

# tiles + orientations + holes used.
# The goal is to count the number of equivalence classes for positioning these tiles.

tiles = ["rouge", "bleu", "nuit", "orange", "pomme"]
##tiles = ["rouge", "bleu", "orange", "pomme"]
##orientations = [0,0,1,0] #, 0, 0, 0, 0]
orientations = [0,0,1,0,1]
holes = []
n_tiles = len(tiles)

##################################

available_locations = [i for i in range(26) if i not in holes]

av = Antivirus()
av.set_holes(holes)

### Dictionary giving the class of all visited positions

equiv_class = {}
n_class = [0]       # should be a list to be accessible from within function rec_for

### Recursive function to try ALL possible positions of the tiles

init = {}
def rec_for(k):
    
    if k < n_tiles:
        # place tile number k
        name = tiles[k]
        for loc_k in available_locations:
            tile  = place_tile(name, orientations[k], loc_k)
            if tile is None:
                continue
            init[name] = tile
            rec_for(k+1)
    else:
        # placed all of n_tiles on the board (possibly with overlaps)
        av.set_initial_position(**init)
        if av.check_initial_position():
            # starting position is valid
            pos = list(init.values())
            if equiv_class.get(tuple(pos)) is None:
                # position has not been encountered yet (new equivalence class). Explore its equivalence class:
                av.solve(stopping_criterion = None)
                # Mark all reached positions, with the same class number
                equiv_class.update((tuple(pos), n_class[0]) for pos in av.visited_tree.keys())
                n_class[0] += 1

rec_for(0)
print(f"Found {n_class[0]} equivalence classes of positions for this choice of tiles.")

### Computing size of various equivalence classes
class_sizes = [None] * n_class[0]

for nc in range(n_class[0]):
    class_sizes[nc] = len([ n for n in equiv_class.values() if n==nc ])
##    print(f"Class {nc} : {class_sizes[nc]} positions")

sortids = sorted(range(n_class[0]), key=lambda k: class_sizes[k], reverse=True)

print("Showing two representants of each class, starting with the larger classes.")
print("Figure 1 : reference position for this class.")
print("Figure 2 : furthest away position in the same class.")

plt.ion()
for nc in sortids:
    
    print(f"Class {nc} : {class_sizes[nc]} positions.")

    plt.figure(1)
    plt.clf()
    pos = list(equiv_class.keys()) [ list(equiv_class.values()).index(nc) ]
    av.plot(pos)
    
    # Look for furthest aways position in the same class
    plt.figure(2)
    plt.clf()
    av.set_initial_position(**dict(zip(tiles,pos)))
    av.solve(stopping_criterion=None)
    print(f"Fig 1 -> Fig 2 = {len(av.shortest_path())} moves.")
    av.plot(av.last_pos)
    
    input("Press Enter.")        
