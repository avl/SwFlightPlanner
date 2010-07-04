from fplan.extract.parse_tma import parse_all_tma,parse_r_areas
from fplan.extract.parse_obstacles import parse_obstacles
from fplan.extract.extract_airfields import extract_airfields
from fplan.extract.parse_sig_points import parse_sig_points
import pickle
import os

version=2

from threading import Lock
aipdata=[]
lock=Lock()
def get_aipdata():
    global aipdata
    lock.acquire()
    try:
        if aipdata and os.path.exists("aipdata.cache") and aipdata.get('version',None)==version:
            return aipdata
        try:
            aipdata=pickle.load(open("aipdata.cache"))
            if aipdata.get('version',None)!=version:
                raise Exception("Bad aipdata version")
        except:
            airspaces=parse_all_tma()
            airspaces.extend(parse_r_areas())
            
            airfields=extract_airfields()
            for ad in airfields:
                if 'spaces' in ad:
                    for space in ad['spaces']:
                        pa=dict()
                        pa['name']=space['name']
                        pa['floor']=space['floor']
                        pa['ceiling']=space['ceil']
                        pa['points']=space['points']
                        pa['type']='CTR'
                        pa['freqs']=''
                        airspaces.append(pa)
            
            aipdata=dict(
                airspaces=airspaces,
                obstacles=parse_obstacles(),
                airfields=airfields,
                sig_points=parse_sig_points(),
                version=version
                )
            pickle.dump(aipdata,open("aipdata.cache","w"),-1)        
        return aipdata
    finally:
        lock.release()
def get_airspaces():
    aipdata=get_aipdata()
    return aipdata['airspaces']
def get_obstacles():
    aipdata=get_aipdata()
    return aipdata['obstacles']
def get_airfields():
    aipdata=get_aipdata()
    return aipdata['airfields']
def get_sig_points():
    aipdata=get_aipdata()
    return aipdata['sig_points']
if __name__=='__main__':
    get_aipdata()
  g  
