#!/usr/bin/python
#lifted from a mapnik sample
import mapnik
import sys, os, tempfile

prj = mapnik.Projection("+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over")

def generate_tile(pixelsize,center,lolat,hilat):
    print "Making tile at %s"%(center,)
    #print "Generating tile"
    mapfile = "/home/anders/saker/avl_fplan_world/mapnik_render/osm.xml"
    
    #---------------------------------------------------
    #  Change this to the bounding box you want
    #
    #    lon         lat        lon        lat
    ll = (center[1], hilat, center[1], lolat)
    #---------------------------------------------------

    
    imgx,imgy=pixelsize

    m = mapnik.Map(imgx,imgy)
    mapnik.load_map(m,mapfile)
    c0 = prj.forward(mapnik.Coord(ll[0],ll[1]))
    c1 = prj.forward(mapnik.Coord(ll[2],ll[3]))
    if hasattr(mapnik,'mapnik_version') and mapnik.mapnik_version() >= 800:
        bbox = mapnik.Box2d(c0.x,c0.y,c1.x,c1.y)
    else:
        bbox = mapnik.Envelope(c0.x,c0.y,c1.x,c1.y)
    m.zoom_to_box(bbox)
    im = mapnik.Image(imgx,imgy)
    mapnik.render(m, im)
    view = im.view(0,0,imgx,imgy) # x,y,width,height
    temphandle,temppath=tempfile.mkstemp(suffix="fplantile")
    try:
        os.close(temphandle)
        view.save(temppath,'png')
        data=open(temppath).read()
    finally:
        os.unlink(temppath)
    #print "Tile complete"
    return data

    
def get_map_corners(pixelsize,center,lolat,hilat):
    mapfile = "/home/anders/saker/avl_fplan_world/mapnik_render/osm.xml"
    
    #---------------------------------------------------
    #  Change this to the bounding box you want
    #
    #    lon         lat        lon        lat
    ll = (center[1], hilat, center[1], lolat)
    #---------------------------------------------------

    
    imgx,imgy=pixelsize

    m = mapnik.Map(imgx,imgy)
    mapnik.load_map(m,mapfile)
    c0 = prj.forward(mapnik.Coord(ll[0],ll[1]))
    c1 = prj.forward(mapnik.Coord(ll[2],ll[3]))
    if hasattr(mapnik,'mapnik_version') and mapnik.mapnik_version() >= 800:
        bbox = mapnik.Box2d(c0.x,c0.y,c1.x,c1.y)
    else:
        bbox = mapnik.Envelope(c0.x,c0.y,c1.x,c1.y)
    m.zoom_to_box(bbox)
    e=m.envelope()
    lowerleft=prj.inverse(mapnik.Coord(e.minx,e.miny))
    upperleft=prj.inverse(mapnik.Coord(e.minx,e.maxy))    
    lowerright=prj.inverse(mapnik.Coord(e.maxx,e.miny))
    upperright=prj.inverse(mapnik.Coord(e.maxx,e.maxy))
    
    assert abs(lowerleft.x-upperleft.x)<1e-6
    assert abs(lowerright.x-upperright.x)<1e-6
    assert abs(upperleft.y-upperright.y)<1e-6
    assert abs(lowerleft.y-lowerright.y)<1e-6
    return (lowerleft.y,lowerleft.x,upperright.y,upperright.x)

    

