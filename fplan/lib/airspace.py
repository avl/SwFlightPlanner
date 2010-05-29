import fplan.lib.mapper as mapper
from pyshapemerge2d import Line2,Vertex,Polygon,vvector
import fplan.extract.extracted_cache as cache
import fplan.extract.parse_obstacles as parse_obstacles

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


def get_airspaces(lat,lon):
    zoomlevel=14
    px,py=mapper.latlon2merc((lat,lon),zoomlevel)
    insides=[]
    for space in cache.get_airspaces():                
        poly_coords=[]
        for coord in space['points']:
            x,y=mapper.latlon2merc(mapper.from_str(coord),zoomlevel)
            poly_coords.append(Vertex(int(x),int(y)))
        if len(poly_coords)<3:
            print "Space %s has few points: %s "%(space['name'],space['points'])
            continue
        poly=Polygon(vvector(poly_coords))
        if poly.is_inside(Vertex(int(px),int(py))):
            insides.append(space)
    return insides
    
if __name__=="__main__":
    print get_airspaces(59,18)
            
            

    
    
    
