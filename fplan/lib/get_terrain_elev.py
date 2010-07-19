from struct import unpack

terrain_files=[]

def init_terrain():
    terrain_files.append(dict(
        fhandle=open("/home/anders/saker/avl_fplan_world/srtp/E020N90.DEM"),
        west=20.0,#-1e-5,
        east=60.0,
        north=90.0,
        south=40.0))
    terrain_files.append(dict(
        fhandle=open("/home/anders/saker/avl_fplan_world/srtp/W020N90.DEM"),
        west=-20.0,
        east=20.0,#+1e-5,
        north=90.0,
        south=40.0))

    

def get_terrain_elev(latlon):
    global terrain_files
    lat,lon=latlon
    if terrain_files==[]:
        init_terrain()    
    for terr in terrain_files:        
        if lat>=terr['south'] and lat<=terr['north'] and lon>=terr['west'] and lon<=terr['east']:
            y=int(6000.0*(terr['north']-lat)/float(terr['north']-terr['south']))
            x=int(4800.0*(lon-terr['west'])/float(terr['east']-terr['west']))
            f=terr['fhandle']
            #print "reading from ",x,y
            if x>=4800: x=4800-1
            if x<0: x=0
            if y>=6000: y=6000-1
            if y<0: y=0
            idx=int(y*4800+x)
            if idx<0: idx=0
            if idx>=4800*6000: idx=4800*6000-1
            f.seek(2*idx)
            bytes=f.read(2)
            elev,=unpack(">h",bytes)
            return elev/0.3048
    print "Nothing found",lat,lon
    return -9999

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
   
