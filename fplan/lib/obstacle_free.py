from pyshapemerge2d import Vector,Line,Vertex
from fplan.lib.get_terrain_elev import get_terrain_elev_in_box_approx
import fplan.extract.extracted_cache as extracted_cache
import fplan.lib.mapper as mapper
from fplan.lib.bsptree import BoundingBox
from itertools import chain
import fplan.lib.notam_geo_search as notam_geo_search

def get_obstacle_free_height_on_line(pos1,pos2):
    
    minimum_distance=2.0
    
    merc1=mapper.latlon2merc(pos1,13)
    merc2=mapper.latlon2merc(pos2,13)
    
    onenm=mapper.approx_scale(merc1,13,1.0)
    av=Vertex(int(merc1[0]),int(merc1[1]))
    bv=Vertex(int(merc2[0]),int(merc2[1]))
    linelen=(av-bv).approxlength()
    l=Line(av,bv)
    bb=BoundingBox(min(merc1[0],merc2[0]),
                   min(merc1[1],merc2[1]),
                   max(merc1[0],merc2[0]),
                   max(merc1[1],merc2[1])).expanded(onenm*minimum_distance*1.5)
    
    obstacles=[0]
    for item in chain(notam_geo_search.get_notam_objs_cached()['obstacles'],
                      extracted_cache.get_obstacles_in_bb(bb)):
        if not 'pos' in item: continue        
        if not 'elev' in item: continue        
        try:
            itemmerc=mapper.latlon2merc(mapper.from_str(item['pos']),13)            
        except Exception:
            print "Bad coord:",item['pos']
            continue
        itemv=Vertex(int(itemmerc[0]),int(itemmerc[1]))
        onenm=mapper.approx_scale(itemmerc,13,1.0)        
        actualclosest=l.approx_closest(itemv)        
        
        
        actualdist=(actualclosest-itemv).approxlength()/onenm
        if actualdist<minimum_distance:
            itemalt=mapper.parse_elev(item['elev'])
            obstacles.append(itemalt)
            
    minstep=2*onenm
            
    stepcount=linelen/float(minstep)
    if stepcount>100:
        newstep=linelen/100.0
        if newstep>minstep:
            minstep=newstep
        
    if linelen<1e-3:
        linelen=1e-3
    along=0.0
    #isfirstorlast=(idx==0 or idx==l-1)        
    while True:
        alongf=float(along)/float(linelen)
        end=False
        if alongf>1.0:
            alongf=1.0
            end=True
        merc=((1.0-alongf)*merc1[0]+(alongf)*merc2[0],
              (1.0-alongf)*merc1[1]+(alongf)*merc2[1])        
        latlon=mapper.merc2latlon(merc,13)
        elev=get_terrain_elev_in_box_approx(latlon,2.0*minstep/onenm)
        obstacles.append(elev)            
        along+=minstep
        if end: break
            
    return max(obstacles)
