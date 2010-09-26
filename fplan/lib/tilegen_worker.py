import sys, os, tempfile
import fplan.lib.mapper as mapper
import math
import Pyro.naming
import md5
import Pyro.core
import Image
import cairo
import numpy
from fplan.extract.extracted_cache import get_airspaces,get_obstacles,get_airfields,get_sig_points,get_aip_sup_areas
import fplan.extract.parse_obstacles as parse_obstacles
import StringIO
from fplan.lib.notam_geo_search import get_notam_objs_cached

#have_mapnik=True
have_mapnik=False
#If changing this - also change 'meta=x' in tilegen_planner .

def use_existing_tiles():
    if have_mapnik: return None
    #if tma:
    #    return "/home/anders/saker/avl_fplan_world/tiles/airspace"
    #else:
    return True
    
if have_mapnik:
    import mapnik
    prj = mapnik.Projection("+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over")
else:
    import maptilereader

def get_dirpath(cachedir,zoomlevel,x1,y1):
    print "X1: %d, Y1: %d, tilepixelsize: %d"%(x1,y1,tilepixelsize)
    assert (x1%tilepixelsize)==0
    assert (y1%tilepixelsize)==0
    assert type(zoomlevel)==int
    assert type(x1)==int
    assert type(y1)==int
    return os.path.join(cachedir,str(int(zoomlevel)),str(y1))
def get_path(cachedir,zoomlevel,x1,y1):
    return os.path.join(get_dirpath(cachedir,zoomlevel,x1,y1),str(x1)+".png")
    



    
def generate_big_tile(pixelsize,x1,y1,zoomlevel,tma=False,return_format="PIL"):
    imgx,imgy=pixelsize

    if not use_existing_tiles():
        #print "Making %dx%d tile at %s/%s, zoomlevel: %d"%(pixelsize[0],pixelsize[1],x1,y1,zoomlevel)
        #print "Generating tile"
        mapfile = "/home/anders/saker/avl_fplan_world/mapnik_render/osm.xml"
        
        #---------------------------------------------------
        #  Change this to the bounding box you want
        #
        #    lon         lat        lon        lat
        #ll = (center[1], hilat, center[1], lolat)
        #---------------------------------------------------
            
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
        
        buf=im.tostring()
        #print "len im tostring:" ,len(buf)
        assert len(buf)%4==0
        num_pixels=len(buf)/4            
        as_array=numpy.fromstring(buf,numpy.dtype("u1"))
        assert len(as_array)==len(buf)
        r,g,b,a=numpy.hsplit(as_array.reshape(num_pixels,4),(1,2,3))
        assert len(r)==num_pixels
        #print "Num pixels: ",num_pixels
        swapped=numpy.column_stack((b,g,r,a)).reshape(4*num_pixels)
        assert len(swapped)==num_pixels*4   
        assert num_pixels==imgx*imgy
        im=cairo.ImageSurface.create_for_data(swapped,cairo.FORMAT_RGB24,imgx,imgy)
        #as_array=numpy.fromstring(buf,numpy.dtype("u4"))
        #as_array.byteswap(True)
    else:
        im=Image.new("RGBA",(imgx,imgy))
        for i in xrange(0,pixelsize[0],256):
            for j in xrange(0,pixelsize[1],256):
                #print "i,j: %d,%d"%(i,j)
                #fname=get_path(use_existing_tiles(),zoomlevel,x1+i,y1+j)
                #if os.path.exists(fname):
                #    sub=Image.open(fname)
                #else:
                #    print "Warning, missing data: ",fname
                #    sub=Image.open("fplan/public/nodata.png")
                rawtile,tilemeta=maptilereader.gettile("plain",zoomlevel,x1+i,y1+j)
                io=StringIO.StringIO(rawtile)
                io.seek(0)
                sub=Image.open(io)
                im.paste(sub,(i,j,i+256,j+256))
                
        buf=im.tostring()
        #print "len im tostring:" ,len(buf)
        assert len(buf)%4==0
        num_pixels=len(buf)/4           
        assert num_pixels==imgx*imgy 
        as_array=numpy.fromstring(buf,numpy.dtype("u1"))
        assert len(as_array)==len(buf)
        r,g,b,a=numpy.hsplit(as_array.reshape(num_pixels,4),(1,2,3))
        assert len(r)==num_pixels
        #print "Num pixels: ",num_pixels
        swapped=numpy.column_stack((b,g,r,a)).reshape(4*num_pixels)
        im=cairo.ImageSurface.create_for_data(swapped,cairo.FORMAT_RGB24,imgx,imgy)
    


    ctx=cairo.Context(im)
    if tma:
        def tolocal(merc):
            return (merc[0]-x1,merc[1]-y1)
        for space in get_airspaces()+get_notam_objs_cached()['areas']+get_aip_sup_areas():        
            
            for coord in space['points']:
                merc=mapper.latlon2merc(mapper.from_str(coord),zoomlevel)
                ctx.line_to(*tolocal(merc))#merc[0]-x1,merc[1]-y1)
            areacol,solidcol=dict(
                        TMA=((1.0,1.0,0.0,0.15),(1.0,1.0,0.0,0.75)),
                        CTA=((1.0,0.85,0.0,0.20),(1.0,0.85,0.0,0.75)),
                        R=((1.0,0.0,0.0,0.15),(1.0,0.0,0.0,0.75)),
                        CTR=((1.0,0.5,0.0,0.15),(1.0,0.5,0.0,0.75)),
                        notamarea=((0.5,1,0.5,0.15),(0.25,1,0.25,0.9)),
                        aip_sup=  ((0.8,1,0.8,0.05),(0.8,1,0.8,0.75)),
                        mountainarea=((0.7,0.7,1.0,0.05),(0.7,0.7,1.0,0.75)),
                        )[space['type']]
                        
            ctx.close_path()   
            ctx.set_source(cairo.SolidPattern(*areacol))
            ctx.fill_preserve()
            ctx.set_source(cairo.SolidPattern(*solidcol))
            ctx.stroke()
        for obst in get_obstacles():
            if zoomlevel>=9:
                ctx.set_source(cairo.SolidPattern(1.0,0.0,1.0,0.25))
                merc=mapper.latlon2merc(mapper.from_str(obst['pos']),zoomlevel)
                pos=tolocal(merc)#(merc[0]-x1,merc[1]-y1)            
                radius=parse_obstacles.get_pixel_radius(obst,zoomlevel)
                
                ctx.new_path()
                ctx.arc(pos[0],pos[1],radius,0,2*math.pi)
                ctx.fill_preserve()
                ctx.set_source(cairo.SolidPattern(1.0,0.0,1.0,0.75))
                ctx.new_path()
                ctx.arc(pos[0],pos[1],radius,0,2*math.pi)
                ctx.stroke()                 

        for sigp in get_sig_points():
            if zoomlevel>=9:
                ctx.set_source(cairo.SolidPattern(1.0,1.0,0.0,0.25))
                merc=mapper.latlon2merc(mapper.from_str(sigp['pos']),zoomlevel)
                pos=tolocal(merc)#(merc[0]-x1,merc[1]-y1)            
                radius=3            
                ctx.new_path()
                ctx.arc(pos[0],pos[1],radius,0,2*math.pi)
                ctx.fill_preserve()
                ctx.set_source(cairo.SolidPattern(1.0,1.0,0.0,0.75))
                ctx.new_path()
                ctx.arc(pos[0],pos[1],radius,0,2*math.pi)
                ctx.stroke()                 
                
        for notamtype,items in get_notam_objs_cached().items():
            if notamtype=="areas": continue
            for item in items:
                if zoomlevel>=8:
                    ctx.set_source(cairo.SolidPattern(0.25,1,0.25,0.25))
                    merc=mapper.latlon2merc(mapper.from_str(item['pos']),zoomlevel)
                    pos=tolocal(merc)#(merc[0]-x1,merc[1]-y1)            
                    radius=5
                    
                    ctx.new_path()
                    ctx.arc(pos[0],pos[1],radius,0,2*math.pi)
                    ctx.fill_preserve()
                    ctx.set_source(cairo.SolidPattern(0,1.0,0,0.75))
                    ctx.new_path()
                    ctx.arc(pos[0],pos[1],radius,0,2*math.pi)
                    ctx.stroke()                 
                               
        for airfield in get_airfields():
            if zoomlevel<6:
                continue
            ctx.set_source(cairo.SolidPattern(0.8,0.5,1.0,0.25))
            merc=mapper.latlon2merc(mapper.from_str(airfield['pos']),zoomlevel)
            pos=(merc[0]-x1,merc[1]-y1)
            if zoomlevel<=11:            
                radius=5
            else:
                radius=5<<(zoomlevel-11)
            
            ctx.new_path()
            ctx.arc(pos[0],pos[1],radius,0,2*math.pi)
            ctx.fill_preserve()
            ctx.set_source(cairo.SolidPattern(0.8,0.5,1.0,0.75))
            ctx.new_path()
            ctx.arc(pos[0],pos[1],radius,0,2*math.pi)
            ctx.stroke()
            
            for rwy in airfield.get('runways',[]):
                ends=rwy['ends']
                mercs=[]
                print "Ends:",ends
                for end in ends:
                    print "pos:",end['pos']
                    latlon=mapper.from_str(end['pos'])
                    print "latlon:",latlon
                    merc=mapper.latlon2merc(latlon,zoomlevel)
                    print "Merc:",merc
                    mercs.append(merc)
                if len(mercs)==2:
                    a,b=mercs
                    print "Drawing:",airfield['icao'],a,b
                    ctx.set_source(cairo.SolidPattern(0.0,0.0,0.0,1))
                    lwidth=mapper.approx_scale(a,zoomlevel,40.0/1852.0)
                    if lwidth<=2:
                        lwidth=2.0
                    ctx.set_line_width(lwidth)
                    ctx.new_path()
                    ctx.move_to(*tolocal(a))
                    ctx.line_to(*tolocal(b))
                    ctx.stroke()

        
            
    
    
    if return_format=="PIL":   
        b,g,r,a=numpy.hsplit(swapped.reshape(num_pixels,4),(1,2,3))    
        back=numpy.column_stack((r,g,b)).reshape(3*num_pixels)
        im=Image.frombuffer("RGB",(imgx,imgy),back,'raw','RGB',0,1)
    else:
        assert return_format=="cairo"
        pass
    
    #print "Returning rendered image and map"
    return im

def test_stockholm_tile():
    im=generate_big_tile((2048,2048),71936-256*4,38400-256*4,9,tma=True)
    p="output.png"
    if hasattr(im,'crop'):
        #print "PIL-image"
        view = im.crop((0,0,2048,2048))
        view.save(p,'png')
    else:
        #print "Cairo image"
        im.write_to_png(p)

        

tilepixelsize=256




def do_work_item(planner,coord,descr):
    print "do work item",coord
    zoomlevel,mx1,my1,mx2,my2=coord
    assert mx1%tilepixelsize==0
    assert mx2%tilepixelsize==0
    assert my1%tilepixelsize==0
    assert my2%tilepixelsize==0
    
    metax1=descr['metax1']
    metax2=descr['metax2']
    metay1=descr['metay1']
    metay2=descr['metay2']
    render_tma=descr['render_tma']
    maxy=mapper.max_merc_y(zoomlevel)
    maxx=mapper.max_merc_x(zoomlevel)
    
    im=generate_big_tile((mx2-mx1+metax1+metax2,my2-my1+metay1+metay2),mx1-metax1,my1-metay1,zoomlevel,tma=render_tma)
    cadir=planner.get_cachedir()            
    subwork=[]
    for j in xrange(0,2048,tilepixelsize):
        for i in xrange(0,2048,tilepixelsize):
            
            if mx1+i+tilepixelsize>maxx:
                continue
            if my1+j+tilepixelsize>maxy:
                continue
                
            #dirpath=get_dirpath(cadir,zoomlevel,mx1+i,my1+j)
            #if not os.path.exists(dirpath):
            #    try:
            #        os.makedirs(dirpath)
            #    except:
            #        pass #probably raise, dir now exists
            
            #p=get_path(cadir,zoomlevel,mx1+i,my1+j)

            view = im.crop((metax1+i,metay1+j,metax1+i+256,metay1+j+256))
            io=StringIO.StringIO()
            view.save(io,'png')
            io.seek(0)
            data=io.read()
            subwork.append((zoomlevel,mx1+i,my1+j,data))
    planner.finish_work(coord,subwork)


# finds object automatically if you're running the Name Server.
def run(planner):    
    while True:
        wi=planner.get_work()
        if wi==None:
            break
        coord,descr=wi
        try:
            do_work_item(planner,coord,descr)
        except Exception,cause:
            print "Worker encountered problem: %s"%(cause,)
            planner.giveup_work(coord)
            raise
            
if __name__=="__main__":
    planner=Pyro.core.getProxyForURI("PYRONAME://planner")
    run(planner)
    
    
    
    
    
