#!/bin/bash
for (( ; ; ))
do
   nice python fplan/extract/extracted_cache.py $1 $2 $3
   sleep 1800
done



