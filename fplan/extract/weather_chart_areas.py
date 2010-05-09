
import coord2latlon

cache=None
def get_areas():
    global cache
    if cache==None:
        files=["llf_middle","llf_southern","llf_northern"]
        cache=dict()
        for filename in files:
            areas=coord2latlon.run(os.path.join("fplan/extract/",filename))
            for areaname,geo_points in areas.items():
                cache[areaname]=geo_points
    return cache
