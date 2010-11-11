from fplan.extract.parse_tma import parse_all_tma,parse_r_areas
from fplan.extract.fi_parse_tma import fi_parse_tma
from fplan.extract.parse_obstacles import parse_obstacles
from fplan.extract.fi_parse_obstacles import fi_parse_obstacles
from fplan.extract.fi_parse_restrict import fi_parse_restrictions
from fplan.extract.fi_parse_sigpoints import fi_parse_sigpoints
from fplan.extract.extract_airfields import extract_airfields
from fplan.extract.fi_extract_airfields import fi_parse_airfields
from fplan.extract.fi_extract_small_airfields import fi_parse_small_airfields
from fplan.extract.parse_sig_points import parse_sig_points
from fplan.extract.fetchdata import get_filedate
from fplan.extract.parse_aip_sup import parse_all_sups
from fplan.extract.parse_mountain_area import parse_mountain_area
from fplan.extract.fi_extract_ats_rte import fi_parse_ats_rte
import fplan.lib.remove_unused_users
import fplan.extract.fetchdata as fetchdata
from datetime import datetime,timedelta
import pickle
import os
import shutil
import time
import sys
from threading import Lock
version=2

aipdata=[]
debug=True
loaded_aipdata_cachefiledate=None
last_timestamp_check=datetime.utcnow()
lock=Lock()
def get_aipdata(cachefile="aipdata.cache",generate_if_missing=False):
    global aipdata
    global loaded_aipdata_cachefiledate
    global last_timestamp_check
    lock.acquire()
    try:
            
        if aipdata and os.path.exists(cachefile) and aipdata.get('version',None)==version:
            if datetime.utcnow()-last_timestamp_check>timedelta(0,15) and os.path.exists(cachefile):
                last_timestamp_check=datetime.utcnow()
                filestamp=get_filedate(cachefile)
                print "Timestamp of loaded aipdata: %s, Timestamp of aipdata on disk: %s"%(loaded_aipdata_cachefiledate,filestamp)
                if filestamp!=loaded_aipdata_cachefiledate:
                    try:
                        print "Loading new aipdata"
                        newaipdata=pickle.load(open(cachefile))
                        if newaipdata.get('version',None)!=version:
                            raise Exception("Bad aipdata version")
                        loaded_aipdata_cachefiledate=get_filedate(cachefile);
                        aipdata=newaipdata
                        return aipdata
                    except Exception,cause:
                        print "Tried to load new aipdata from disk, but failed"
            return aipdata
        try:
            aipdata=pickle.load(open(cachefile))
            if aipdata.get('version',None)!=version:
                raise Exception("Bad aipdata version")
            loaded_aipdata_cachefiledate=get_filedate(cachefile);
            return aipdata
        except:
            if not generate_if_missing:
                raise Exception("You must supply generate_if_missing-parameter for aip-data parsing and generation to happen")
            airspaces=[]
            airfields=[]
            sig_points=[]
            obstacles=[]
            seenpoints=dict()
            def sig_points_extend(points):
                for point in points:
                    name,pos=point['name'],point['pos']
                    samename=seenpoints.setdefault(name,[])
                    already=False
                    for s in samename:
                        if s['pos']==pos:
                            already=True
                    samename.append(point)
                    if not already:
                        sig_points.append(point)
            if 1: #finland
                airspaces.extend(fi_parse_tma())
                sig_points_extend(fi_parse_sigpoints())
                obstacles.extend(fi_parse_obstacles())
                airspaces.extend(fi_parse_ats_rte())
                fi_airfields,fi_spaces,fi_ad_points=fi_parse_airfields()
                airspaces.extend(fi_spaces)
                airspaces.extend(fi_parse_restrictions())
                airfields.extend(fi_airfields)
                airfields.extend(fi_parse_small_airfields())
            if 1: #sweden
                se_airfields,se_points=extract_airfields()
                sig_points_extend(se_points)
                airfields.extend(se_airfields)
                sig_points_extend(parse_sig_points())
                airspaces.extend(parse_all_tma())
                airspaces.extend(parse_r_areas())
                airspaces.extend(parse_mountain_area())
                
                obstacles.extend(parse_obstacles())
                
            for ad in airfields:
                if 'spaces' in ad:
                    for space in ad['spaces']:
                        pa=dict()
                        pa['name']=space['name']
                        pa['floor']=space['floor']
                        pa['ceiling']=space['ceil']
                        pa['points']=space['points']
                        pa['type']='CTR'
                        pa['freqs']=space.get('freqs',"")
                        airspaces.append(pa)
            
            aipdata=dict(
                downloaded=datetime.utcnow(),
                airspaces=airspaces,
                obstacles=obstacles,
                airfields=airfields,
                sig_points=sig_points,
                aip_sup_areas=parse_all_sups(),
                version=version
                )
            pickle.dump(aipdata,open(cachefile,"w"),-1)        
            loaded_aipdata_cachefiledate=get_filedate(cachefile);
            return aipdata
    finally:
        lock.release()
        
        
def get_airspaces():
    aipdata=get_aipdata()
    return aipdata['airspaces']
def get_aip_sup_areas():
    aipdata=get_aipdata()
    return aipdata.get('aip_sup_areas',[])
def get_obstacles():
    aipdata=get_aipdata()
    return aipdata['obstacles']
def get_airfields():
    aipdata=get_aipdata()
    return aipdata['airfields']
def get_sig_points():
    aipdata=get_aipdata()
    return aipdata['sig_points']
def get_aip_download_time():
    aipdata=get_aipdata()
    return aipdata.get('downloaded',None)
    

single_force=False
last_update=None
def run_update_iteration():
    from fplan.lib.tilegen_unithread import update_unithread
    global last_update
    global aipdata
    global single_force
    try:
        d=datetime.utcnow()
        if single_force or ((d.hour>23 or d.hour<=2) and (last_update==None or datetime.utcnow()-last_update>timedelta(0,3600*6))): #Wait until it is night before downloading AIP, and at least 6 hours since last time  
            single_force=False
            last_update=datetime.utcnow()
            #if not debug: #non-caching is just annoying
            #    fetchdata.caching_enabled=False
            aipdata=[]
            get_aipdata("aipdata.cache.new",generate_if_missing=True)
            shutil.move("aipdata.cache.new","aipdata.cache")
            print "moved new aipdata to aipdata.cache"            
            if debug:
                print "Yes exit"
                sys.exit()
            print "Now re-rendering maps"
            update_unithread()
            print "Finished re-rendering maps"
            time.sleep(2)
            print "Now deleteting old unregistered users"
            fplan.lib.remove_unused_users.run()
        else:
            print "Chose to not update aipdata. Cur hour: %d, last_update: %s, now: %s"%(d.hour,last_update,datetime.utcnow())
    except Exception,cause:
        print "aipdata-update, Exception:",cause
        raise

    
if __name__=='__main__':
    from sqlalchemy import engine_from_config
    from paste.deploy import appconfig
    from fplan.config.environment import load_environment
    conf = appconfig('config:%s'%(os.path.join(os.getcwd(),"development.ini"),))    
    load_environment(conf.global_conf, conf.local_conf)
    print sys.argv
    if not ("debug" in sys.argv):
        debug=False
    print "Debug:",debug
    time.sleep(2)
    if len(sys.argv)>1 and sys.argv[1]:
        single_force=True
    while True:
        run_update_iteration()
        time.sleep(3600)



