from fplan.lib.blobfile import BlobFile
import fplan.lib.mapper as mapper
import os
from datetime import datetime,timedelta
import stat
import time
import random
from threading import Lock
        
def latlon_limits():
    limits="55,10,69,24"
    lat1,lon1,lat2,lon2=limits.split(",")
    return float(lat1),float(lon1),float(lat2),float(lon2)

def merc_limits(zoomlevel,conservative=False):
    def ints(xs): return [int(x) for x in xs]
    lat1,lon1,lat2,lon2=latlon_limits()
    limitx1,limity1=ints(mapper.latlon2merc((lat2,lon1),zoomlevel))
    limitx2,limity2=ints(mapper.latlon2merc((lat1,lon2),zoomlevel))
    if conservative:
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
        return limitx1,limity1,limitx2,limity2

def get_tiles_timestamp():
    if blobcachestamp==None:
        gettile("plain",0,0,0) #Just to force initialization of blobcaches
        if blobcachestamp==None:
            return datetime(1970,1,1)
    return blobcachestamp
    
blobcache=None
blobcachelock=Lock()
blobcachestamp=None
last_reopencheck=datetime.utcnow()
last_mtime=0
def gettile(variant,zoomlevel,mx,my):
    #print "Accessing blobs %s for zoomlevel %s"%(variant,zoomlevel)
    global blobcache
    global last_reopencheck
    global last_mtime
    global blobcachestamp
    reopen_blobs=False
    if datetime.utcnow()-last_reopencheck>timedelta(0,60):
        path="/home/anders/saker/avl_fplan_world/tiles/airspace/level5" #used to detect if map has been updated
        mtime=os.stat(path)[stat.ST_MTIME]
        #print "mtime, level 5: ",mtime
        if mtime!=last_mtime:
            reopen_blobs=True
            last_mtime=mtime
        last_reopencheck=datetime.utcnow()    

    blobcachelock.acquire()
    try:
        if blobcache==None or reopen_blobs:
            #print "Reopen blobs:",reopen_blobs
            blobcache=dict()
            stamps=[0]
            loadvariants=["airspace","plain"]
            for loadvariant in loadvariants:
                for loadzoomlevel in xrange(14):
                    path="/home/anders/saker/avl_fplan_world/tiles/%s/level%d"%(
                            loadvariant,
                            loadzoomlevel)
                    #print "Reading: ",path
                    if os.path.exists(path):
                        stamps.append(os.stat(path)[stat.ST_MTIME])
                        #print "Reopening "+path
                        blobcache[(loadvariant,loadzoomlevel)]=BlobFile(path)
            blobcachestamp=datetime.utcfromtimestamp(max(stamps))
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
                    

