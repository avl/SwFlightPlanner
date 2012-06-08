from datetime import datetime,timedelta
import re
from threading import Lock
import json
from pyshapemerge2d import Line,Vertex,Polygon,vvector
import sqlalchemy as sa
from fplan.model import meta,CustomSet,CustomSets
import mapper
from bsptree import BoundingBox,BspTree
from bbtree import BBTree
import traceback

from typecolor import typecolormap

def val_str(p,key,log):
    if not key in p:
        log.append("Missing key '%s' in object: %s"%(key,p))
        return False
    x=p[key]
    if type(x) in[str,unicode]:
        return True
    log.append("Key %s must be a string, not %s"%(key,repr(x)))
    return False

def val_float(p,key,log):
    if not key in p:
        log.append("Missing key '%s' in object: %s"%(key,p))
        return False
    x=p[key]
    if type(x) in [float,int]:
        return True
    if type(x) in [str,unicode]:
        try:
            x=float(x)
            p[key]=x
            return True
        except:
            log.append("Key %s must be a number, not %s"%(key,repr(x)))
            return False
    log.append("Key %s must be a number, not %s"%(key,repr(x)))
    return False
    
def val_pos(p,key,log):
    if not key in p:
        log.append("Missing key '%s' in object: %s"%(key,p))
        return False
    x=p[key]
    if not type(x) in[str,unicode]:
        log.append("Key %s must be a string representing position, not %s"%(key,repr(x)))
        return False
    try:
        pos=mapper.anyparse(x)
        p[key]=pos
        return True
    except Exception,cause:
        log.append("Couldn't parse position: %s"%(cause,))
        return False

def optval_date(x,log):
    if not 'date' in x: return
    d=x['date']
    try:
        x['date']=datetime.strptime(d.rstrip("Z").rstrip("z"), "%Y-%m-%dT%H:%M:%S")
    except:
        try:
            x['date']=datetime.strptime(d, "%Y-%m-%dT%H:%M:%S.%fZ")
        except Exception,cause:
            log.append(cause.message)
            return False
    return True
            
    
def validate_point(point,pointtype,log):
    ploglen=len(log)
    optval_date(point,log)
    if pointtype=='sigpoints':
        val_str(point,'name',log)
        val_pos(point,'pos',log)
        val_str(point,'kind',log)        
        return ploglen==len(log)
    if pointtype=='airfields':
        val_str(point,'icao',log)
        point['icao']=point['icao'].upper()
        if len(point['icao'])!=4:
            log.append(u"ICAO code must be 4 letters, not: %s"%(point['icao'],))
        val_str(point,'name',log)
        val_pos(point,'pos',log)
        if val_float(point,'elev',log):
            point['elev']=int(point['elev'])
        return ploglen==len(log)
    
    if pointtype=='obstacles':
        val_float(point,'elev',log)
        val_float(point,'height',log)
        val_str(point,'kind',log)
        if 'lighting' in point:
            val_str(point,'lighting',log)
        val_str(point,'name',log)
        val_pos(point,'pos',log)        
        return ploglen==len(log)
    log.append("Unknown point type: %s"%(pointtype,))
    return False

def val_alt(space,key,log):
    if not key in space:
        log.append("Missing key '%s' in object: %s"%(key,space))
        return False
    x=space[key]
    try:
        elev=mapper.parse_elev(x)        
    except:
        log.append("Couldn't parse altitude: %s"%(x,))
        return False
    return True
def val_freqs(space,key,log):
    if not key in space:
        log.append("Missing key '%s' in object: %s"%(key,space))
        return False
    x=space[key]
    if not type(x) in [list,tuple]:
        log.append("freqs must be a list of callsign/frequency pairs")
        return False
    for idx,item in enumerate(list(x)):
        if (not type(item) in [list,tuple]) or len(item)!=2:
            log.append("freqs must be a list of callsign/frequency pairs")
            return False
        callsign,freq=item
        if not type(callsign) in [str,unicode]:
            log.append("Callsign must be a string, not %s"%(callsign,))
            return False
        if not type(freq) in [float,int]:
            freqmhz,=re.match(r"\s*(\d{3}\.\d{1,3})\s*(?:Mhz)?",freq)
            x[idx]=(callsign,float(freqmhz))
    return True
def val_area(space,key,log):
    if not key in space:
        log.append("Missing key '%s' in object: %s"%(key,space))
        return False
    areatext=space[key]
    try:
        points=mapper.parse_coord_str(areatext)
        space[key]=points
        return True
    except Exception,cause:
        log.append("Couldn't parse area: %s"%(areatext,))
        return False
    
    
    
def validate_airfield_space(ad,log,spaces):
    if 'spaces' in ad:
        for space in ad['spaces']:
            validate_space(space,'airspaces',log)
        spaces.extend(ad['spaces'])
    
        
def validate_space(space,spacetype,log):
    ploglen=len(log)
    if spacetype=='airspaces':
        optval_date(space,log)
        val_str(space,'name',log)
        val_alt(space,'floor',log)
        val_alt(space,'ceiling',log)
        val_area(space,'points',log)
        val_freqs(space,'freqs',log)
        val_str(space,'type',log)
        if not space['type'] in typecolormap:
            log.append("Airspace type must be one of: %s"%(typecolormap.keys()))
        
        return len(log)==ploglen
    
    log.append("Unknown space type: %s"%(spacetype,))
    return False

class UserData(object):
    def have_any(self):
        return not self.empty
    def __init__(self,user,orders=None):
        print "Loading userdata for ",user
        self.user=user
        self.log=[]
        self.points=dict()
        self.spaces=dict()
        self.pointslookup=dict()
        self.spaceslookup=dict()
        self.empty=True
        
        zoomlevel=13
        pointtypes=['obstacles','airfields','sigpoints']
        spacestypes=['airspaces','firs']
        
        for pointtype in pointtypes:
            self.points[pointtype]=[]
        for spacetype in spacestypes:
            self.spaces[spacetype]=[]
            
        if orders==None:
            orders=[]    
            for csets in meta.Session.query(CustomSets).filter(CustomSets.user==user).all():
                customs=list(meta.Session.query(CustomSet).filter(sa.and_(                                                                          
                            CustomSet.user==user,CustomSet.setname==csets.setname,CustomSet.version==csets.active)).all())
                orders.extend(customs)
            
            
        for custom in orders:
            try:
                print "Found custom set:",custom.setname
                print "Found active custom set:",custom.setname,custom.version
                print "Data:"
                print "------------------"
                print custom.data
                data=json.loads(u"".join([x for x in custom.data.split("\n") if not x.strip().startswith("#")]).encode('utf8'))
                if type(data)!=dict:
                    raise Exception("Top level must be object, that is, file must start with '{'")
                for pointtype in pointtypes:
                    if pointtype in data:
                        out=[]
                        for point in data[pointtype]:
                            if validate_point(point,pointtype,self.log):
                                out.append(point)
                        if pointtype=='airfields':
                            validate_airfield_space(point,self.log,self.spaces['airspaces'])
                            
                        self.points[pointtype].extend(out)
                        data.pop(pointtype)
                for spacetype in spacestypes:
                    if spacetype in data:
                        out=[]
                        for space in data[spacetype]:                            
                            if validate_space(space,spacetype,self.log):
                                out.append(space)
                        self.spaces[spacetype].extend(out)
                        data.pop(spacetype)
                if len(data.keys()):
                    for key in data.keys():
                        self.log.append("Unknown top-level key: %s"%(key,))
                        
            except Exception,cause:
                print traceback.format_exc()
                self.log.append(traceback.format_exc())                
                    
        for pointtype in pointtypes:
            bspitems=[]
            for item in self.points[pointtype]:
                print "Adding BspTree item of type: ",pointtype,"item:",item
                bspitems.append(BspTree.Item(                                           
                    mapper.latlon2merc(mapper.from_str(item['pos']),13),item) )
            self.pointslookup[pointtype]=BspTree(bspitems)
            if bspitems:
                self.empty=False
        
        for spacetype in spacestypes:
            bbitems=[]
            for space in self.spaces[spacetype]:
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
            self.spaceslookup[spacetype]=BBTree(bbitems,0.5)
            if bbitems:
                self.empty=False
        
                
        self.date=datetime.utcnow()        
       
userdata=dict()
lock=Lock()

def purge_user_data(user):
    lock.acquire()
    try:
        if user in userdata:
            userdata.pop(user)            
    finally:
        lock.release()
    

def ensure_user_data(user):
    lock.acquire()
    #print "Running ensire user data for ",user
    
    try:
        if not user in userdata:
            for key in list(userdata.keys()):
                ud=userdata[key]
                if datetime.utcnow()-ud.date>timedelta(0,3600):
                    print "Purging custom data for user ",user
                    userdata.pop(key) #Remove old elements from cache
            print "Loading custom data for user ",user
            userdata[user]=UserData(user)
        else:
            ud=userdata[user]
            #print "Reusing cached custom data for user ",user
            if datetime.utcnow()-ud.date>timedelta(0,300):
                ud=UserData(user)
                print "Refreshing cache for user ",user
                userdata[user]=ud            
        return userdata[user]
    finally:        
        lock.release()

def have_any_for(user):
    ud=ensure_user_data(user)
    return ud.have_any()
    
def get_all_airspaces(user):
    return ensure_user_data(user).spaces['airspaces']
def get_all_airfields(user):
    return ensure_user_data(user).points['airfields']
def get_all_obstacles(user):
    return ensure_user_data(user).points['obstacles']
def get_all_sigpoints(user):
    return ensure_user_data(user).points['sigpoints']

def get_airspaces(lat,lon,user):
    if user==None: return
    zoomlevel=13
    px,py=mapper.latlon2merc((lat,lon),zoomlevel)
    bb0=BoundingBox(px,py,px,py)    
    for item in ensure_user_data(user).spaceslookup['airspaces'].overlapping(bb0):
        print "HIT: ",repr(item.payload)
        yield item.payload[1]

def get_airspaces_in_bb(bb13,user):
    if user==None: return
    for item in ensure_user_data(user).spaceslookup['airspaces'].overlapping(bb13):
        yield item.payload[1]


def get_generic_bb(bb13,user,what):
    ud=ensure_user_data(user)
    for item in ud.pointslookup[what].findall_in_bb(bb13):
        yield item.val

def get_generic(lat,lon,zoomlevel,user,what):
    px,py=mapper.latlon2merc((lat,lon),13)
    rad=8<<(13-zoomlevel)
    bb0=BoundingBox(px-rad,py-rad,px+rad,py+rad)
    ud=ensure_user_data(user)
    for item in ud.pointslookup[what].findall_in_bb(bb0):
        print "Got:",item.val
        yield item.val

def get_airfields(lat,lon,zoomlevel,user):
    if user==None: return []
    return get_generic(lat,lon,zoomlevel,user,"airfields")
def get_obstacles(lat,lon,zoomlevel,user):
    if user==None: return []
    return get_generic(lat,lon,zoomlevel,user,"obstacles")
def get_sigpoints(lat,lon,zoomlevel,user):
    if user==None: return []
    return get_generic(lat,lon,zoomlevel,user,"sigpoints")

def get_airfields_in_bb(bb13,user):
    if user==None: return []
    return get_generic_bb(bb13,user,"airfields")
def get_obstacles_in_bb(bb13,user):
    if user==None: return []
    return get_generic_bb(bb13,user,"obstacles")
def get_sigpoints_in_bb(bb13,user):
    if user==None: return []
    return get_generic_bb(bb13,user,"sigpoints")
