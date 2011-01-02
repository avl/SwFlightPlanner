import fplan.lib.mapper as mapper
from pyshapemerge2d import Vertex,Line

def clampmerc(merc,tilesize):
    tilesizemask=tilesize-1
    x,y=merc
    x,y=int(x),int(y)
    x&=~tilesizemask
    y&=~tilesizemask
    return x,y

def fill(line,merc,zoomlevel,maxdist,tilesize,result=set()):
    if merc[0]<0 or merc[1]<0: return
    if merc in result: return
    dist=line.approx_dist(Vertex(merc[0]+tilesize/2,merc[1]+tilesize/2))
    if dist>maxdist: return
    #tile=blob.get_tile(*merc)
    print "zoomlevel:",zoomlevel,"merc:",merc,"dist:",dist,"maxdist:",maxdist    
    #result[merc]=tile
    result.add(merc)
    x,y=merc
    for cand in [
        (x-tilesize,y),
        (x+tilesize,y),
        (x,y-tilesize),
        (x,y+tilesize)]:
        fill(line,cand,zoomlevel,maxdist,tilesize,result)

def get_all_tiles_near(routes,zoomlevel,dist_nm,tilesize):
    resultset=set()
    for rt in routes:
        m1=mapper.latlon2merc(mapper.from_str(rt.a.pos),zoomlevel)
        m2=mapper.latlon2merc(mapper.from_str(rt.b.pos),zoomlevel)
        
        av=Vertex(int(m1[0]),int(m1[1]))
        bv=Vertex(int(m2[0]),int(m2[1]))
        l=Line(av,bv)
        startmerc=clampmerc(m1,tilesize)
        maxdist=mapper.approx_scale(startmerc,zoomlevel,dist_nm)
        maxdist+=3*tilesize/2
        fill(l,startmerc,zoomlevel=zoomlevel,maxdist=maxdist,tilesize=tilesize,result=resultset)
    return resultset

