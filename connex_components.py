'''
Given a set of tiles and orientations, count the number of connex components for their positions (two positions are in the same component if one can move from one to the other).
'''

import matplotlib.pyplot as plt

from antivirus_solver import Antivirus
from problem_creator import place_tile

##################################

# tiles + orientations + holes used.
# The goal is to count the number of connex components for positioning these tiles.

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

### Dictionary giving the component of all visited positions

connex_component = {}
n_compo = [0]       # should be a list to be accessible from within function rec_for

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
            if connex_component.get(tuple(pos)) is None:
                # position has not been encountered yet (new connex component). Explore its connex component:
                av.solve(stopping_criterion = None)
                # Mark all reached positions, with the same class number
                connex_component.update((tuple(pos), n_compo[0]) for pos in av.visited_tree.keys())
                n_compo[0] += 1

rec_for(0)
print(f"Found {n_compo[0]} connex components of positions for this choice of tiles.")

### Computing size of various equivalence classes
class_sizes = [None] * n_compo[0]

for nc in range(n_compo[0]):
    class_sizes[nc] = len([ n for n in connex_component.values() if n==nc ])
##    print(f"Class {nc} : {class_sizes[nc]} positions")

sortids = sorted(range(n_compo[0]), key=lambda k: class_sizes[k], reverse=True)

print("Showing two representants of each component, starting with the larger components.")
print("Figure 1 : reference position for this component.")
print("Figure 2 : furthest away position in the same component.")

plt.ion()
for nc in sortids:
    
    print(f"Component {nc} : {class_sizes[nc]} positions.")

    plt.figure(1)
    plt.clf()
    pos = list(connex_component.keys()) [ list(connex_component.values()).index(nc) ]
    av.plot(pos)
    
    # Look for furthest aways position in the same class
    plt.figure(2)
    plt.clf()
    av.set_initial_position(**dict(zip(tiles,pos)))
    av.solve(stopping_criterion=None)
    print(f"Fig 1 -> Fig 2 = {len(av.shortest_path())} moves.")
    av.plot(av.last_pos)
    
    input("Press Enter.")        
