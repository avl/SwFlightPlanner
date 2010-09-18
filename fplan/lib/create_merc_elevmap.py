from struct import pack,unpack
from maptilereader import latlon_limits,merc_limits
from StringIO import StringIO
from blobfile import BlobFile
from fplan.lib import mapper
from fplan.lib.get_terrain_elev import get_terrain_elev
from itertools import product
import sys
import numpy
import Image
import md5
import os
tilesize=64

def create_merc_elevmap(dest):    
    zoomlevel=8
    limitx1,limity1,limitx2,limity2=merc_limits(zoomlevel)
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
    limitx1,limity1,limitx2,limity2=merc_limits(zoomlevel)

    tilesizemask=tilesize-1
    assert (limitx1&tilesizemask)==0
    assert (limity1&tilesizemask)==0

    srcblob=BlobFile(src+"-%d"%(srczoomlevel,),tilesize=tilesize)
    trgfile=src+"-%d"%(zoomlevel,)
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
    srcblob=BlobFile(src+"-%d"%(zoomlevel,),tilesize=tilesize)
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

if __name__=='__main__':
    print sys.argv
    task=sys.argv[1]
    if len(sys.argv)<=2:
        dest="/home/anders/saker/avl_fplan_world/elevmap.bin"
    else:
        dest=sys.argv[2]
    if task=='refine':
        zoomlevel=8
        while zoomlevel>=0:
            refine_merc_elevmap(dest,zoomlevel)
            zoomlevel-=1
    elif task=='verify':
        verify(dest,int(sys.argv[3]))
    elif task=="create":
        create_merc_elevmap(dest+"-8")
    else:
        print "Unknown command:",task
    
    
