#!/bin/bash
nice python fplan/extract/extracted_cache.py force
for (( ; ; ))
do
   nice python fplan/extract/extracted_cache.py
   sleep 7200
done



