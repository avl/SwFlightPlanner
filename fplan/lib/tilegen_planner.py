#!/usr/bin/python
#lifted from a mapnik sample
import mapnik
import sys, os, tempfile
import fplan.lib.mapper as mapper
import math
import Pyro.core
import Pyro.naming
from struct import pack

from blobfile import BlobFile
from maptilereader import latlon_limits,merc_limits
        

def generate_work_packages(tma,blobs,cachedir):
    lat1,lon1,lat2,lon2=latlon_limits()
    lat1=float(lat1)
    lat2=float(lat2)
    lon1=float(lon1)
    lon2=float(lon2)
    
    meta=0 #50 Change back to if using mapnik
    if meta==0:
        print "\n\n\n\n\n=====================================================================\nWARNING! meta==0!!!!!!!!!!!!!!!!!!!!!!!!!\n\n\n"
    for zoomlevel in xrange(7):
        maxy=mapper.max_merc_y(zoomlevel)
        maxx=mapper.max_merc_x(zoomlevel)
        limitsx1,limitsy1,limitsx2,limitsy2=merc_limits(zoomlevel)
        assert limitx2>limitx1
        assert limity2>limity1
        print "Limits: %f,%f - %f,%f"%(limitx1,limity1,limitx2,limity2)
        blobs[zoomlevel]=BlobFile(os.path.join(cachedir,"level"+str(zoomlevel)),zoomlevel,
            limitx1,limity1,limitx2,limity2,'w')
            
        for my1 in xrange(limity1,limity2,2048):
            for mx1 in xrange(limitx1,limitx2,2048):
                
                                
                mx2=mx1+2048
                my2=my1+2048
                if my2>maxy:
                    my2=maxy
                if mx2>maxx:
                    mx2=maxx
                if my1>=meta:
                    metay1=meta
                else:
                    metay1=0
                if mx1>=meta:
                    metax1=meta
                else:
                    metax1=0
                if my2<=maxy-meta:
                    metay2=meta
                else:
                    metay2=0
                if mx2<=maxx-meta:
                    metax2=meta
                else:
                    metax2=0
                    
                latb,lona=mapper.merc2latlon((mx1,my1),zoomlevel)
                lata,lonb=mapper.merc2latlon((mx2,my2),zoomlevel)
                if latb<lat1: continue
                if lata>lat2: continue
                if lonb<lon1: continue                
                if lona>lon2: continue                                
                    
                coord=(zoomlevel,mx1,my1,mx2,my2)

                
                yield (coord,dict(
                           checkedout=None,
                           metax1=metax1,
                           metay1=metay1,
                           metax2=metax2,
                           metay2=metay2,
                           render_tma=tma
                           ))
    print "Finished initializing work"
class TilePlanner(Pyro.core.ObjBase):
    def init(self,cachedir,tma):
        self.tma=int(tma)
        self.blobs=dict()
        self.work=dict(generate_work_packages(self.tma,self.blobs,cachedir))
        self.inprog=dict()
        self.cachedir=cachedir
        
    def get_work(self):
        if len(self.work)==0:
            return None #Finished
        coord,descr=self.work.popitem()
        self.inprog[coord]=descr
        print "Handing out work: %s"%(coord,)
        return (coord,descr)
    def get_cachedir(self):
        return self.cachedir
    def finish_work(self,coord,data):
        print "finish_work(%s,%d)"%(coord,len(data))
        if not coord in self.inprog: 
            print "finish_work was called with unknown work package: %s of size %d bytes"%(coord,len(data))
        self.inprog.pop(coord)
        cprog=len(self.inprog)
        ctot=len(self.work)
        zoom,x1,y1,x2,y2=coord
        for zoomlevel,x,y,pngdata in data:
            assert zoomlevel==zoom
            self.blobs[zoomlevel].add_tile(x,y,pngdata)
        print "Work left: %d (in progress: %d)"%(cprog+ctot,cprog)
        if cprog+ctot==0:
            print "Finished! You may exit this program now"
            for blob in self.blobs.values():
                blob.close()

    def giveup_work(self,coord):
        descr=self.inprog.pop(coord)
        self.work[coord]=descr
        
daemon=Pyro.core.Daemon()
ns=Pyro.naming.NameServerLocator().getNS()
daemon.useNameServer(ns)
p=TilePlanner()
p.init(sys.argv[1],sys.argv[2])
uri=daemon.connect(p,"planner")
daemon.requestLoop()

