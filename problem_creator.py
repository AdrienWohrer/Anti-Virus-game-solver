'''
Problem creator for the game Anti-Virus
'''

import time
from collections import OrderedDict
import random
random.seed()

import matplotlib.pyplot as plt

from antivirus_solver import Antivirus


##################################################
#
# Tile dictionary for position building
#
##################################################

# - Parametrized by (x,y) coordinates along directions (ne,nw).
# - Each tile is coded by its *relative* 2d coordinates from a "central spot" taken as (0,0).
# - Orientation will be modified a posteriori, by exchanging x and y coordinates, and/or adding a minus sign
# - Only some orientations are allowed (by game design and/or symmetry considerations)

tiles = { \
    "rouge" : [(0,0), (0,1)],
    "bleu" : [(0,0), (1,0)],
    "foret" : [(0,0), (1,1)],
    "rose" : [(0,0), (1,1)],
    "orange" : [(1,0), (0,0), (0,1)],
    "violet" : [(1,1), (0,0), (-1,1)],
    "pomme" : [(0,1), (0,0), (-1,-1)],
    "jaune" : [(0,1), (0,0), (1,-1)],
    "nuit" : [(1,1), (0,0), (-1,-1)],
}

allowed_orientations = { \
    "rouge" : [0],            # fixed oriretation
    "bleu" : [0],             # fixed orientation
    "foret" : [0,1],          # only two orientations
    "rose" : [0,1],           # only two orientations
    "nuit" : [0,1],           # only two orientations
    "orange" : [0,1,2,3],
    "violet" : [0,1,2,3],
    "pomme" : [0,1,2,3],
    "jaune" : [0,1,2,3],
}

def place_tile(name, orientation, location):
    '''
    Place a given tile (of key "name" in dict tiles) in a given orientation (0 to 3) at a given absolute location in "standard" indexing (0 to 25).
    Return the absolute tile location (in "standard" indexing) if it is within board bounds, else None.

    :param name: key of the tile
    :param orientation: which of 4 possible orientations for the tile (0 to 4)
    :param location: location of the tile's central spot
    :return: the resulting tile position (tuple) if it is valid ; else None
    '''

    # Tile 2d code
    tile_2d = tiles[name]
    # Rotate if required
    if orientation == 1:
        tile_2d = [ (tup[1],-tup[0]) for tup in tile_2d ]
    elif orientation == 2:
        tile_2d = [ (-tup[0],-tup[1]) for tup in tile_2d ]
    elif orientation == 3:
        tile_2d = [ (-tup[1],tup[0]) for tup in tile_2d ]
    # Place at required location
    offset_2d = Antivirus.loc2coord[location]
    tile = tuple( Antivirus.coord2loc.get( (tup[0]+offset_2d[0], tup[1]+offset_2d[1]) ) for tup in tile_2d )
    if any(i==None for i in tile):
        return None
    return tile

##print(place_tile("pomme", 3, 17))
##print(place_tile("pomme", 3, 18))


##################################################
#
# Problem creator
#
##################################################

def random_position(n_tiles_max = None):
    '''
    Return a randomly generated position.
    '''

    av = Antivirus()
    available_locations = list(range(26))
    
    # Random number of holes
    nholes = random.randint(0,2)
    holes = random.sample(range(2,26), k=nholes)
    av.set_holes(*holes)
    available_locations = [i for i in available_locations if i not in holes]
    
    # Order in which tiles will be tried. But always keep red tile in first position !
    shuffled_tiles = OrderedDict(random.sample(list(tiles.items()),len(tiles)))
    shuffled_tiles.move_to_end(av.tilekeys[0], last=False)
    
    #print(shuffled_tiles)

    # Tried orientations for each tile (given by its name)
    tried_orientations = allowed_orientations.copy()
    for name in tiles.keys():
        random.shuffle(tried_orientations[name])
    
    # Aaaand start placing tiles !

    init = {}
    for name in list(shuffled_tiles.keys())[:n_tiles_max]:
        tile = None
        for ori in tried_orientations[name]:
            for loc in random.sample(available_locations, len(available_locations)):
                tile = place_tile(name, ori, loc)
                if tile is not None:
                    init[name] = tile
                    av.set_initial_position(**init)
                    if av.check_initial_position() and av.solve():
                        # all good ! Keep this tile here, and move to the next name (=tile)
                        break
                    else:
                        # proposed tile leads to some form of invalidity or un-solvability
                        init.pop(name)
            else:
                continue    # https://stackoverflow.com/questions/189645/how-can-i-break-out-of-multiple-loops
            break
        
        # Remove the placed tile (if it exists) from available locations
        if tile is not None:
            available_locations = [i for i in available_locations if i not in tile]

    # For convenience : make sure av is set on the final problem and return it
    av.set_initial_position(**init)
    av.solve()
    
    return holes, init, av


######################################
### Launch ! (Can modify difficulty threshold on n_moves... but a higher threshold takes longer to be found !)

if __name__ == '__main__':
    # Running as a script

    ###################################
    n_tiles_max = 6                         # limit number of tiles on the board. (Warning: long solutions are harder to find with less tiles)
    required_n_moves = [40,1000]            # [lower_bound, upper_bound] on the difficulty threshold (number of moves for the optimal solution)
    ###################################

    # Experimentally-assessed boundary where using "reverse search" becomes useful
    # For values smaller than 30, average output time is faster without reverse_search
    try_reverse_search = (required_n_moves[0] >= 30)

    start = time.time()
    for _ in range(1):
        
        n_moves = 0
        while n_moves < required_n_moves[0] or n_moves > required_n_moves[1]:

            holes, init, av = random_position(n_tiles_max = n_tiles_max)
            n_moves = len(av.shortest_path())
            
            if n_moves < required_n_moves[0] and try_reverse_search:
                av.reset_fast(av.last_pos)          # obtained exit position becomes initial position
                av.solve(stopping_criterion=None)   # 'reverse' tree building from exit position
                av.reset_fast(av.last_pos)          # furthest away position found
                av.solve()
                n_moves = len(av.shortest_path())

        print(f"holes = {holes}")
        print(f"init = {init}")
        print(f"{n_moves} moves")
    
    print(f"Elapsed time: {time.time()-start}")  
    
    plt.ion()
    av.plot()

    input("Press a key to visualize the solution !")
    av.plot_solution(refresh_time=0.25)
    input("Done ! Press a key to close.")


### Some problems generated by the creator:

##holes = [18, 22]
##init = {'rouge': (14, 10), 'jaune': (15, 12, 5), 'pomme': (4, 7, 6), 'foret': (24, 17)}
## 36 moves ; 4 tiles ; JUNIOR

##holes = [4, 21]
##init = {'rouge': (23, 19), 'foret': (14, 7), 'rose': (17, 18), 'bleu': (9, 6), 'pomme': (13, 16, 15)}
## 33 moves ; 5 tiles ; JUNIOR/EXPERT

##holes = [22]
##init = {'rouge': (16, 12), 'bleu': (20, 17), 'pomme': (7, 10, 9), 'orange': (14, 18, 21), 'violet': (8, 1, 2)}
## 40 moves ; 5 tiles ; MASTER

##holes = [12, 14]
##init = {'rouge': (19, 15), 'jaune': (1, 5, 6), 'orange': (20, 16, 13), 'bleu': (24, 21)}
## 57 moves ; 4 tiles ; MASTER

##holes = []
##init = {'rouge': (5, 9), 'bleu': (13, 10), 'foret': (7, 6), 'jaune': (25, 21, 20), 'orange': (23, 19, 16), 'pomme': (0, 1, 8), 'rose': (4, 11)}
## 90 moves ; 7 tiles ;

##holes = [22, 25]
##init = {'rouge': (6, 10), 'orange': (16, 13, 17), 'bleu': (23, 20), 'jaune': (9, 12, 19), 'violet': (8, 1, 2)}
## 100 moves ; 5 tiles

##holes = []
##init = {'rouge': (17, 21), 'violet': (3, 10, 9), 'foret': (13, 14), 'jaune': (22, 19, 12), 'pomme': (0, 1, 8), 'bleu': (5, 2), 'rose': (23, 24)}
## 101 moves ; 7 tiles

