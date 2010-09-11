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
    if os.path.exists("/home/anders/saker/avl_fplan_world/intermediate/"):
        if os.system("rm -rfv /home/anders/saker/avl_fplan_world/intermediate/level*"):
            raise Exception("Couldn't clear dir")
    else:
        if os.system("mkdir -pv /home/anders/saker/avl_fplan_world/intermediate"):
            raise Exception("Couldn't create dir")
    run_unithread("/home/anders/saker/avl_fplan_world/intermediate","1",zoomlevel)
    for zl in xrange(zoomlevel+1):
        newpath="/home/anders/saker/avl_fplan_world/intermediate/level%d"%(zl,)
        try:
            destpath="/home/anders/saker/avl_fplan_world/tiles/airspace/level%d"%(zl,)
            oldsize=os.stat(destpath)[stat.ST_SIZE]
        except:
            oldsize=0            
        newsize=os.stat(newpath)[stat.ST_SIZE]
        for openfd in os.listdir("/proc/self/fd"):
            try:
                openf=os.readlink("/proc/self/fd/"+openfd)
            except:
                continue
            if openf.count("avl_fplan_world/intermediate") or \
                openf.count("avl_fplan_world/tiles/airspace"):
                raise Exception("Unexpected open file: %s - %s"%(openfd,openf))
            
            
        if newsize<oldsize*0.7:
            raise Exception("Infeasible size of newly generated map data: %s. Size = %d, old size: %d"%(newpath,newsize,oldsize))
        print "Move %s (%d) -> %s (%d)"%(newpath,newsize,destpath,oldsize)
        if os.system("mv -v %s %s"%(newpath,destpath)):
            raise Exception("Couldn't move updated airspace blobs to active dir")

if __name__=='__main__':
    conf = appconfig('config:%s'%(os.path.join(os.getcwd(),"development.ini"),))    
    load_environment(conf.global_conf, conf.local_conf)

    update_unithread(int(sys.argv[1]))

