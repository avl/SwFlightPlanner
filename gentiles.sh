#!/bin/bash
export PYTHONPATH=.
python fplan/lib/tilegen_planner.py fplan/public/tiles/ &
sleep 2
nice -n20 python fplan/lib/tilegen_worker.py &
nice -n20 python fplan/lib/tilegen_worker.py &
nice -n20 python fplan/lib/tilegen_worker.py &
nice -n20 python fplan/lib/tilegen_worker.py &
wait
