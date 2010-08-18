from fplan.lib.blobfile import BlobFile
import fplan.lib.mapper as mapper
import os
from datetime import datetime,timedelta
import stat

        
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


blobcache=None
last_reopencheck=datetime.utcnow()
last_mtime=0
def gettile(variant,zoomlevel,mx,my):
    global blobcache
    global last_reopencheck
    global last_mtime
    
    reopen_blobs=False
    if datetime.utcnow()-last_reopencheck>timedelta(0,60):
        path="/home/anders/saker/avl_fplan_world/tiles/airspace/level5" #used to detect if map has been updated
        mtime=os.stat(path)[stat.ST_MTIME]
        #print "mtime, level 5: ",mtime
        if mtime!=last_mtime:
            reopen_blobs=True
            last_mtime=mtime
        last_reopencheck=datetime.utcnow()    
    if blobcache==None or reopen_blobs:
        #print "Reopen blobs:",reopen_blobs
        blobcache=dict()
        variants=["airspace","plain"]
        for variant in variants:
            for zoomlevel in xrange(14):
                path="/home/anders/saker/avl_fplan_world/tiles/%s/level%d"%(
                        variant,
                        zoomlevel)
                #print "Reading: ",path
                if os.path.exists(path):
                    #print "Reopening "+path
                    blobcache[(variant,zoomlevel)]=BlobFile(path)
        
    blob=blobcache.get((variant,zoomlevel),None)
    if blob==None:
        print "Zoomlevel %d not loaded"%(zoomlevel,)
        return open("fplan/public/nodata.png").read()
    #print "Reading level: ",zoomlevel
    d=blob.get_tile(mx,my)
    if d:
        return d;
    #print "Missing tile at merc %d,%d zoom %d"%(mx,my,zoomlevel)
    return open("fplan/public/nodata.png").read()
                    

