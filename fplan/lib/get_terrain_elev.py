from struct import unpack
from math import floor
import math

terrain_files=[]

def init_terrain():
    terrain_files.append(dict(
        fname="/home/anders/saker/avl_fplan_world/srtp/E020N90.DEM",
        west=20.0,#-1e-5,
        east=60.0,
        north=90.0,
        south=40.0))
    terrain_files.append(dict(
        fname="/home/anders/saker/avl_fplan_world/srtp/W020N90.DEM",
        west=-20.0,
        east=20.0,#+1e-5,
        north=90.0,
        south=40.0))


base_xres=4800
base_yres=6000
res_for_level=dict()
def initreslevel():
    xres=base_xres
    yres=base_yres
    for level in xrange(15):
        res_for_level[level]=(xres,yres)
        xres/=2
        yres/=2    
    
initreslevel()    
        
def get_terrain_elev_in_box_approx(latlon,nautmiles):
    pixels=nautmiles/0.5
    lat,lon=latlon
    ypixels=pixels
    f=math.cos(lat*math.pi/180.0)
    if f<0.1: f=0.1
    xpixels=pixels/f
    resolutionlevel=0
    while ypixels>5:
        ypixels/=2
        xpixels/=2
        resolutionlevel+=1
    return get_terrain_elev(latlon,resolutionlevel,(xpixels,ypixels))
    
def get_terrain_elev(latlon,resolutionlevel=0,samplebox=(1,1)):
    if resolutionlevel>12:
        raise Exception("Invalid (too high) resolution level")
    global terrain_files
    lat,lon=latlon
    if terrain_files==[]:
        init_terrain()
    elevs=[-9999]
    for terr in terrain_files:        
        if lat>=terr['south'] and lat<=terr['north'] and lon>=terr['west'] and lon<=terr['east']:
            logicalxres,logicalyres=4800,6000#res_for_level[resolutionlevel]            
            xres,yres=res_for_level[resolutionlevel]            
            print "reading lat/lon:",lat,lon,"size:",xres,yres
            y=int(floor(float(logicalyres)*(terr['north']-lat)/float(terr['north']-terr['south'])))
            x=int(floor(float(logicalxres)*(lon-terr['west'])/float(terr['east']-terr['west'])))
            for i in xrange(resolutionlevel):
                x/=2
                y/=2
            if resolutionlevel==0:
                filename=terr['fname']
            else:
                filename="%s-%d"%(terr['fname'],resolutionlevel)
            x1=x-samplebox[0]/2
            x2=x1+samplebox[0]
            y1=y-samplebox[1]/2
            y2=y1+samplebox[1]
            f=open(filename)
            for y in xrange(y1,y2):
                for x in xrange(x1,x2):
                    print "reading from ",filename,x,y
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
                    elevs.append(elev/0.3048)
    if len(elevs)==1:
        print "Nothing found",lat,lon
    return max(elevs)

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
   
