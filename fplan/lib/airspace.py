import fplan.lib.mapper as mapper
from pyshapemerge2d import Line2,Vertex,Polygon,vvector
import fplan.extract.extracted_cache as cache

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
            
            

    
    
    
