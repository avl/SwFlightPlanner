from struct import unpack
from math import floor
import math
from fplan.lib import mapper
import os
import maptilereader
import struct

#terrain_files=[]
#
#def init_terrain():
#    terrain_files.append(dict(
#        fname=os.path.join(os.getenv("SWFP_DATADIR"),"srtp/E020N90.DEM"),
#        west=20.0,#-1e-5,
#        east=60.0,
#        north=90.0,
#        south=40.0))
#    terrain_files.append(dict(
#        fname=os.path.join(os.getenv("SWFP_DATADIR"),"srtp/W020N90.DEM"),
#        west=-20.0,
#        east=20.0,#+1e-5,
#        north=90.0,
#        south=40.0))


#base_xres=4800
##base_yres=6000
#res_for_level=dict()
#def initreslevel():
#    xres=base_xres
#    yres=base_yres
#    for level in xrange(15):
#        res_for_level[level]=(xres,yres)
#        xres/=2
#        yres/=2    
#    
#initreslevel()    

     
def get_terrain_elev_in_box_approx(latlon,nautmiles):
    #nautmiles/=2
    zoomlevel=8
    merc_=mapper.latlon2merc(latlon,zoomlevel)
    merc=(int(merc_[0]),int(merc_[1]))
    pixels=mapper.approx_scale(merc, zoomlevel, nautmiles)
    #print "Num pixels on zoomlevel 8",pixels," naut",nautmiles
    del merc
    del merc_
    while pixels>4 and zoomlevel>0:
        zoomlevel-=1
        pixels/=2
        #print "Pixels on zoom",zoomlevel,": ",pixels
    pixels=int(pixels+0.5)
    if pixels<=1: pixels=1
    if zoomlevel>=8: zoomlevel=8

    merc_=mapper.latlon2merc(latlon,zoomlevel)
    merc=(int(merc_[0]),int(merc_[1]))
    #print "Getting terrain zoomlevel ",zoomlevel
    return get_terrain_elev_merc(merc,zoomlevel,(pixels,pixels))
    
def get_terrain_elev(latlon,zoomlevel=8):
    if zoomlevel>=8: zoomlevel=8
    if zoomlevel<=0: zoomlevel=0
    merc=mapper.latlon2merc(latlon,zoomlevel)
    ret=int(get_terrain_elev_merc(merc,zoomlevel))
    return ret
    
elev_tilesize=256
    
def get_terrain_elev_merc(merc,zoomlevel,samplebox=(1,1)):
    if zoomlevel>8:
        raise Exception("Invalid (too high) resolution level")
    if zoomlevel<0:
        raise Exception("Invalid (too low) resolution level")
    merc=(int(merc[0]),int(merc[1]))
    tilex,tiley=None,None
    heights=[]
    for y in xrange(merc[1],merc[1]+samplebox[1]):
        for x in xrange(merc[0],merc[0]+samplebox[0]):
            mx=x&(~(elev_tilesize-1))
            my=y&(~(elev_tilesize-1))
            if mx!=tilex or my!=tiley:
                raw,status=maptilereader.getmaptile('elev',zoomlevel,mx,my)
                tilex=mx
                tiley=my
                if status.get('status','nok')!="ok":
                    return 9999
            dx=x-mx
            dy=y-my
            assert not (dx<0 or dy<0 or dx>=elev_tilesize or dy>=elev_tilesize)
            #for rownr in range(elev_tilesize):
            #    row=[]
            #    for colnr in range(elev_tilesize):
            #        idx=4*(elev_tilesize*rownr+colnr)
            #        rawheight=raw[idx:idx+2]
            #        height=struct.unpack(">h",rawheight)[0]/100
            #        row.append(chr(ord('0')+height%10))
            #    print "#"+str(rownr)+": "+"".join(row)

            idx=2*(elev_tilesize*dy+dx)
            rawheight=raw[idx:idx+2]
            #minheight=struct.unpack(">h",rawheight[0:2])[0]
            maxheight=struct.unpack(">h",rawheight[0:2])[0]
            #print "Minheight,maxheight",minheight,maxheight
            height=maxheight
            #print "Adding x,y %d,%d dx,dy %d,%d : h: %d"%(
            #    x,y,dx,dy,height)
            heights.append(height)
    #print "Returning",(heights)
    return max(heights)

if __name__=='__main__':
    import Image
    xs=100
    ys=100
    im=Image.new("RGB",(xs,ys))
    for x in xrange(0,100):
        for y in xrange(0,100):
            lat=70-y/float(ys)*5.0
            lon=18.0+x/float(xs)*5.0
            elev=get_terrain_elev((lat,lon))
            e=int(elev/8.0)%255
            #print lat,lon,e
            im.putpixel((x,y),(e,e,e))
    im.save("test.png")
   
