#!/bin/bash
nice python fplan/extract/extracted_cache.py $1 $2
for (( ; ; ))
do
   nice python fplan/extract/extracted_cache.py
   nice python ./download_weather.py
   
   sleep 3600
done



