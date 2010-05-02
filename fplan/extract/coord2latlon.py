import sys
import math
from math import cos,sin
import fplan.lib.mapper as mapper

def parse_line(l,inv=True):
    name,coords_str=l.split(":")
    coords=[]
    for coord_str in coords_str.strip().split(";"):
        coord=[]
        for component in coord_str.strip().split(","):
            coord.append(int(component.strip()))
        if inv:
            x,y=coord
            x=float(x)
            y=float(y)
        else:
            x,y=coord

        coords.append((x,y))
    return name.strip(),coords

def vec_len(x):
    return math.sqrt(x[0]**2.0+x[1]**2.0)
def vec_sub(x,y):
    return x[0]-y[0],x[1]-y[1]
def get_angle(v):
    return math.atan2(v[1],v[0])
def format_latlon(p):
    return "%.5fN%.5fE"%(p[1],p[0])

def vec_add(a,b):
    return a[0]+b[0],a[1]+b[1]
def vec_mul(k,a):
    return k*a[0],k*a[1]
def vec_rotate(angle,vec):
    return (cos(angle)*vec[0]-sin(angle)*vec[1],
            sin(angle)*vec[0]+cos(angle)*vec[1])

Error: What needs to be done: Convert to mercator proj coords for all coord2latlon purposes!
def fixup(coord,calib):

    center_coord=calib['center_coord']
    center_geo_points=calib['center_geo_points']
    rotate=calib['rotate']
    scale=calib['scale']

    coord_off=vec_sub(coord,center_coord)
    scaled=vec_mul(scale,coord_off)
    rotated=vec_rotate(rotate,scaled)
    finished=vec_add(rotated,center_geo_points)
    return finished

def run(path):
    f=open(path)
    lines=list(f)
    calib=None
    for line in lines:
        name,coords=parse_line(line)
        if name.count("(")==1 and name.count(")")==1:
            print "Calib:",name,coords
            assert calib==None #only one calibration line per file, please
            dummy,rest=name.split("(")
            assert rest.endswith(")")
            rest=rest[:-1]
            geo_points=[]
            for c_str in rest.split("-"):
                geo_point=[]
                for comp_str in c_str.split(","):
                    geo_point.append(float(comp_str.strip()))

                geo_points.append(tuple(mapper.latlon2merc((geo_point[0],geo_point[1]),zoomlevel)))
            assert len(geo_points)==2
            print "Geo_points:",geo_points
            print "Coords:",coords
            geo_dist=vec_len(vec_sub(*geo_points))
            coord_dist=vec_len(vec_sub(*coords))
            geo_angle=get_angle(vec_sub(geo_points[1],geo_points[0]))
            coord_angle=get_angle(vec_sub(coords[1],coords[0]))
            print "Geo angle: %f"%(geo_angle*180.0/math.pi)
            print "Coord angle: %f"%(coord_angle*180.0/math.pi)

            coord_offset=vec_sub(geo_points[0],coords[0])

            calib=dict(
                center_coord=coords[0],
                center_geo_points=geo_points[0],
                rotate=geo_angle-coord_angle,
                scale=float(geo_dist)/float(coord_dist))
    assert calib!=None
    print calib
    for line in lines:
        name,coords=parse_line(line)
        #if name.count("(")!=1 or name.count(")")!=1:
        geo_points=[]
        for cd in coords:
            geo_points.append(fixup(cd,calib))
        print name,":","; ".join(format_latlon(mapper.merc2mlatlon(c,zoomlevel)) for c in geo_points)
    


if __name__=='__main__':
    run(sys.argv[1])

    