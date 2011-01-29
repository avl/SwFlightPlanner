#!/bin/bash
export PYTHONPATH=.
python fplan/lib/tilegen_planner.py /home/anders/saker/avl_fplan_world/tiles/plain/ &
sleep 2
nice -n20 python fplan/lib/tilegen_worker.py &
nice -n20 python fplan/lib/tilegen_worker.py &
nice -n20 python fplan/lib/tilegen_worker.py &
nice -n20 python fplan/lib/tilegen_worker.py &
wait
