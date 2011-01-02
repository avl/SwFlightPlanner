#!/bin/bash

python fplan/lib/create_merc_elevmap.py create $SWFP_DATADIR/tiles/elev/level
python fplan/lib/create_merc_elevmap.py refine $SWFP_DATADIR/tiles/elev/level

