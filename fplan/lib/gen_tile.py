#!/usr/bin/python
#lifted from a mapnik sample
import mapnik
import sys, os, tempfile
import Image
from ImageDraw import Draw
import ImageFont
import fplan.lib.mapper as mapper
import cStringIO
import math

prj = mapnik.Projection("+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over")


def get_map_corners():
    raise Exception("Not supported")
"""
def generate_tile(pixelsize,x1,y1,zoomlevel):
    img=Image.new("RGB",pixelsize)
    draw=Draw(img)
    #merc=mapper.latlon2merc(center,zoomlevel)
    min_x=x1#int(merc[0])-0.5*pixelsize[0]
    min_y=y1#int(merc[1])-0.5*pixelsize[1]
    max_x=x1+pixelsize[0]
    max_y=y1+pixelsize[1]
    font = ImageFont.truetype("/var/lib/defoma/x-ttcidfont-conf.d/dirs/TrueType/FreeMonoBold.ttf",14)
    draw=Draw(img)
    def modrange(a,b,mod):
        start=mod*int(math.floor(a/mod))
        end=mod*int(math.ceil(b/mod))
        return xrange(start,end,mod)
    
    
    #draw.text((0,0),"upper",fill=(255,255,255),font=font)
    draw.rectangle(((0,0),(pixelsize[0]-1,pixelsize[1]-1)),outline=(255,255,255))        
    for y in modrange(min_y,max_y,100):
        for x in modrange(min_x,max_x,100):
            latlon=mapper.merc2latlon((x,y),zoomlevel)
            lat,lon=latlon
            text1="%.2fN"%(lat,)
            text2="%.2fE"%(lon,)
            #print "Drawing at %s: %s/%s"%((x,y),text1,text2)
            draw.text((x-min_x,y-min_y),text1,fill=(255,255,255),font=font)        
            draw.text((x-min_x,y-min_y+15),text2,fill=(255,255,255),font=font)        
    outp=cStringIO.StringIO()
    img.save(outp,"png")
    outp.seek(0)
    print "Zoomlevel:",zoomlevel
    return outp.read()
"""


def generate_tile(pixelsize,x1,y1,zoomlevel):

    print "Making tile at %s/%s, zoomlevel: %d"%(x1,y1,zoomlevel)
    #print "Generating tile"
    mapfile = "/home/anders/saker/avl_fplan_world/mapnik_render/osm.xml"
    
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

tilepixelsize=256

def get_dirpath(cachedir,zoomlevel,x1,y1):
    assert (x1%tilepixelsize)==0
    assert (y1%tilepixelsize)==0
    assert type(zoomlevel)==int
    assert type(x1)==int
    assert type(y1)==int
    iy=y1/tilepixelsize
    ix=x1/tilepixelsize
    return os.path.join(cachedir,str(int(zoomlevel)),str(iy))
def get_path(cachedir,zoomlevel,x1,y1):
    return os.path.join(get_dirpath(cachedir,zoomlevel,x1,y1),str(x1)+".png")
    

def generate_big_tile(pixelsize,x1,y1,zoomlevel):

    #print "Making %dx%d tile at %s/%s, zoomlevel: %d"%(pixelsize[0],pixelsize[1],x1,y1,zoomlevel)
    #print "Generating tile"
    mapfile = "/home/anders/saker/avl_fplan_world/mapnik_render/osm.xml"
    
    #---------------------------------------------------
    #  Change this to the bounding box you want
    #
    #    lon         lat        lon        lat
    #ll = (center[1], hilat, center[1], lolat)
    #---------------------------------------------------
        
    imgx,imgy=pixelsize
    lat1,lon1=mapper.merc2latlon((x1,y1),zoomlevel)
    lat2,lon2=mapper.merc2latlon((x1+imgx,y1+imgy),zoomlevel)
    
    m = mapnik.Map(imgx,imgy)
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
    im = mapnik.Image(imgx,imgy)
    mapnik.render(m, im)
    #print "Returnign rendered image and map"
    return m,im
    
def generate_tile_cache(cachedir,limits):
    lat1,lon1,lat2,lon2=limits.split(",")
    lat1=float(lat1)
    lat2=float(lat2)
    lon1=float(lon1)
    lon2=float(lon2)
    meta=50    
    for zoomlevel in xrange(12):
        maxy=mapper.max_merc_y(zoomlevel)
        maxx=mapper.max_merc_x(zoomlevel)
        for my1 in xrange(0,maxy,2048):
            for mx1 in xrange(0,maxy,2048):
                
                
                
                mx2=mx1+2048
                my2=my1+2048
                if my2>maxy:
                    my2=maxy
                if mx2>maxx:
                    mx2=maxx
                if my1>=meta:
                    metay1=meta
                else:
                    metay1=0
                if mx1>=meta:
                    metax1=meta
                else:
                    metax1=0
                if my2<=maxy-meta:
                    metay2=meta
                else:
                    metay2=0
                if mx2<=maxx-meta:
                    metax2=meta
                else:
                    metax2=0
                    
                latb,lona=mapper.merc2latlon((mx1,my1),zoomlevel)
                lata,lonb=mapper.merc2latlon((mx2,my2),zoomlevel)
                if latb<lat1: continue
                if lata>lat2: continue
                if lonb<lon1: continue
                if lona>lon2: continue
                    
                #print "maxx: ",maxx,"maxy: ",maxy
                #print "mx1,my1",mx1,my1
                #print "mx2,my2",mx2,my2
                #print "metas:",metax1,metay1,metax2,metay2
                allexist=True
                deleteonfailure=set()
                existing=set()                            
                try:
                    for j in xrange(0,2048,tilepixelsize):
                        for i in xrange(0,2048,tilepixelsize):
                            #print "ij",i,j
                            if mx1+i+tilepixelsize>maxx:
                                continue
                            if my1+j+tilepixelsize>maxy:
                                continue
                            dirpath=get_dirpath(cachedir,zoomlevel,mx1+i,my1+j)
                            if not os.path.exists(dirpath):
                                try:
                                    os.makedirs(dirpath)
                                except:
                                    pass #probably raise, dir now exists
                            p=get_path(cachedir,zoomlevel,mx1+i,my1+j)
                            if not os.path.exists(p):
                                allexist=False
                                try:
                                    fd=os.open(p, os.O_WRONLY|os.O_EXCL|os.O_CREAT)
                                except:
                                    existing.add(p)
                                    continue
                                deleteonfailure.add(p)
                                os.close(fd)
                            else:
                                existing.add(p)
                            
                    if allexist:
                        continue
                        
                    m,im=generate_big_tile((mx2-mx1+metax1+metax2,my2-my1+metay1+metay2),mx1-metax1,my1-metay1,zoomlevel)        
                    
                    for j in xrange(0,2048,tilepixelsize):
                        for i in xrange(0,2048,tilepixelsize):
                            #print "ij",i,j
                            if mx1+i+tilepixelsize>maxx:
                                continue
                            if my1+j+tilepixelsize>maxy:
                                continue
                            p=get_path(cachedir,zoomlevel,mx1+i,my1+j)
                            if p in existing: continue
                            #print "Writing view %d,%d to %s"%(metax1+i,metay1+i,p)                            
                            view = im.view(metax1+i,metay1+j,256,256)
                            view.save(p,'png')
                            deleteonfailure.remove(p)
                    inty=my1/2048.0
                    intx=mx1/2048.0
                    tot=(maxx/2048.0)*(maxy/2048.0)
                    print "Zoom level %d, %.2f%%"%(zoomlevel,100.0*(inty*(maxx/2048.0)+intx)/(tot  ))
                except:
                    for d in deleteonfailure:
                        os.unlink(d)
                    raise                
    
if __name__=='__main__':
    if len(sys.argv)<3:
        limit="55,10,69,24"
    else:
        limit=sys.argv[2]
    generate_tile_cache(sys.argv[1],limit)
"""    
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
"""
    

