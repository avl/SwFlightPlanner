import mapper
import Image
import StringIO
import maptilereader

def get_big_map_img(merc,size,zoomlevel):
    merc=(int(merc[0]),int(merc[1]))
    size=(int(size[0]),int(size[1]))
    sx1=merc[0]&(~255)
    sy1=merc[1]&(~255)
    sx2=merc[0]+size[0]
    sy2=merc[1]+size[1]
    nsize=(sx2-sx1,sy2-sy1)
    
    im=Image.new("RGB",nsize)
    for i in xrange(sx1,sx2,256):
        for j in xrange(sy1,sy2,256):
            rawtile,tilemeta=maptilereader.gettile("airspace",zoomlevel,i,j)
            io=StringIO.StringIO(rawtile)
            io.seek(0)
            sub=Image.open(io)
            im.paste(sub,(i-sx1,j-sy1,i+256-sx1,j+256-sy1))
    cp=im.crop((merc[0]-sx1,merc[1]-sy1,nsize[0],nsize[1]))
    assert cp.size==size
    return cp
    


def get_png(width,height,ll1,ll2,ll3,ll4):
    """
    Orientation of lls:
    
    ll1----------ll4
    |             |
    |             |
    |             |
    |             |
    ll2----------ll3
    """
    zl=13
    while zl>=5:
        pp1=mapper.latlon2merc(ll1,zl)
        pp2=mapper.latlon2merc(ll2,zl)
        pp3=mapper.latlon2merc(ll3,zl)
        pp4=mapper.latlon2merc(ll4,zl)
        pps=[pp1,pp2,pp3,pp4]
        xs=[t[0] for t in pps]
        ys=[t[1] for t in pps]
        x1=min(xs)
        x2=max(xs)
        y1=min(ys)
        y2=max(ys)
        
        ysize=(y2-y1)
        xsize=(x2-x1)
        if xsize>=2*width or ysize>=2*height:
            zl-=1
        else:
            break                        
    
    big=get_big_map_img((x1,y1),(x2-x1,y2-y1),zl)
    qs=[]
    for pp in pps:
        x,y=pp
        o=[x-x1,y-y1]
        qs.extend(o)
        
    res=big.transform((width,height),
        Image.QUAD,
        tuple(qs))
                  
    return res


    