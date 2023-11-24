# Anti-Virus-game-solver
Solver for the [Anti-Virus®](https://www.smartgames.eu/uk/one-player-games/anti-virus) game by SmartGames®.

* antivirus_solver.py contains the main class, allowing to define and solve an instance of Anti-Virus® game.

* problem_creator.py is a script to generate random problems for the Anti-Virus® game.

* equivalence_classes.py is a script to count equivalence classes given a set of tiles and orientations.

Each of these three files can be executed as a script. For example, under linux, type in the command line

    python3 problem_creator.py

Modify the scripts in their "Testing" section (near the bottom) to define a new position to solve, modify the parameters of the problem creator, etc.

Note that this is *not* an interface to play Anti-Virus®. There is no GUI allowing a user to move the tiles. Its display capabilities are limited to showing an initial position, and displaying the found solution.

This code is dedicated to Coco :)
