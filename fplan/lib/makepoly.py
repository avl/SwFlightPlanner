from pyshapemerge2d import Vertex,Line,Polygon,vvector
import mapper

def poly(points): 
    last=None
    poly_coords=[]
    for coord in points:
        merc=mapper.latlon2merc(mapper.from_str(coord),13)
        if merc==last: continue
        last=merc
        poly_coords.append(Vertex(int(merc[0]),int(merc[1])))
    if len(poly_coords)>=3:
        return Polygon(vvector(poly_coords))
    return None

