
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
from fplan.extract.fetchdata import get_filedate,is_devcomp
import fplan.extract.extract_cities as extract_cities
from fplan.extract.parse_aip_sup import parse_all_sups
from fplan.extract.parse_mountain_area import parse_mountain_area
from fplan.extract.fi_extract_ats_rte import fi_parse_ats_rte
from fplan.lib.bbtree import BBTree
from pyshapemerge2d import Line,Vertex,Polygon,vvector
from fplan.lib.bsptree import BspTree,BoundingBox
import fplan.lib.remove_unused_users
import fplan.lib.delete_old_notams
import fplan.lib.mapper as mapper
import fplan.extract.fetchdata as fetchdata
from datetime import datetime,timedelta
from fplan.extract.de_parse import parse_denmark

from fplan.extract.ee_parse_tma import ee_parse_tma
from fplan.extract.ev_parse_tma import ev_parse_tma,ev_parse_r,ev_parse_obst
from fplan.extract.ee_parse_restrictions import ee_parse_restrictions

import pickle
import os
import shutil
import time
import sys
from threading import Lock
version=2

aipdata=None
aipdatalookup=None
debug=True
loaded_aipdata_cachefiledate=None
last_timestamp_check=datetime.utcnow()
lock=Lock()

def gen_bsptree_lookup(data):
    r=dict()
    
    lookup_points=['obstacles',
             'airfields',
             'sig_points']
    for look in lookup_points:
        items=data.get(look,None)
        if True:
            bspitems=[BspTree.Item(
                    mapper.latlon2merc(mapper.from_str(item['pos']),13),item) for
                    item in items]
            #print "Items for bsptree",items
            bsp=BspTree(bspitems)   
            #assert len(bsp.getall())==len(items)
            #after=sorted(set(x['name'] for x in bsp.getall()))
            #before=sorted(set(x['name'] for x in obsts))
            #print after,"\n-------------------\n\n",before
            #assert after==before
            #print "same before as after"
            r[look]=bsp
    del item
    del items
    del bspitems
    del bsp
    
    
    lookup_spaces=['airspaces']
    for look in lookup_spaces:
        spaces=data.get(look,None)
        if spaces:
            bbitems=[]
            zoomlevel=13
            for space in spaces:
                poly_coords=[]
                bb=BoundingBox(1e30,1e30,-1e30,-1e30)
                for coord in space['points']:
                    x,y=mapper.latlon2merc(mapper.from_str(coord),zoomlevel)
                    bb.x1=min(bb.x1,x)
                    bb.x2=max(bb.x2,x)
                    bb.y1=min(bb.y1,y)
                    bb.y2=max(bb.y2,y)
                    poly_coords.append(Vertex(int(x),int(y)))
                if len(poly_coords)<3:
                    continue
                poly=Polygon(vvector(poly_coords))
                #print "Item:",space
                bbitems.append(
                    BBTree.TItem(bb,(poly,space)))
                                
                #if poly.is_inside(Vertex(int(px),int(py))):
                #    insides.append(space)
            
            
            bbt=BBTree(bbitems,0.5)
            r[look]=bbt       
    
    return r
            
                          
def get_aipdata(cachefile="aipdata.cache",generate_if_missing=False):
    global aipdata
    global aipdatalookup
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
                        newaipdatalookup=gen_bsptree_lookup(newaipdata)
                        aipdata,aipdatalookup=newaipdata,newaipdatalookup
                        
                        return aipdata
                    except Exception,cause:
                        print "Tried to load new aipdata from disk, but failed"
            return aipdata
        try:
            aipdata=pickle.load(open(cachefile))
            aipdatalookup=gen_bsptree_lookup(aipdata)
            if aipdata.get('version',None)!=version:
                raise Exception("Bad aipdata version")
            loaded_aipdata_cachefiledate=get_filedate(cachefile);
            return aipdata
        except Exception,cause:
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
            if not is_devcomp() or True: #estonia
                airspaces.extend(ee_parse_restrictions())
                airspaces.extend(ee_parse_tma())
            if not is_devcomp() or True: #latvia
                #airspaces.extend(ee_parse_restrictions())
                airspaces.extend(ev_parse_tma())
                airspaces.extend(ev_parse_r())
                obstacles.extend(ev_parse_obst())
                
            if not is_devcomp() or True: #denmark
                denmark=parse_denmark()
                airspaces.extend(denmark['airspace'])
                airfields.extend(denmark['airfields'])
            if not is_devcomp() or True: #finland
                airspaces.extend(fi_parse_tma())
                sig_points_extend(fi_parse_sigpoints())
                obstacles.extend(fi_parse_obstacles())
                airspaces.extend(fi_parse_ats_rte())
                fi_airfields,fi_spaces,fi_ad_points=fi_parse_airfields()
                airspaces.extend(fi_spaces)
                airspaces.extend(fi_parse_restrictions())
                airfields.extend(fi_airfields)
                airfields.extend(fi_parse_small_airfields())
            if not is_devcomp() or True: #sweden
                se_airfields,se_points=extract_airfields()
                sig_points_extend(se_points)
                airfields.extend(se_airfields)
                sig_points_extend(parse_sig_points())
                airspaces.extend(parse_all_tma())
                airspaces.extend(parse_r_areas())
                airspaces.extend(parse_mountain_area())
                
                obstacles.extend(parse_obstacles())
            #cities    
            sig_points.extend(extract_cities.get_cities())
            
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
            
            if not is_devcomp() or False: #sweden
                sup_areas,sup_hours=parse_all_sups()
            else:
                sup_areas=[]
                sup_hours=[]
            aipdata=dict(
                downloaded=datetime.utcnow(),
                airspaces=airspaces,
                obstacles=obstacles,
                airfields=airfields,
                sig_points=sig_points,
                aip_sup_areas=sup_areas,
                se_aip_sup_hours=sup_hours,
                version=version
                )
            aipdatalookup=gen_bsptree_lookup(aipdata)
            pickle.dump(aipdata,open(cachefile,"w"),-1)        
            loaded_aipdata_cachefiledate=get_filedate(cachefile);
            return aipdata
    finally:
        lock.release()
        
        
def get_airspaces():
    aipdata=get_aipdata()
    return aipdata['airspaces']

def get_se_aip_sup_hours_url():
    aipdata=get_aipdata()
    return aipdata.get('se_aip_sup_hours','http://www.lfv.se/sv/FPC/IAIP/AIP-SUP/')

def get_airspaces_in_bb(bb):
    get_aipdata()
    for item in aipdatalookup['airspaces'].overlapping(bb):
        yield item.payload #tuple of (Polygon,Airspace-dict)

def get_aip_sup_areas():
    aipdata=get_aipdata()
    return aipdata.get('aip_sup_areas',[])

def get_obstacles():
    aipdata=get_aipdata()
    return aipdata['obstacles']
def get_obstacles_in_bb(bb):
    get_aipdata()
    for item in aipdatalookup['obstacles'].findall_in_bb(bb):
        yield item.val
def get_sig_points():
    aipdata=get_aipdata()
    return aipdata['sig_points']
def get_sig_points_in_bb(bb):
    get_aipdata()
    for item in aipdatalookup['sig_points'].findall_in_bb(bb):
        yield item.val

def get_airfields_in_bb(bb):
    get_aipdata()
    for item in aipdatalookup['airfields'].findall_in_bb(bb):
        yield item.val
        
def get_airfields():
    aipdata=get_aipdata()
    return aipdata['airfields']
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
            aipdata=None
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
            fplan.lib.delete_old_notams.run()
        else:
            print "Chose to not update aipdata. Cur hour: %d, last_update: %s, now: %s"%(d.hour,last_update,datetime.utcnow())
    except Exception,cause:
        print "aipdata-update, Exception:",repr(cause)
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



