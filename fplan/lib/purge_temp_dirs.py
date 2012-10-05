import os
import os.path
import time
def purge_all_old_basic():
    print "Purging temporary directories"
    tmppath=os.path.join(os.getenv("SWFP_DATADIR"),"aip")
    purge_all_old(tmppath)
    #tmppath=os.path.join(os.getenv("SWFP_DATADIR"),"adcharts")
    #purge_all_old(tmppath)
    #tmppath=os.path.join(os.getenv("SWFP_DATADIR"),"aiptext")
    #purge_all_old(tmppath)

def purge_all_old(tempdir,maxage=86400*30*2):
    now=time.time()        
    print "Puring old stuff in ",tempdir
    for root, dirs, files in os.walk(tempdir, topdown=False):
        for name in files:
            p=os.path.join(root, name)
            age=now-os.path.getmtime(p)
            print p,"age",age,"maxage",maxage
            if age>maxage:
                print "Removing",p,"age:",age,"(=",age/86400," days)"                
                os.remove(p)
