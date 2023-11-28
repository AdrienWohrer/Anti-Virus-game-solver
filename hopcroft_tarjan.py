
### https://en.wikipedia.org/wiki/Biconnected_component

def hopcroft_tarjan(start_pos, find_neighbors):
    '''
        Depth-first Hopcroft-Tarjan algorithm for biconnected components.

        @param find_neighbors: function defining the underlying graph, i.e., such that
                L = find_neighbors(pos)
        gives the list of neighbors of vertex `pos`
     '''
    
    ### First pass :
    # - build Depth-First search tree
    # - compute low point

    # We use a "fake" tree root `None` that has a single edge to start_pos
    # (allowing to treat `start_pos` as a regular vertex in the search)
    
    to_explore = [None]                         # Stack (Last In First Out) of positions to explore.
    tree = {None: [None,None,None,-1,None]}     # Store [father, children, other_neighbors, depth, lowpoint] for each position
    articulation_points = {}
    
    while len(to_explore)>0:

        pos = to_explore[-1]
        info = tree[pos]
        father = info[0]
        
        # First visit of pos: compute neighbors
        if info[1] is None:
            info[1] = []                                                    # future list of children in the tree
            if pos is None: # (fake root)
                info[2] = [start_pos]
            else:
                info[2] = [i for i in find_neighbors(pos) if i!=father]     # list of neighbors in the graph (remove father)

        children, neighbors, depth = info[1], info[2], info[3]

        # Append neighbors to the stack
        
        for n_pos in neighbors:
            n_info = tree.get(n_pos)
            if n_info is None:
                to_explore.append(n_pos)
                children.append(n_pos)
                neighbors.remove(n_pos)                                 # (neighbors will only retain non-father, non-children neighbors)
                tree[n_pos] = [pos, None, None, depth+1, None]
                break  # --> explore n_pos

        else:
            # no break --> all neighbors have already been explored. Finish treatment of `pos' before popping out

            # Compute lowpoint...
            lowpoint = min(depth, depth, *[tree[n_pos][3] for n_pos in neighbors])
            for n_pos in children:
                _, _, _, n_depth, n_lowpoint = tree[n_pos]
                lowpoint = min(lowpoint, n_lowpoint)

                # Detect articulation points...
                if depth <= n_lowpoint :
                    # `pos' is an articulation point, and (pos, n_pos) is an articulation edge
                    if articulation_points.get(pos) is None:
                        articulation_points[pos] = []
                    articulation_points[pos].append(n_pos)
            info[4] = lowpoint
            # Pop out `pos'
            to_explore.pop()

    # Remove fake tree root
##    del articulation_points[None], tree[None]
##    articulation_points[start_pos].remove(find_neighbors(start_pos)[0]) # (ugly :()
    
    ### Second pass : compute biconnected components
    # (we re-parse the tree in a breadth-first way, a bit easier to code)

    components = {}

    components_to_explore = [(None, -2)]
    N_comp = -2
    # -2 = fake_root ; -1 = (fake_root <-> start_pos) ; 0 and onwards = true components

    while len(components_to_explore) > 0 :

        comp_start, comp_id = components_to_explore.pop()
        components[comp_start] = [comp_id]
        to_visit = [comp_start]
    
        while len(to_visit) > 0:

            pos = to_visit.pop()
            children = tree[pos][1]
            
            for n_pos in children:
                if n_pos in articulation_points.get(pos,[]):
                    # launch a new component ! (Will be visited later)
                    N_comp += 1
                    components[pos].append(N_comp)
                    components_to_explore.append((n_pos, N_comp))
                else:
                    # neighbor belongs to same component as current_comp
                    components[n_pos] = [comp_id]
                    to_visit.append(n_pos)
    

    ### Second pass : old version

##    to_visit = [None]
##    revisited = {None: True}
##    components = {None: [-2]}   # -2 = fakeroot ; -1 = (fakeroot <-> start_pos) ; 0 and onwards = true components
##    N_comp = -2
##    current_comp = -2
##    
##    while len(to_visit)>0:
##
##        pos = to_visit[-1]
##        father, children, _, _, _ = tree[pos]
##
##        for n_pos in children:
##            if revisited.get(n_pos) is None:
##                if n_pos in articulation_points.get(pos,[]):
##                    # launch a new component !
##                    N_comp += 1
##                    current_comp = N_comp
##                    components[pos].append(N_comp)
##                    components[n_pos] = [N_comp]
##                else:
##                    # neighbor belongs to same component as current_comp
##                    components[n_pos] = [current_comp]
##                # Go visit n_pos !
##                revisited[n_pos] = True
##                to_visit.append(n_pos)
##                break  # --> go visit n_pos
##        else:
##            # no break --> all neighbors have already been explored. Finish treatment of `pos' before popping out
##            if father is not None:
##                current_comp = components[father][-1]       # back to father's currently treated component
##            to_visit.pop()

    # Remove 'fake root' information
    del components[None], tree[None]
    components[start_pos].remove(-1)
    
    return components, tree


###########################################
##### TEST / RUN !
###########################################

if __name__ == "__main__":
    
    # Graph from https://en.wikipedia.org/wiki/Biconnected_component (nodes left to right):
    graph = { \
        0: [1,2],
        1: [0,3],
        2: [0,3],
        3: [1,2,4],
        4: [3,5],
        5: [4,6],
        6: [7,11,13],
        7: [6,8,9],
        8: [7,9],
        9: [7,8,10],
        10: [9,11],
        11: [6,10,12],
        12: [11],
        13: [6],
        }

    def graph_neighbors(pos):
        return graph[pos]

    components, tree = hopcroft_tarjan(0, graph_neighbors)
    print(components)

    ### Other graphs
##
##    import networkx as nx
##    import matplotlib.pyplot as plt
##    plt.ion()
##    
####    g = nx.graph_atlas(996)
##    g = nx.watts_strogatz_graph(30, 2, .8)
##    
##    nx.draw(g, with_labels=True, font_weight='bold')
##    
##    components, _, _ = hopcroft_tarjan(0, g.neighbors)
##    print(components)
##    input()
    
