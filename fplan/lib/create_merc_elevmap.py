from struct import pack,unpack
from maptilereader import merc_limits
from StringIO import StringIO
from blobfile import BlobFile
from fplan.lib import mapper
from itertools import product
import sys
import numpy
import Image
import md5
import os
tilesize=64
from math import floor
import math


terrain_files=[]

def init_terrain():
    for lat in [90,40]:
        for lon in range(-140,80,40):    
                    
            terrain_files.append(dict(
                fname=os.path.join(os.getenv("SWFP_DATADIR"),"srtp/%s%03d%s%02d.DEM"%(
                    "W" if lon<0 else "E",abs(lon),
                    "N" if lat>0 else 'S',abs(lat))),
                west=lon,
                east=lon+40,
                north=lat,
                south=lat-50))
init_terrain()
    
"""        
    terrain_files.append(dict(
        fname=os.path.join(os.getenv("SWFP_DATADIR"),"srtp/W020N90.DEM"),
        west=-20.0,
        east=20.0,#+1e-5,
        north=90.0,
        south=40.0))
"""

base_xres=4800
base_yres=6000
    

    
def get_terrain_elev(latlon):
    global terrain_files
    lat,lon=latlon
    if terrain_files==[]:
        init_terrain()
    for terr in terrain_files:        
        if lat>=terr['south'] and lat<=terr['north'] and lon>=terr['west'] and lon<=terr['east']:
            xres,yres=4800,6000#res_for_level[resolutionlevel]            
            #xres,yres=res_for_level[resolutionlevel]            
            #print "reading lat/lon:",lat,lon,"size:",xres,yres
            y=int(floor(float(yres)*(terr['north']-lat)/float(terr['north']-terr['south'])))
            x=int(floor(float(xres)*(lon-terr['west'])/float(terr['east']-terr['west'])))
            filename=terr['fname']
            f=open(filename)
            if x>=xres: x=xres-1
            if x<0: x=0
            if y>=yres: y=yres-1
            if y<0: y=0
            
            idx=int(y*xres+x)
            if idx<0: idx=0
            if idx>=xres*yres: idx=xres*yres-1
            f.seek(2*idx)
            bytes=f.read(2)
            elev,=unpack(">h",bytes)
            return elev/0.3048
    print "No elev for: ",latlon
    return -9999



def create_merc_elevmap(dest):    
    zoomlevel=8
    limitx1,limity1,limitx2,limity2=merc_limits(zoomlevel,hd=True)
    tilesizemask=tilesize-1

    #a,b=mapper.latlon2merc((61,15),zoomlevel)
    #limitx1,limity1=int(a),int(b)
    
    #limity1=int(19000)
    #limity2=limity1+tilesize*16
    #limitx1=int(35000)
    #limitx2=limitx1+tilesize*16
    #tilesizemask=tilesize-1
    #limitx1&=~tilesizemask
    #limity1&=~tilesizemask
    #limitx2&=~tilesizemask
    #limity2&=~tilesizemask
    
    assert (limitx1&tilesizemask)==0
    assert (limity1&tilesizemask)==0
    assert (limitx2&tilesizemask)==0
    assert (limity2&tilesizemask)==0
    if os.path.exists(dest):
        os.unlink(dest)
    blob=BlobFile(dest,zoomlevel,limitx1,limity1,limitx2,limity2,"w",tilesize=tilesize)
    for by in xrange(limity1,limity2,tilesize):
        for bx in xrange(limitx1,limitx2,tilesize):
            f=StringIO()
            for y in xrange(tilesize):
                for x in xrange(tilesize):
                    mx=bx+x
                    my=by+y
                    latlon=mapper.merc2latlon((mx,my),zoomlevel)
                    elev=int(get_terrain_elev(latlon))
                    f.write(pack(">h",elev)) #min
                    f.write(pack(">h",elev)) #max
            buf=f.getvalue()
            assert(len(buf)==64*64*4)
            blob.add_tile(bx,by,buf)
            print "Perc complete: %.1f%%"%(100.0*(by-limity1)/float(limity2-limity1))
    blob.close()  
    
    
def refine_merc_elevmap(src,srczoomlevel):
    zoomlevel=srczoomlevel-1
    limitx1,limity1,limitx2,limity2=merc_limits(zoomlevel,hd=True)

    tilesizemask=tilesize-1
    assert (limitx1&tilesizemask)==0
    assert (limity1&tilesizemask)==0

    srcblob=BlobFile(src+"%d"%(srczoomlevel,),tilesize=tilesize)
    trgfile=src+"%d"%(zoomlevel,)
    if os.path.exists(trgfile):
        os.unlink(trgfile)
    trgblob=BlobFile(trgfile,zoomlevel,limitx1,limity1,limitx2,limity2,"w",tilesize=tilesize)
    for by in xrange(limity1,limity2,tilesize):
        #if (by-limity1)/float(limity2-limity1)>0.2:
        #    break
        for bx in xrange(limitx1,limitx2,tilesize):            
            print "Perc complete: %.1f%%"%(100.0*(by-limity1)/float(limity2-limity1))
            loout=numpy.zeros((tilesize,tilesize))
            hiout=numpy.zeros((tilesize,tilesize))
            for suby in xrange(2):
                for subx in xrange(2):
                    srcx=2*(bx)+subx*tilesize
                    srcy=2*(by)+suby*tilesize   
                    buf=srcblob.get_tile(srcx,srcy)
                    if buf==None:
                        continue #It'll be all-zeroes...
                    #print "Got buf:",md5.md5(buf).hexdigest()
                    #print "got at %d,%d: %d bytes"%(srcx,srcy,len(buf) if buf else 0)
                    assert(len(buf)==64*64*4)
                    fi=StringIO(buf)                  
                    losub=numpy.zeros((tilesize,tilesize))
                    hisub=numpy.zeros((tilesize,tilesize))
                    for j in xrange(tilesize):
                        for i in xrange(tilesize):
                            losub[j,i]=unpack(">h",fi.read(2))[0]
                            hisub[j,i]=unpack(">h",fi.read(2))[0]                            
                    fi.close()
                    del fi
                    tsh=tilesize/2
                    for j in xrange(tilesize/2):
                        for i in xrange(tilesize/2):
                            def s(sub,fn):
                                return fn(sub[2*j+a,2*i+b] for (a,b) in product(xrange(2),xrange(2)))
                            losum=s(losub,min)
                            hisum=s(hisub,max)
                            #print "losum: %d from %s"%(losum,losub[2*j,2*i])
                            crd=(j+suby*tsh,i+subx*tsh)
                            #losum=suby*500+subx*2000
                            #hisum=suby*100+subx*500
                            loout[crd]=losum
                            hiout[crd]=hisum
                    del losub
                    del hisub                    
            #print "loout:",loout
            #print "hiout:",hiout
            f=StringIO()
            for j in xrange(tilesize):
                for i in xrange(tilesize):                    
                    f.write(pack(">h",loout[j,i])) #min
                    f.write(pack(">h",hiout[j,i])) #max
            trgblob.add_tile(bx,by,f.getvalue())
        
                               
def verify(src,zoomlevel):
    limitx1,limity1=mapper.latlon2merc((63,15),zoomlevel)
    limitx1=int(limitx1)
    limity1=int(limity1)
    tilesizemask=tilesize-1
    limitx1&=~tilesizemask
    limity1&=~tilesizemask
    srcblob=BlobFile(src+"%d"%(zoomlevel,),tilesize=tilesize)
    f=16
    im=Image.new("RGB",(f*tilesize,f*tilesize))
    basey=0    
    for by in xrange(limity1,limity1+f*tilesize,tilesize):
        basex=0
        print "DOne: %f"%(basey/float(f*tilesize))
        for bx in xrange(limitx1,limitx1+f*tilesize,tilesize):            
            b=srcblob.get_tile(bx,by)
            if b==None: 
                print "NO tile at ",bx,by
                basex+=tilesize
                continue
            print "found tile at ",bx,by
            assert len(b)==4*tilesize*tilesize
            fi=StringIO(b)
            for i in xrange(tilesize):
                for j in xrange(tilesize):
                    lo=unpack(">h",fi.read(2))[0]
                    hi=unpack(">h",fi.read(2))[0]
                    im.putpixel((basex+j,basey+i),(hi/6,hi/6,hi/6.0))
            basex+=tilesize
        basey+=tilesize
    im.save("out-%d.png"%(zoomlevel,))


def gen_basic_test():
    import Image
    xs=1000
    ys=1000
    im=Image.new("RGB",(xs,ys))
    for x in xrange(0,xs):
        for y in xrange(0,ys):
            lat=80-y/float(ys)*80.0
            lon=-100.0+x/float(xs)*150.0
            elev=get_terrain_elev((lat,lon))
            e=int(elev/25.0)%255
            #print lat,lon,e
            im.putpixel((x,y),(e,e,e))
    im.save("test.png")
   


if __name__=='__main__':
    print sys.argv
    task=sys.argv[1]
    if len(sys.argv)<=2:
        dest=os.path.join(os.getenv("SWFP_DATADIR"),"tiles/elev/level")
    else:
        dest=sys.argv[2]
    if task=='test':
        gen_basic_test()        
    elif task=='refine':
        zoomlevel=8
        while zoomlevel>=0:
            refine_merc_elevmap(dest,zoomlevel)
            zoomlevel-=1
    elif task=='verify':
        verify(dest,int(sys.argv[3]))
    elif task=="create":
        create_merc_elevmap(dest+"8")
    else:
        print "Unknown command:",task
    
    
