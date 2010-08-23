import fplan.lib.mapper as mapper
from pyshapemerge2d import Line2,Vertex,Polygon,vvector
import fplan.extract.extracted_cache as cache
import fplan.extract.parse_obstacles as parse_obstacles
from notam_geo_search import get_notam_objs_cached

def get_obstacles(lat,lon,zoomlevel):
    clickx,clicky=mapper.latlon2merc((lat,lon),zoomlevel)
    for obst in cache.get_obstacles():
        x,y=mapper.latlon2merc(mapper.from_str(obst['pos']),zoomlevel)
        radius=parse_obstacles.get_pixel_radius(obst,zoomlevel)
        d=(clickx-x)**2+(clicky-y)**2
        if d<=(radius+5)**2:
           yield obst

def get_airfields(lat,lon,zoomlevel):
    clickx,clicky=mapper.latlon2merc((lat,lon),zoomlevel)
    for airp in cache.get_airfields():
        x,y=mapper.latlon2merc(mapper.from_str(airp['pos']),zoomlevel)
        radius=20
        d=(clickx-x)**2+(clicky-y)**2
        if d<=(radius)**2:
           yield airp

def get_sigpoints(lat,lon,zoomlevel):
    clickx,clicky=mapper.latlon2merc((lat,lon),zoomlevel)
    for sigp in cache.get_sig_points():
        x,y=mapper.latlon2merc(mapper.from_str(sigp['pos']),zoomlevel)
        radius=10
        d=(clickx-x)**2+(clicky-y)**2
        if d<=(radius)**2:
           yield sigp

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
        

def get_polygons_around(lat,lon,polys):
    zoomlevel=14
    px,py=mapper.latlon2merc((lat,lon),zoomlevel)
    insides=[]
    for space in polys:                
        poly_coords=[]
        for coord in space['points']:
            x,y=mapper.latlon2merc(mapper.from_str(coord),zoomlevel)
            poly_coords.append(Vertex(int(x),int(y)))
        if len(poly_coords)<3:
            print "Space %s has few points: %s "%(space['name'],space['points'])
            continue
        poly=Polygon(vvector(poly_coords))
        print "Checking if inside poly:",space
        if poly.is_inside(Vertex(int(px),int(py))):
            insides.append(space)
            print "Is inside"
        else:
            print "Is NOT inside"
    return insides

def get_polygons_on_line(latlon1,latlon2,polys):
    zoomlevel=14
    px1,py1=mapper.latlon2merc(latlon1,zoomlevel)
    px2,py2=mapper.latlon2merc(latlon2,zoomlevel)
    line=Line2(Vertex(int(px1),int(py1)),Vertex(int(px2),int(py2)))
    crosses=[]
    for space in polys:                
        poly_coords=[]
        for coord in space['points']:
            x,y=mapper.latlon2merc(mapper.from_str(coord),zoomlevel)
            poly_coords.append(Vertex(int(x),int(y)))
        if len(poly_coords)<3:
            print "Space %s has few points: %s "%(space['name'],space['points'])
            continue
        poly=Polygon(vvector(poly_coords))
        print "Checking if intersect poly:",space
        if len(poly.intersect_line(line))>0:
            crosses.append(space)
            print "Is crossing"
        else:
            print "Is NOT crossing"
    return crosses


def get_airspaces(lat,lon):
    spaces=get_polygons_around(lat,lon,cache.get_airspaces())
    return spaces

def get_airspaces_on_line(latlon1,latlon2):
    spaces=get_polygons_on_line(latlon1,latlon2,cache.get_airspaces())
    return spaces


def get_notam_areas(lat,lon):
    return get_polygons_around(lat,lon,get_notam_objs_cached()['areas'])
def get_notam_areas_on_line(latlon1,latlon2):
    return get_polygons_on_line(latlon1,latlon2,get_notam_objs_cached()['areas'])
    
    
    
    
if __name__=="__main__":
    print get_airspaces(59,18)
            
            

    
    
    
