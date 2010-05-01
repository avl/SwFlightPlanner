import mapnik
import sys, os, tempfile
import fplan.lib.mapper as mapper
import math
import Pyro.naming
import md5
import Pyro.core

prj = mapnik.Projection("+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over")

def get_dirpath(cachedir,zoomlevel,x1,y1):
    assert (x1%tilepixelsize)==0
    assert (y1%tilepixelsize)==0
    assert type(zoomlevel)==int
    assert type(x1)==int
    assert type(y1)==int
    return os.path.join(cachedir,str(int(zoomlevel)),str(y1))
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

tilepixelsize=256

def do_work_item(planner,coord,descr):
    zoomlevel,mx1,my1,mx2,my2=coord
    metax1=descr['metax1']
    metax2=descr['metax2']
    metay1=descr['metay1']
    metay2=descr['metay2']
    maxy=mapper.max_merc_y(zoomlevel)
    maxx=mapper.max_merc_x(zoomlevel)
    
    m,im=generate_big_tile((mx2-mx1+metax1+metax2,my2-my1+metay1+metay2),mx1-metax1,my1-metay1,zoomlevel)
    cadir=planner.get_cachedir()            
    for j in xrange(0,2048,tilepixelsize):
        for i in xrange(0,2048,tilepixelsize):
            
            if mx1+i+tilepixelsize>maxx:
                continue
            if my1+j+tilepixelsize>maxy:
                continue
            dirpath=get_dirpath(cadir,zoomlevel,mx1+i,my1+j)
            if not os.path.exists(dirpath):
                try:
                    os.makedirs(dirpath)
                except:
                    pass #probably raise, dir now exists
            
            p=get_path(cadir,zoomlevel,mx1+i,my1+j)
            view = im.view(metax1+i,metay1+j,256,256)
            view.save(p,'png')
            thesum=md5.md5(open(p).read()).hexdigest()
            assert type(thesum)==str            
            alt=planner.get_alternate(str(thesum),p)
            if alt:
                print "Creating hardlink from %s -> %s"%(alt,p)
                os.unlink(p)
                os.link(alt,p)


# finds object automatically if you're running the Name Server.
def run():
    planner = Pyro.core.getProxyForURI("PYRONAME://planner")
    while True:
        wi=planner.get_work()
        if wi==None:
            break
        coord,descr=wi
        do_work_item(planner,coord,descr)
        planner.finish_work(coord)
        
if __name__=="__main__":
    run()
    
