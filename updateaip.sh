#!/bin/bash
nice python fplan/extract/extracted_cache.py $1 $2
for (( ; ; ))
do
   ionice -c Idle nice python fplan/extract/extracted_cache.py
   sleep 7200
done



