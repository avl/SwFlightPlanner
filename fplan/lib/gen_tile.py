#!/usr/bin/python
#lifted from a mapnik sample
import sys, os, tempfile
import Image
from ImageDraw import Draw
import ImageFont
import fplan.lib.mapper as mapper
import cStringIO
import math
import os

#prj = mapnik.Projection("+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over")


def generate_tile(pixelsize,x1,y1,zoomlevel):

    print "Making tile at %s/%s, zoomlevel: %d"%(x1,y1,zoomlevel)
    #print "Generating tile"
    mapfile = os.path.join(os.getenv("SWFP_DATADIR"),"mapnik_render/osm.xml")
    
    #---------------------------------------------------
    #  Change this to the bounding box you want
    #
    #    lon         lat        lon        lat
    #ll = (center[1], hilat, center[1], lolat)
    #---------------------------------------------------
    
    
    meta=50
    imgx,imgy=pixelsize
    mapx=imgx+2*meta
    mapy=imgy+2*meta
    lat1,lon1=mapper.merc2latlon((x1-meta,y1-meta),zoomlevel)
    lat2,lon2=mapper.merc2latlon((x1+imgx+meta,y1+imgy+meta),zoomlevel)
    
    m = mapnik.Map(mapx,mapy)
    mapnik.load_map(m,mapfile)
    c0 = prj.forward(mapnik.Coord(lon1,lat1))
    c1 = prj.forward(mapnik.Coord(lon2,lat2))
    if hasattr(mapnik,'mapnik_version') and mapnik.mapnik_version() >= 800:
        #bbox = mapnik.Box2d(0,0,256<<zoomlevel,256<<zoomlevel)
        bbox = mapnik.Box2d(c0.x,c0.y,c1.x,c1.y)
    else:
        bbox = mapnik.Envelope(c0.x,c0.y,c1.x,c1.y)
        #bbox = mapnik.Envelope(0,0,256<<zoomlevel,256<<zoomlevel)
    m.zoom_to_box(bbox)
    im = mapnik.Image(mapx,mapy)
    mapnik.render(m, im)
    
    view = im.view(meta,meta,imgx,imgy) # x,y,width,height
    temphandle,temppath=tempfile.mkstemp(suffix="fplantile")
    try:
        os.close(temphandle)
        view.save(temppath,'png')
        data=open(temppath).read()
    finally:
        os.unlink(temppath)
    print "Tile complete"
    return data
