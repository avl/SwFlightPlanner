import math
import fplan.lib.mapper as mapper
from pyshapemerge2d import Vertex,Line2
from fplan.lib.blobfile import BlobFile
#http://localhost:5000/api/get_elev_near_trip?user=ank&password=ank&trip=Short

tilesize=64
tilesizemask=tilesize-1
def clampmerc(merc):
    x,y=merc
    x,y=int(x),int(y)
    x&=~tilesizemask
    y&=~tilesizemask
    return x,y

def fill(blob,line,merc,zoomlevel,maxdist,result=dict()):
    if merc[0]<0 or merc[1]<0: return
    if merc in result: return
    dist=line.approx_dist(Vertex(merc[0]+tilesize/2,merc[1]+tilesize/2))
    print "zoomlevel:",zoomlevel,"merc:",merc,"dist:",dist,"maxdist:",maxdist
    if dist>maxdist: return
    tile=blob.get_tile(*merc)
    result[merc]=tile
    x,y=merc
    for cand in [
        (x-tilesize,y),
        (x+tilesize,y),
        (x,y-tilesize),
        (x,y+tilesize)]:
        fill(blob,line,cand,zoomlevel,maxdist,result)

    
def heightmap_tiles_near(routes,dist_nm):
    zoomlevel=8
    factor=1
    tiles_on_levels=dict()
    print "routes:",len(routes)
    tottiles=0
    while zoomlevel>=5:       
        path="/home/anders/saker/avl_fplan_world/tiles/elev/level%d"%(zoomlevel)
        blob=BlobFile(path,tilesize=tilesize)
        def cm(latlonstr,zoomlevel):
            return clampmerc(mapper.latlon2merc(mapper.from_str(latlonstr),zoomlevel))
                
        result=dict()
        for rt in routes:
            #print "a",rt.a.pos
            #print "b",rt.a.pos
            
            m1=mapper.latlon2merc(mapper.from_str(rt.a.pos),zoomlevel)
            m2=mapper.latlon2merc(mapper.from_str(rt.b.pos),zoomlevel)
            
            av=Vertex(int(m1[0]),int(m1[1]))
            bv=Vertex(int(m2[0]),int(m2[1]))
            l=Line2(av,bv)
            print "Line: %s -> %s"%(m1,m2)
            print "Rt: ",rt.a.waypoint,rt.b.waypoint
            startmerc=clampmerc(m1)
            maxdist=mapper.approx_scale(startmerc,zoomlevel,dist_nm)
            #maxdist=32
            maxdist+=3*tilesize/2
            fill(blob,l,startmerc,zoomlevel=zoomlevel,maxdist=maxdist,result=result)
        tottiles+=len(result)
        tiles_on_levels[zoomlevel]=result
        
        zoomlevel-=1
        factor*=2
    print "Total tile count",tottiles
    return tiles_on_levels

        
