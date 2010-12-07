#!/bin/bash

python fplan/lib/create_merc_elevmap.py create /home/anders/saker/avl_fplan_world/tiles/elev/level
python fplan/lib/create_merc_elevmap.py refine /home/anders/saker/avl_fplan_world/tiles/elev/level

