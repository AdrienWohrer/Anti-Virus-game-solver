'''
Solver for the game Anti-Virus
'''

import numpy as np
import matplotlib.pyplot as plt

##################################################
#
# Basic game encoding
#
##################################################

# Locations on the grid are indexed as follows :
#  0
#    1   2   3   4
#      5   6   7
#    8   9  10  11
#     12  13  14
#   15  16  17  18
#     19  20  21
#   22  23  24  25

# Any location outside of the grid is indexed by None

# Tiles are coded as tuples of locations, e.g.,
#   tile = (13,17) is the red tile located at position 13, 
#   tile = (5,9,12) is the orange tile located in position 9 and below, etc.

# Moves directions are indexed by 4 strings : "nw","ne","sw","se"

# A "game position" is a list of tiles. For example :
#   tile1 = (13,17) 
#   tile2 = (5,9,12)
#   tile3 = (1,2,3)
#   pos = [tile1, tile2, tile3]

# A tile within pos is represented by its index tix (first tile is tix=0, the second is tix=1, etc.)


class Antivirus():

    ##################################################
    #
    # Initialization structures and functions
    #
    ##################################################
    
    
    ### Initialization function
    
    def __init__(self):

        # List of tile keys. All tile-related dicts must use these keys.
        # First element is the key of the default target, that must escape the maze.
        
        self.tilekeys = ["rouge", "bleu", "orange", "rose", "foret", "nuit", "violet", "pomme", "jaune"]
        
        # Color associated to each of self.tilekeys (in order)
        self.tile_colors = ['xkcd:red', 'xkcd:blue', 'xkcd:orange', 'xkcd:pink', 'xkcd:emerald green',
                   'xkcd:royal blue', 'xkcd:bright purple', 'xkcd:lime green', 'xkcd:bright yellow']

        # Initial tile names and positions (key:position)
        self.initial_position = {}
        
        # Location of the holes
        self.holes = []
        
        # Resulting location of any of the 4 moves on positions 0...25 (before possible holes are defined)
        self.resulting_locs = { \
            "nw": [None,0,None,None,None,1,2,3,None,5,6,7,8,9,10,None,12,13,14,15,16,17,None,19,20,21],
            "ne": [None,None,None,None,None,2,3,4,5,6,7,None,9,10,11,12,13,14,None,16,17,18,19,20,21,None],
            "sw": [None,None,5,6,7,8,9,10,None,12,13,14,15,16,17,None,19,20,21,22,23,24,None,None,None,None],
            "se": [1,5,6,7,None,9,10,11,12,13,14,None,16,17,18,19,20,21,None,23,24,25,None,None,None,None]}
        
        # Tree that will store the solution to the current problem.  Stored elements are of the form (visited_position: father_info)
        self.visited_tree = {}
        
        # Last visited position during the tree building
        self.last_pos = None
    
        # Forced passage positions (just for fun ; not necessary)
        self.forced_passage = None

        
    ### Set a "hole" at each given location (this is irreversible for this Antivirus instance)

    def set_holes(self, *locations):
        self.holes.extend(locations)
        for hole in locations:
            for move in self.resulting_locs.keys():
                self.resulting_locs[move] = [None if i==hole else i for i in self.resulting_locs[move]]


    ### Set an initial position for the tiles (without full error checking)
    
    def set_initial_position(self, **kwargs):
        '''
        Set an initial position for the tiles, in the form of a list of keyword arguments
            tilename = (3,1,5)
        where tilename is the chosen name for the tile, and the tuple denotes the board locations taken by the tile.
        '''

        # (only checking done here has to do with the used tile keys)
        for key in kwargs.keys():
            if key not in self.tilekeys:
                raise ValueError(f"key '{key}' is not a valid tile key.\nValid tile keys are : {self.tilekeys}")
        self.initial_position = kwargs
    
    
    ### Alternative "2d" parametrization
    
    # For some tasks (position building, game display), another encoding of tile positions is more convenient :
    # - each location is parametrized by (x,y) coordinates along directions (ne,nw)
    # - the central location (13) is taken as the origin (0,0)
    #
    # The link between the two encodings ("standard" tile index vs. "2d" tile coordinates) is realized by the two structures:
    # - Antivirus.loc2coord[i] returns the 2d coordinates of location i
    # - Antivirus.coord2loc[(x,y)] returns the standard location of coordinates (x,y)

    loc2coord = [(0,4)]
    for s in range(3,-4,-1):
        for x in range(-3,4):
            if 2*x-s >= -3 and 2*x-s <=3:
                loc2coord.append((x,s-x))
    
    coord2loc = {}
    for loc,coord in enumerate(loc2coord):
        coord2loc[coord] = loc
    
    #print(loc2coord)
    #print(coord2loc)  

    
    ##################################################
    #
    # Various validity checks
    #
    ##################################################


    ### Basic validity checking for a single tile

    def check_tile(self, tile):
        return not (tile is None or any(i is None or i in self.holes for i in tile))
    
        
    ### Detect overlaps within a position

    @staticmethod
    def check_overlaps(pos, ref_tix):
        '''Return the list of tile indices in position 'pos' that overlap with the tile of index 'ref_tix' '''
        
        ref_tile = pos[ref_tix]
        overlapping_tiles = []
        for tix,tile in enumerate(pos):
            if tix != ref_tix and any(j==i for i in ref_tile for j in tile):
                overlapping_tiles.append(tix)
        return overlapping_tiles


    ### Overall checking for the defined holes and initial position

    def check_initial_position(self):
        '''Return True if the defined initial position is valid (even if not necessarily solvable), False otherwise (tiles out of bounds, on holes, or overlapping)'''

        pos = list(self.initial_position.values())
        for tix,tile in enumerate(pos):
            if not self.check_tile(tile):
                return False
            if len(self.check_overlaps(pos,tix))>0:
                return False
        return True


    ##################################################
    #
    # Tile moving function
    #
    ##################################################


    def change_pos(self, pos, tix, move):
        '''
        Starting from some game position 'pos', move the tile given by index 'tix' in direction 'move'. 
        If necessary, automatically propagate the move to tiles in the same "block" as the tile, to make this a "block move".
        If the resulting position is valid, return it. Else, return None.
        
        :param pos: game position before move
        :param tix: index of the moved tile
        :param move: move direction
        :return:
            - The updated position if it is valid ; else None
            - The block size (number of tiles involved in the move)
        '''

        pos = pos.copy()
        res_locs = self.resulting_locs[move]    # Location changes for this move
        to_move = [tix]                         # List of tiles to move (will be expanded in case of a 'block move')
        block_size = 0
        while len(to_move) > 0:
            tix = to_move.pop(0)
            block_size += 1
            # Move tile tix
            pos[tix] = tuple(res_locs[i] for i in pos[tix])
            # Check for tile stepping out of grid
            if any(i is None for i in pos[tix]):
                return None, 1
            # Propagate move to overlapping tiles ("block move") (TODO: could be optimized by progressively reducing the list of remaining tiles to check)
            to_move.extend(self.check_overlaps(pos,tix))
        return pos, block_size


    ##################################################
    #
    # Solver (breadth-first tree search)
    #
    ##################################################


    ### Tree building function, from a given starting position.
    ### Note : stopping_criterion can be customized to perform other types of searches.

    def solve(self, stopping_criterion = "default", distance_max=None, penalize_blocks=True):
        '''
        Starting from initial position, explore all tile moves until stopping criterion is met (or distance_max is reached).

        :param stopping_criterion: "default" is the classic escape rule of Anti-Virus game. Alternatively, provide a function such that stopping_criterion(pos)=True when position pos (list of tiles) meets the stopping criterion.

        :param distance_max: optionally, return before stopping_criterion is met, when all positions at a distance <= distance_max have been explored.
        
        :param penalize_blocks: if True, penalize block moves by assigning them as many moves as there are tiles involved in the block (this is slightly faster, for some reason!?).
        
        :return: True/False, whether a solution has been found or not.
        '''
        
        father_info = ("start",0,"start")                   # Surrogate "father information" for start_pos
        start_pos = list(self.initial_position.values())
        to_explore = [(start_pos, 1, father_info, 0)]       # Queue (First In First Out) of positions to explore. Last number is the distance from start_pos.
        self.visited_tree = {}                              # Re-initialize tree and last_pos
        self.last_pos = None
      
        if stopping_criterion == "default":
            # Default stopping criterion : when default target tile has reached location 0
            try:
                target_tix = list(self.initial_position.keys()).index(self.tilekeys[0])
            except ValueError:
                raise ValueError(f"Initial position does not define the default target tile : '{self.tilekeys[0]}'")
            stopping_criterion = lambda pos: any(i == 0 for i in pos[target_tix])    

        while len(to_explore)>0:

            pos, waiting_time, father_info, distance = to_explore.pop(0)

            if distance_max and distance > distance_max:
                return False
            
            if penalize_blocks and waiting_time > 1:
                # if penalize_blocks, a block of size N counts for an "equivalent distance" of N tiles
                # thus, reinsert position 'pos' at the end of the queue, with one less waiting time
                to_explore.append((pos, waiting_time-1, father_info, distance+1))
                continue

            if self.visited_tree.get(tuple(pos)) is not None:
                # pos has already been reached from another path : just drop this occurence
                continue
            
            # Treat position pos
            self.visited_tree[tuple(pos)] = father_info
            self.last_pos = pos
            if stopping_criterion and stopping_criterion(pos):
                return True

            # Previous tile moved : always try to move it first, to promote successive movements of the same tile
            prev_tix = father_info[1]
            for tix in [prev_tix]+list(range(prev_tix))+list(range(prev_tix+1,len(pos))):
                for move in ["nw","ne","sw","se"]:
                    new_pos, block_size = self.change_pos(pos, tix, move)
                    if new_pos is not None:
                        if self.visited_tree.get(tuple(new_pos)) is None:
                            # Found a new valid position
                            to_explore.append( (new_pos, block_size, (pos, tix, move), distance+1) )

        return False    # (parsed the whole graph of attainable positions without reaching solution)


    ### Return the shortest path to the solution

    def shortest_path(self):
        path = []
        pos, tix, move = self.last_pos, None, None
        assert pos is not None, "No search tree built yet. Call function solve() first."
        
        while pos != "start":
            path.insert(0, (pos, tix, move))
            pos, tix, move = self.visited_tree[tuple(pos)]
        return path
    
    
    ### Print the shortest path solution in a readable format

    def print_solution(self):
        path = self.shortest_path()
        names = list(self.initial_position.keys())
        for s in path[:-1]:
            print(f"{names[s[1]]} : {s[2]}")
        print(f"Nombre d'étapes: {len(path)}")

    ##################################################

        
    ### Just for fun ! Target 'forced passage' positions in the solution
    ### We compute these forced passage points thanks to the depth-first Hopcroft-Tarjan algorithm for articulation points

    def compute_forced_passage_positions(self):

        pos = self.last_pos
        assert pos is not None, "No search tree built yet. Call function solve() first."

        articulation_points, df_tree = self.hopcroft_tarjan()

        self.forced_passage = []
        while pos != None:
            if articulation_points.get(tuple(pos)) is True:
                self.forced_passage.insert(0, tuple(pos))
            pos = df_tree[tuple(pos)][0]


     ### https://en.wikipedia.org/wiki/Biconnected_component
     
    def hopcroft_tarjan(self):

        start = time.time()        
        start_pos = list(self.initial_position.values())
        to_explore = [start_pos]                             # Stack (Last In First Out) of positions to explore.
        tree = {tuple(start_pos): [None,None,0,0,None]}      # Store [parent, other_neighbors, depth, lowpoint] for each position
        articulation_points = {}
        
        while len(to_explore)>0:

            pos = to_explore[-1]
            info = tree[tuple(pos)]
            father = info[0]
            
            # First visit of pos: compute neighbors
            if info[1] is None:
                neighbors = []
                for tix in range(len(pos)):
                    for move in ["nw","ne","sw","se"]:
                        new_pos, _ = self.change_pos(pos, tix, move)
                        if new_pos is not None and (father is None or tuple(father) != tuple(new_pos)):
                            neighbors.append(new_pos)
                info[1] = neighbors
            else:
                neighbors = info[1]

            # Append neighbors to the stack
            for n_pos in neighbors:
                n_info = tree.get(tuple(n_pos))
                if n_info is None:
                    to_explore.append( n_pos )
                    tree[tuple(n_pos)] = [pos, None, info[2]+1, info[2]+1]      # info[2] = depth
                    break  # --> explore n_pos
                else:
                    # already known neighbor... update lowpoint
                    info[3] = min(info[3], n_info[2], n_info[3])                # info[3] = lowpoint
                    if tuple(pos) != tuple(start_pos) and info[2] <= n_info[3]:
                        articulation_points[tuple(pos)] = True
            else:
                # no break --> all neighbors have been explored --> pos can be popped out
                to_explore.pop()

        return articulation_points, tree
    
    
    ##################################################
    #
    # Visualization functions
    #
    ##################################################


    ### Rotation matrix for viewing

    Mview = np.array([[1,1],[-1,1]]) / np.sqrt(2)

    ### Draw a circle (not filled)

    @staticmethod
    def draw_circle(center, r, **kwargs):
        t = np.arange(0, np.pi * 2.0, 0.01)
        plt.plot(center[0] + r * np.cos(t), center[1] + r * np.sin(t) , **kwargs)

    ## Draw a tile

    @staticmethod
    def draw_tile(tile, color):
        tile = np.array([Antivirus.loc2coord[i] for i in tile]) @ Antivirus.Mview
        for i in range(tile.shape[0]):
            plt.gca().add_patch(plt.Circle(tile[i], .4, color=color))
        plt.plot(tile[:,0],tile[:,1], linewidth=20, color=color)


    ### Plot a position
        
    def plot(self, pos=None):
        '''
        Plot the currently defined Antivirus object.
        If pos=None, use the initial position.
        If pos is precised, as a list of tiles, plot the positions given by the tiles.
        '''
        
        if pos is None:
            pos = list(self.initial_position.values())
        
        # Background colors
        plt.gcf().patch.set_facecolor([.9,.9,.9])
        plt.gca().patch.set_facecolor([.9,.9,.9])

        # Draw locations (and holes)
        for loc,tup in enumerate(self.loc2coord):
            center = np.array(tup) @ self.Mview
            if loc in self.holes:
                plt.gca().add_patch(plt.Circle(center, .4, color='k'))
            else:
                self.draw_circle(center, .3, color='k')
            
        # Retrieve color for the tiles (a bit convoluted!)
        colors = [ self.tile_colors[self.tilekeys.index(key)] for key in self.initial_position.keys() ]

        # Draw tiles
        for tix in range(len(pos)):
            self.draw_tile(pos[tix], colors[tix])
        
        # Aspect ratio
        plt.axis('square')
        plt.axis('off')


    ### Plot the shortest path solution

    def plot_solution(self, refresh_time=None):  
        '''
        Graphical plot of the solution.
        - Step-by-step if `refresh_time`=None)
        - Else, plot a move every `refresh_time` seconds.
        '''
        for i,pos in enumerate(self.shortest_path()):
            plt.clf()
            self.plot(pos[0])
            if refresh_time is None:
                if self.forced_passage and tuple(pos[0]) in self.forced_passage:
                    input(f"move {i} (* forced passage)")
                    input()
                else:
                    input(f"move {i}")
            else:
                plt.pause(refresh_time)
    
    
##################################################
#
# Testing
#
##################################################

if __name__ == '__main__':
    # Running as a script

    import time

##    ## 'Junior' problem from the Smartgames online playing website
##    holes = [10]
##    init = {'rouge': (17,21), 'orange': (12,16,13), 'pomme': (8,15,19), 'nuit': (25,18,11)}

##    ## Problem 58 from the booklet
##    holes = [2]
##    init = {'rouge': (17,21), 'bleu': (3,6), 'foret': (10,11), 'violet': (16,23,22), 'pomme': (0,1,8), 'jaune': (9,12,19)}
    
    ## Problem 60 from the booklet
    holes = [4]
    init = {'rouge': (20,24), 'bleu': (11,14), 'foret': (5,12), 'violet': (2,1,8), 'pomme': (17,16,19), 'rose': (15,22)}
    
##    ## Random hard problem created with position_creator.py
##    holes = []
##    init = {'rouge': (5, 9), 'bleu': (13, 10), 'foret': (7, 6), 'jaune': (20, 21, 25), 'orange': (16, 19, 23), 'pomme': (0, 1, 8), 'rose': (4, 11)}
    
##    ## Coco's problem
##    holes = []
##    init = {'rouge': (25,21), 'bleu': (16,19), 'foret': (17,24), 'rose': (15,22), 'orange': (10,7,11), 'pomme': (6,3,4), 'jaune': (0,1,2)}
    
##    ## Coco's problem
##    holes = []
##    init = {'rouge': (10,14), 'bleu': (5,8), 'foret': (11,18), 'rose': (12,13), 'violet': (23,16,17), 'jaune': (2,3,7)}

    ################
    
    av = Antivirus()
    av.set_holes(*holes)
    av.set_initial_position(**init)

    plt.ion()
    av.plot()                                   # plot initial position
    refresh_time = 0.25                         # refresh time of the animated solution (in seconds)
    
    start = time.time()
    found = av.solve(penalize_blocks=True)      # solve the position
    solvetime = time.time()-start
    
    if found:
        av.print_solution()        
        print(f"Solving time: {solvetime}")

        if True:
            print("Computing forced passage positions in the solution. (Feel free to comment this part!)")
            start = time.time()
            av.compute_forced_passage_positions()
            print(f"Done in time: {time.time()-start}")
            refresh_time = None

        input("Press a key to visualize the solution !")
        plt.figure()
        av.plot_solution(refresh_time=refresh_time)
        input("Done ! Press a key to close.")
    else:
        print("No solution !")

    
