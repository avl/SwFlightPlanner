import math
import fplan.lib.mapper as mapper
from pyshapemerge2d import Vertex,Line2
from fplan.lib.blobfile import BlobFile
from tiles_near_route import get_all_tiles_near
import StringIO
import Image
#http://localhost:5000/api/get_elev_near_trip?user=ank&password=ank&trip=Short


    
def heightmap_tiles_near(routes,dist_nm):
    tilesize=64
    zoomlevel=8

    tiles_on_levels=dict()

    tottiles=0
    while zoomlevel>=0:       
        path="/home/anders/saker/avl_fplan_world/tiles/elev/level%d"%(zoomlevel)
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

def map_tiles_near(routes,dist_nm):
    tilesize=256
    zoomlevel=7

    tiles_on_levels=dict()

    tottiles=0

    path="/home/anders/saker/avl_fplan_world/tiles/airspace/level%d"%(zoomlevel)
    blob=BlobFile(path,tilesize=tilesize)
    def cm(latlonstr,zoomlevel):
        return clampmerc(mapper.latlon2merc(mapper.from_str(latlonstr),zoomlevel))
            
    resultset=get_all_tiles_near(routes,zoomlevel,dist_nm,tilesize)
    result=dict()
    for merc in resultset:
        rawtile=blob.get_tile(*merc)
        io=StringIO.StringIO(rawtile)
        io.seek(0)
        im=Image.open(io)
        x,y=merc
        print "Map merc ",merc        
        x%=512
        y%=512
        if x>=256:
            im=im.transpose(Image.FLIP_LEFT_RIGHT)
            print "X-flipping"
        else:
            print "Not X-flipping"
        if y>=256:
            im=im.transpose(Image.FLIP_TOP_BOTTOM)
            print "Y-flippin'"
        else:
            print "Not Y-flippin'"
        buf=StringIO.StringIO()
        im.save(buf,"png")
        png=buf.getvalue()
        result[merc]=png
    tottiles+=len(result)
    tiles_on_levels[zoomlevel]=result

    return tiles_on_levels

        
