from fplan.lib.blobfile import BlobFile
import fplan.lib.mapper as mapper
import os
from datetime import datetime,timedelta
import stat
import time
import random
from threading import Lock
import StringIO
import fplanquick.fplanquick as fplanquick
from fplanquick.fplanquick import svector
import Image
        
def latlon_limits():
    lat1=53
    lon1=3
    lat2=71.5
    lon2=31.8
    return lat1,lon1,lat2,lon2

def latlon_limits_hd():
    lat1=10
    lon1=-140
    lat2=75
    lon2=40
    return lat1,lon1,lat2,lon2

mlim={}
def merc_limits(zoomlevel,conservative=False,hd=False):
    def ints(xs): return [int(x) for x in xs]
    if (zoomlevel,conservative,hd) in mlim:
        return mlim[(zoomlevel,conservative,hd)]
    if hd:
        lat1,lon1,lat2,lon2=latlon_limits_hd()
    else:
        lat1,lon1,lat2,lon2=latlon_limits()
    limitx1,limity1=ints(mapper.latlon2merc((lat2,lon1),zoomlevel))
    limitx2,limity2=ints(mapper.latlon2merc((lat1,lon2),zoomlevel))
    if conservative:
        mlim[(zoomlevel,conservative,hd)]=(limitx1,limity1,limitx2,limity2)
        return limitx1,limity1,limitx2,limity2
    else:
        tilesize=256
        tilesizemask=tilesize-1
        limitx1&=~tilesizemask
        limity1&=~tilesizemask
        limitx2&=~tilesizemask
        limity2&=~tilesizemask
        limitx2+=tilesize
        limity2+=tilesize
        mlim[(zoomlevel,conservative,hd)]=(limitx1,limity1,limitx2,limity2)
        return limitx1,limity1,limitx2,limity2

    
blobcache=None
blobcachelock=Lock()

last_mtime_check=datetime(1970,1,1)
last_mtime=0
loaded_mtime=0

def get_mtime():
    global last_mtime_check
    global last_mtime
    if datetime.utcnow()-last_mtime_check>timedelta(0,60):
        path=os.path.join(os.getenv("SWFP_DATADIR"),"tiles/airspace/level5") #used to detect if map has been updated
        if not os.path.exists(path):
            return 0
        mtime=os.stat(path)[stat.ST_MTIME]
        last_mtime=mtime
        last_mtime_check=datetime.utcnow()
    return last_mtime


def gettile(variant,zoomlevel,mx,my,mtime=None): 
    if variant in ['plain','airspace']:
        return getmaptile(variant,zoomlevel,mx,my,mtime)
    if variant=='elev':
        return getelevtile(zoomlevel,mx,my,mtime)
    raise Exception("Unknown image variant: "+variant)
    
def getelevtile(zoomlevel,mx,my,mtime): 
    assert zoomlevel>=5   
    raw,status=getmaptile('elev',zoomlevel,mx,my,mtime)
    #print "get tile",status,len(raw)
    if status['status']!="ok":
        return open("fplan/public/nodata.png").read(),dict(status="underlying getmaptile failed: "+status['status'])
    assert type(raw)==str
    raws=[raw]
    #print "About to call colorize"
    rawimg=fplanquick.colorize_combine_heightmap(svector(raws))
    #print "colorize returned"
    if len(rawimg)==0:
        #print "Colorize found nothing"
        return open("fplan/public/nodata.png").read(),dict(status="colorize returned 0-len")
    assert len(rawimg)==256*256*3
    img=Image.fromstring("RGB",(256,256),rawimg)

    io=StringIO.StringIO()
    img.save(io,'png')
    io.seek(0)
    return io.read(),dict(status="ok")
    
def getmaptile(variant,zoomlevel,mx,my,mtime=None):
    """
    Some explanation is in order for the mtime parameter:
    If it is supplied, the blobfiles are reloaded if mtime
    given does not match the mtime of the blobs loaded.
    (mtime = MTIME attribute of level5-file in airspace set).
    If mtime is not set, the blobs are never reloaded.
    """
    #print "Accessing blobs %s for zoomlevel %s"%(variant,zoomlevel)
    global blobcache
    global last_reopencheck
    global loaded_mtime
    
    reopen_blobs=False
    mtime=get_mtime()

    
    #print "mtime, level 5: ",mtime
    blobcachelock.acquire()
    #print "Gettile: mtime: %d, last_mtime: %d, loaded mtime: %d"%(mtime,last_mtime,loaded_mtime)
    try:
        if mtime!=None and mtime!=loaded_mtime:
            reopen_blobs=True    
        if blobcache==None or reopen_blobs:
            #print "Reopen blobs:",reopen_blobs
            blobcache=dict()
            loadvariants=["airspace","plain",'elev']
            for loadvariant in loadvariants:
                for loadzoomlevel in xrange(14):
                    path=os.path.join(os.getenv("SWFP_DATADIR"),"tiles/%s/level%d"%(
                            loadvariant,
                            loadzoomlevel))
                    #print "Reading: ",path
                    if os.path.exists(path):
                        #print "Reopening "+path
                        ltilesize=256
                        if loadvariant=="elev": ltilesize=256
                        blobcache[(loadvariant,loadzoomlevel)]=BlobFile(path,tilesize=ltilesize)
        loaded_mtime=mtime
    finally:
        blobcachelock.release()        
    
    blob=blobcache.get((variant,zoomlevel),None)
    
    #print "Got blob for zoomlevel: %d (=%d)"%(zoomlevel,blob.zoomlevel)
    if blob==None:
        print "Zoomlevel %d not loaded"%(zoomlevel,)
        return open("fplan/public/nodata.png").read(),dict(status="missing zoomlevel")
    #print "Reading tile: ",mx,my,zoomlevel
    d=blob.get_tile(mx,my)
    if d:
        return d,dict(status="ok")
    print "Missing tile at merc %d,%d zoom %d"%(mx,my,zoomlevel)
    return open("fplan/public/nodata.png").read(),dict(status="missing tile")
                    

