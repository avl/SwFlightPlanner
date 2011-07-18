from tilegen_planner import TilePlanner
import tilegen_worker
import sys
import os
import stat
from fplan.config.environment import load_environment
from paste.deploy import appconfig

def run_unithread(target_path,tma,zoomlevel=13):
    p=TilePlanner()
    #cachedir tma
    p.init(target_path,tma,zoomlevel)
    tilegen_worker.run(p)
    p.close()
    
def update_unithread(zoomlevel=13):
    if os.path.exists(os.path.join(os.getenv("SWFP_DATADIR"),"intermediate/")):
        if len([x for x in os.listdir(os.path.join(os.getenv("SWFP_DATADIR"),"intermediate/")) if x.startswith("level")]):
            if os.system("rm -rfv "+os.path.join(os.getenv("SWFP_DATADIR"),"intermediate/level*")):
                raise Exception("Couldn't clear dir")
    else:
        if os.system("mkdir -pv "+os.path.join(os.getenv("SWFP_DATADIR"),"intermediate")):
            raise Exception("Couldn't create dir")
    run_unithread(os.path.join(os.getenv("SWFP_DATADIR"),"intermediate"),"1",zoomlevel)
    for zl in xrange(zoomlevel+1):
        newpath=os.path.join(os.getenv("SWFP_DATADIR"),"intermediate/level%d"%(zl,))
        try:
            destpath=os.path.join(os.getenv("SWFP_DATADIR"),"tiles/airspace/level%d"%(zl,))
            oldsize=os.stat(destpath)[stat.ST_SIZE]
        except:
            oldsize=0            
        newsize=os.stat(newpath)[stat.ST_SIZE]
            
            
        if newsize<oldsize*0.5:
            raise Exception("Infeasible size of newly generated map data: %s. Size = %d, old size: %d"%(newpath,newsize,oldsize))
        print "Move %s (%d) -> %s (%d)"%(newpath,newsize,destpath,oldsize)
        if os.system("mv -v %s %s"%(newpath,destpath)):
            raise Exception("Couldn't move updated airspace blobs to active dir")
        if os.system("touch %s"%(destpath,)):
            raise Exception("Couldn't touch updated airspace blobs in active dir")

if __name__=='__main__':
    conf = appconfig('config:%s'%(os.path.join(os.getcwd(),"development.ini"),))    
    load_environment(conf.global_conf, conf.local_conf)
    repeatcount=1
    if len(sys.argv)>2:
        repeatcount=int(sys.argv[2])
    for x in xrange(repeatcount):
        update_unithread(int(sys.argv[1]))

