import fplan.lib.mapper as mapper
from pyshapemerge2d import Line,Vertex,Polygon,vvector
import fplan.extract.extracted_cache as cache
from fplan.lib.bsptree import BoundingBox
import fplan.extract.parse_obstacles as parse_obstacles
from notam_geo_search import get_notam_objs_cached
from fplan.lib.get_terrain_elev import get_terrain_elev
from itertools import chain

def get_pos_elev(latlon):
    for airf in cache.get_airfields():
        #print "Considering:",airf
        apos=mapper.from_str(airf['pos'])
        dx=apos[0]-latlon[0]
        dy=apos[1]-latlon[1]
        if abs(dx)+abs(dy)<0.25*1.0/60.0 and 'elev' in airf:
            return airf['elev']
    return get_terrain_elev(latlon)

def get_obstacles(lat,lon,zoomlevel):
    clickx,clicky=mapper.latlon2merc((lat,lon),13)
    rad=8
    if zoomlevel>=11:
        rad+=(zoomlevel-11)*6
        
    rad<<=(13-zoomlevel)
    bb=BoundingBox(clickx-rad,clicky-rad,clickx+rad,clicky+rad)
    #print "Looking for stuff in bb",bb
    for obst in cache.get_obstacles_in_bb(bb):
        #print "Got obstacle ",obst
        yield obst

def get_sigpoints(lat,lon,zoomlevel):
    clickx,clicky=mapper.latlon2merc((lat,lon),13)
    rad=8<<(13-zoomlevel)
    bb=BoundingBox(clickx-rad,clicky-rad,clickx+rad,clicky+rad)
    out=[]
    for sigp in cache.get_sig_points_in_bb(bb):
        x,y=mapper.latlon2merc(mapper.from_str(sigp['pos']),zoomlevel)
        d=(clickx-x)**2+(clicky-y)**2
        out.append((d,sigp))
    return [sigp for d,sigp in sorted(out)]


def get_airfields(lat,lon,zoomlevel):
    clickx,clicky=mapper.latlon2merc((lat,lon),13)
    rad=10
    if zoomlevel>=10:
        rad<<=(zoomlevel-10)      
    rad<<=(13-zoomlevel)
    bb=BoundingBox(clickx-rad,clicky-rad,clickx+rad,clicky+rad)
    out=[]
    for airp in cache.get_airfields_in_bb(bb):
        x,y=mapper.latlon2merc(mapper.from_str(airp['pos']),zoomlevel)
        d=(clickx-x)**2+(clicky-y)**2
        out.append((d,airp))
    return [airp for d,airp in sorted(out)]
    

def get_notampoints(lat,lon,zoomlevel):
    clickx,clicky=mapper.latlon2merc((lat,lon),zoomlevel)
    for kind,items in get_notam_objs_cached().items():
        if kind!="areas":
            for item in items:            
                x,y=mapper.latlon2merc(mapper.from_str(item['pos']),zoomlevel)
                radius=10
                d=(clickx-x)**2+(clicky-y)**2
                if d<=(radius)**2:
                   yield item



def get_notampoints_on_line(latlon1,latlon2,dist_nm):
    zoomlevel=13
    distmax=mapper.approx_scale(mapper.latlon2merc(latlon1,zoomlevel),zoomlevel,dist_nm)
    px1,py1=mapper.latlon2merc(latlon1,zoomlevel)
    px2,py2=mapper.latlon2merc(latlon2,zoomlevel)
    a=Vertex(int(px1),int(py1))
    b=Vertex(int(px2),int(py2))
    line=Line(a,b)    
    crosses=[]
    for kind,items in get_notam_objs_cached().items():
        if kind!="areas":
            for item in items:
                x,y=mapper.latlon2merc(mapper.from_str(item['pos']),zoomlevel)
                d=line.approx_dist(Vertex(int(x),int(y)))
                clo=line.approx_closest(Vertex(int(x),int(y)))
                alongd=(clo-a).approxlength()
                totd=(a-b).approxlength()
                #print "AlongD: %s, totd: %s"%(alongd,totd)
                #print "Line: %s, notam coord: %s, closest: %s"%((a,b),(x,y),clo)
                #print "Item %s, d: %s, distmax: %s"%(item,d,distmax)
                if totd<1e-6:
                    perc=0
                else:                    
                    perc=alongd/totd
                if d<distmax:
                    #print "Yielding item."
                    yield dict(item=item,alongperc=perc)
        

def get_polygons_around(lat,lon,polys):
    zoomlevel=13
    px,py=mapper.latlon2merc((lat,lon),zoomlevel)
    insides=[]
    for space in polys:                
        poly_coords=[]
        for coord in space['points']:
            x,y=mapper.latlon2merc(mapper.from_str(coord),zoomlevel)
            poly_coords.append(Vertex(int(x),int(y)))
        if len(poly_coords)<3:
            #print "Space %s has few points: %s "%(space['name'],space['points'])
            continue
        poly=Polygon(vvector(poly_coords))
        #print "Checking if inside poly:",space
        if poly.is_inside(Vertex(int(px),int(py))):
            insides.append(space)
            #print "Is inside"
        else:
            pass#print "Is NOT inside"
    return insides


def get_polygons_around2(lat,lon,polyspaces):
    """for Polygon,Space-pairs"""
    zoomlevel=13
    px,py=mapper.latlon2merc((lat,lon),zoomlevel)
    insides=[]
    for polyspace in polyspaces:                
        poly,space=polyspace
        #print "Checking if inside poly:",space
        if poly.is_inside(Vertex(int(px),int(py))):
            insides.append(space)
            #print "Is inside"
        else:
            pass#print "Is NOT inside"
    return insides


def get_polygons_on_line2(latlon1,latlon2,polyspaces):
    zoomlevel=13
    px1,py1=mapper.latlon2merc(latlon1,zoomlevel)
    px2,py2=mapper.latlon2merc(latlon2,zoomlevel)
    line=Line(Vertex(int(px1),int(py1)),Vertex(int(px2),int(py2)))
    crosses=[]
    for poly,space in polyspaces:                
        if len(poly.intersect_line(line))>0:
            crosses.append(space)
            #print "Is crossing"
        else:
            pass#print "Is NOT crossing"
    return crosses


def get_polygons_on_line(latlon1,latlon2,polys):
    zoomlevel=13
    px1,py1=mapper.latlon2merc(latlon1,zoomlevel)
    px2,py2=mapper.latlon2merc(latlon2,zoomlevel)
    line=Line(Vertex(int(px1),int(py1)),Vertex(int(px2),int(py2)))
    crosses=[]
    for space in polys:                
        poly_coords=[]
        for coord in space['points']:
            x,y=mapper.latlon2merc(mapper.from_str(coord),zoomlevel)
            poly_coords.append(Vertex(int(x),int(y)))
        if len(poly_coords)<3:
            #print "Space %s has few points: %s "%(space['name'],space['points'])
            continue
        poly=Polygon(vvector(poly_coords))
        #print "Checking if intersect poly:",space
        if len(poly.intersect_line(line))>0:
            crosses.append(space)
            #print "Is crossing"
        else:
            pass#print "Is NOT crossing"
    return crosses


def get_airspaces(lat,lon):
    zoomlevel=13
    px,py=mapper.latlon2merc((lat,lon),zoomlevel)
    bb0=BoundingBox(px,py,px,py)
    spaces=get_polygons_around2(lat,lon,cache.get_airspaces_in_bb(bb0))
    return spaces
def get_firs(latlon):
    px1,py1=mapper.latlon2merc(latlon,13)
    bb0=BoundingBox(px1,py1,px1,py1)
    for poly,space in cache.get_firs_in_bb(bb0):
        if poly.is_inside(Vertex(int(px1),int(py1))):
            yield space
            
def get_fir_crossing(latlon1,latlon2):
    """
    Returns tuple of: 
     * airspace-dict
     * latlon of crossing
    """
    px1,py1=mapper.latlon2merc(latlon1,13)
    px2,py2=mapper.latlon2merc(latlon2,13)
    bb0=BoundingBox(min(px1,px2),min(py1,py2),max(px1,px2),max(py1,py2))
    line=Line(Vertex(int(px1),int(py1)),Vertex(int(px2),int(py2)))
    for poly,space in cache.get_firs_in_bb(bb0):
        a=poly.is_inside(Vertex(int(px1),int(py1)))
        b=poly.is_inside(Vertex(int(px2),int(py2)))
        print "Considering space %s, starting: %s, ending: %s"%(
                space['name'],a,b)
        
        if b and not a: 
            cross=list(poly.first_entrance(line))
            if cross:
                outlatlon=(cross[0].get_x(),cross[0].get_y())
                return space,mapper.merc2latlon(outlatlon,13)
    return None
        

def get_aip_sup_areas(lat,lon):
    spaces=get_polygons_around(lat,lon,cache.get_aip_sup_areas())
    return spaces

def get_airspaces_on_line(latlon1,latlon2):
    px1,py1=mapper.latlon2merc(latlon1,13)
    px2,py2=mapper.latlon2merc(latlon2,13)
    bb0=BoundingBox(min(px1,px2),min(py1,py2),max(px1,px2),max(py1,py2))
    airsp=list(cache.get_airspaces_in_bb(bb0))
    #print "Intsersecting with",list([a[1]['name'] for a in airsp])
    spaces=get_polygons_on_line2(latlon1,latlon2,airsp)
    return spaces

def get_aip_sup_on_line(latlon1,latlon2):
    spaces=get_polygons_on_line(latlon1,latlon2,cache.get_aip_sup_areas())
    return spaces


def get_notam_areas(lat,lon):
    return get_polygons_around(lat,lon,get_notam_objs_cached()['areas'])
def get_notam_areas_on_line(latlon1,latlon2):
    return get_polygons_on_line(latlon1,latlon2,get_notam_objs_cached()['areas'])
    
    
def get_any_space_on_line(latlon1,latlon2):
    return list(
        chain(
              get_airspaces_on_line(latlon1,latlon2),
              #get_polygons_on_line(latlon1,latlon2,cache.get_airspaces()),
              get_polygons_on_line(latlon1,latlon2,cache.get_aip_sup_areas()),
              get_polygons_on_line(latlon1,latlon2,get_notam_objs_cached()['areas'])
              ))
              
    
if __name__=="__main__":
    print get_airspaces(59,18)
            
            

    
    
    
