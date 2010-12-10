import math
import fplan.lib.mapper as mapper
from pyshapemerge2d import Vertex,Line2
from fplan.lib.blobfile import BlobFile
from tiles_near_route import get_all_tiles_near
#http://localhost:5000/api/get_elev_near_trip?user=ank&password=ank&trip=Short


    
def heightmap_tiles_near(routes,dist_nm):
    tilesize=64
    zoomlevel=8

    tiles_on_levels=dict()

    tottiles=0
    while zoomlevel>=0:       
        path=os.path.join(os.getenv("SWFP_DATADIR"),"tiles/elev/level%d"%(zoomlevel))
        blob=BlobFile(path,tilesize=tilesize)
        def cm(latlonstr,zoomlevel):
            return clampmerc(mapper.latlon2merc(mapper.from_str(latlonstr),zoomlevel))
                
        resultset=get_all_tiles_near(routes,zoomlevel,dist_nm,tilesize)
        result=dict()
        for merc in resultset:
            result[merc]=blob.get_tile(*merc)
        tottiles+=len(result)
        tiles_on_levels[zoomlevel]=result
        
        zoomlevel-=1


    return tiles_on_levels

        
