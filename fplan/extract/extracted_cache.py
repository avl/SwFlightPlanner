from fplan.extract.parse_tma import parse_all_tma,parse_r_areas
from fplan.extract.parse_obstacles import parse_obstacles
import pickle
import os
from threading import Lock
aipdata=[]
lock=Lock()
def get_aipdata():
    global aipdata
    lock.acquire()
    try:
        if aipdata and os.path.exists("aipdata.cache"):
            return aipdata
        try:
            aipdata=pickle.load(open("aipdata.cache"))
        except:
            airspaces=parse_all_tma()
            airspaces.extend(parse_r_areas())
            aipdata=dict(
                airspaces=airspaces,
                obstacles=parse_obstacles())
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
