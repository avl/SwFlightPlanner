import sys, os, tempfile
import fplan.lib.mapper as mapper
import math
import Pyro.naming
import md5
import Pyro.core
import Image
import cairo
import numpy
from fplan.extract.extracted_cache import get_firs,get_airspaces_in_bb2,get_obstacles_in_bb,get_airfields_in_bb,get_sig_points_in_bb,get_aip_sup_areas
import fplan.extract.parse_obstacles as parse_obstacles
import StringIO
from fplan.lib.notam_geo_search import get_notam_objs_cached
import socket
import maptilereader
from itertools import izip,chain
import userdata
import sys
from bsptree import BoundingBox
#have_mapnik=True

#If changing this - also change 'meta=x' in tilegen_planner .
try:
    try:
        import mapnik
    except:
        import mapnik2 as mapnik
    have_mapnik=True
    prj = mapnik.Projection("+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over")
except Exception:
    have_mapnik=False



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
    
from typecolor import typecolormap
def get_airspace_color(airspacetype):
    """returns area-color , edge/solid color"""
    return typecolormap[airspacetype]
    
def generate_big_tile(pixelsize,x1,y1,zoomlevel,osmdraw,tma=False,return_format="PIL",user=None,only_user=False):
    """
    set osmdraw==True and make sure a full working openstreetmap mapnik environment is available,
    in order to draw using mapnik. If false, a basemap must already have been drawn, and all that can
    be done is that new airspaces etc an be filled in.
    """
    def only(x):
        if only_user:
            #print "Ignoring ",len(x)
            return []
        return x
    print "TMA:",tma
    imgx,imgy=pixelsize
    assert osmdraw in [True,False]
    if not osmdraw: #osmdraw should probably be renamed use 'use_existing_basemap'
        print "Making %dx%d tile at %s/%s, zoomlevel: %d"%(pixelsize[0],pixelsize[1],x1,y1,zoomlevel)
        print "Generating tile"
        print "mapnikstyle file:",os.getenv("SWFP_MAPNIK_STYLE")
        mapfile = os.path.join(os.getenv("SWFP_MAPNIK_STYLE"),"osm.xml")
        
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
        print "Num pixels: ",num_pixels
        swapped=numpy.column_stack((b,g,r,a)).reshape(4*num_pixels)
        assert len(swapped)==num_pixels*4   
        assert num_pixels==imgx*imgy
        im=cairo.ImageSurface.create_for_data(swapped,cairo.FORMAT_RGB24,imgx,imgy)
        #as_array=numpy.fromstring(buf,numpy.dtype("u4"))
        #as_array.byteswap(True)
    else:
        #print "Reading existing map instead"
        im=Image.new("RGBA",(imgx,imgy))
        for i in xrange(0,pixelsize[0],256):
            for j in xrange(0,pixelsize[1],256):
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
        
        merc13=mapper.merc2merc((x1-50,y1-50),zoomlevel,13)
        merc13b=mapper.merc2merc((x1+imgx+50,y1+imgy+50),zoomlevel,13)
        bb13=BoundingBox(merc13[0],merc13[1],merc13b[0],merc13b[1])
        
        
        bycolor=dict()
        for space in chain(
                only(get_airspaces_in_bb2(bb13)),get_notam_objs_cached()['areas'],
                only(get_aip_sup_areas()),get_firs(),userdata.get_all_airspaces(user)):        
            if space['type']=='sector':
                continue #Don't draw "sectors"
            vertices=[]
            for coord in space['points']:
                merc=mapper.latlon2merc(mapper.from_str(coord),zoomlevel)
                vertices.append(tolocal(merc))#merc[0]-x1,merc[1]-y1)
            try:
                areacol,solidcol=get_airspace_color(space['type'])
            except Exception:
                print space
                raise   
            bycolor.setdefault((areacol,solidcol),[]).append(vertices)
        def colorsorter(col):
            if col[0]>0.5: return (110,0,0,0)
            return col
            
        for (areacol,solidcol),polygons in sorted(bycolor.items(),key=lambda x:colorsorter(x[0])):
            if areacol[3]<=0.05: continue
            surface2 = cairo.ImageSurface(cairo.FORMAT_ARGB32, imgx, imgy)
            ctx2=cairo.Context(surface2)
            ctx2.set_operator(cairo.OPERATOR_DEST_OUT)
            ctx2.rectangle(0,0,imgx,imgy)
            ctx2.set_source(cairo.SolidPattern(0,0,0,1.0))
            ctx2.paint()
            ctx2.set_operator(cairo.OPERATOR_OVER)
            for poly in polygons:
                ctx2.new_path()
                for vert in poly:
                    ctx2.line_to(*vert)
                ctx2.close_path()   
                ctx2.set_source(cairo.SolidPattern(areacol[0],areacol[1],areacol[2],1.0))
                ctx2.fill_preserve()
            ctx2.set_operator(cairo.OPERATOR_DEST_OUT)
            ctx2.rectangle(0,0,imgx,imgy)
            ctx2.set_source(cairo.SolidPattern(0,0,0,1.0-areacol[3]))
            ctx2.paint()
            #ctx2.set_operator(cairo.OPERATOR_OVER)
            
            ctx.set_source_surface(surface2)
            ctx.rectangle(0,0,imgx,imgy)
            ctx.paint()
        for (areacol,solidcol),polygons in sorted(bycolor.items(),key=lambda x:colorsorter(x[1])):
            for poly in polygons:
                ctx.new_path()
                for vert in poly:
                    ctx.line_to(*vert)
                ctx.close_path()   
                ctx.set_source(cairo.SolidPattern(*solidcol))
                ctx.stroke()
        for obst in chain(only(get_obstacles_in_bb(bb13)),userdata.get_all_obstacles(user)):
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

        for sigp in chain(only(get_sig_points_in_bb(bb13)),userdata.get_all_sigpoints(user)):
            if zoomlevel>=9:
                #print sigp
                if zoomlevel==9 and sigp.get('kind','') in ['entry/exit point','holding point']:
                    continue
                if sigp.get('kind','') in ['town','city']:continue
                merc=mapper.latlon2merc(mapper.from_str(sigp['pos']),zoomlevel)
                pos=tolocal(merc)#(merc[0]-x1,merc[1]-y1)            
                ctx.set_source(cairo.SolidPattern(0.0,0.0,1.0,0.65))
                ctx.new_path()
                ctx.line_to(pos[0],pos[1]-3)
                ctx.line_to(pos[0]+3,pos[1])
                ctx.line_to(pos[0],pos[1]+3)
                ctx.line_to(pos[0]-3,pos[1])
                ctx.close_path()   
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
                               
        for airfield in chain(only(get_airfields_in_bb(bb13)),userdata.get_all_airfields(user)):
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
                #print "Ends:",ends
                surface=rwy.get('surface','hard').lower()
                for end in ends:
                    #print "pos:",end['pos']
                    latlon=mapper.from_str(end['pos'])
                    #print "latlon:",latlon
                    merc=mapper.latlon2merc(latlon,zoomlevel)
                    #print "Merc:",merc
                    mercs.append(merc)
                if len(mercs)==2:
                    a,b=mercs
                    #print "Drawing:",airfield['icao'],a,b
                    if surface=='gravel':
                        ctx.set_source(cairo.SolidPattern(0.5,0.3,0.0,1))
                    elif surface=='grass':
                        ctx.set_source(cairo.SolidPattern(0.0,0.65,0.0,1))
                    else:
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
    im=generate_big_tile((2048,2048),71936-256*4,38400-256*4,9,osmdraw=False,tma=False)
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
    
    im=generate_big_tile((mx2-mx1+metax1+metax2,my2-my1+metay1+metay2),mx1-metax1,my1-metay1,zoomlevel,osmdraw=render_tma,tma=render_tma)
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
            #    except Exception:
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
    if len(sys.argv)>1 and sys.argv[1]=="test":
        test_stockholm_tile()
        sys.exit()
    planner=Pyro.core.getProxyForURI("PYRONAME://planner")
    run(planner)
    
    
    
    
    
