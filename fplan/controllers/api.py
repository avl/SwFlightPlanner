import logging
import StringIO
from pylons import request, response, session, tmpl_context as c
import fplan.lib.metartaf as metartaf
from pylons.controllers.util import abort, redirect
from fplan.model import meta,User,Trip,Waypoint,Route,Download,Recording,AirportProjection,Aircraft
from fplan.lib import mapper
from datetime import datetime,timedelta
from fplan.lib.recordings import parseRecordedTrip
import fplan.extract.parse_landing_chart as parse_landing_chart
import StringIO
import traceback
#import md5
from fplan.lib.helpers import md5str,utcdatetime2stamp_inexact
import fplan.lib.customproj as customproj
import stat
from fplan.lib.notam_geo_search import get_notam_objs_cached
import fplan.lib.calc_route_info as calc_route_info
from fplan.lib.base import BaseController, render
import json
log = logging.getLogger(__name__)
import sqlalchemy as sa
import fplan.extract.extracted_cache as extracted_cache
from pyshapemerge2d import Polygon,Vertex,vvector
import fplan.lib.notam_geo_search as notam_geo_search
from fplan.lib.androidstuff import android_fplan_map_format,android_fplan_bitmap_format
import csv
from itertools import chain
from fplan.lib.get_near_route import heightmap_tiles_near,map_tiles_near
import zlib
import math
import struct
import os
class BadCredentials(Exception):pass

def get_user_trips(user):
    users=meta.Session.query(User).filter(User.user==user).all()
    if len(users)==0:
        return []
    user,=users
    
    trips=meta.Session.query(Trip).filter(sa.and_(Trip.user==user.user)).order_by(Trip.trip).all()
    out=[]
    for trip in trips:
        meta.Session.flush()
        try:
            #print "Processing trip",trip.trip
            tripobj=dict()
            tripobj['name']=trip.trip
            tripobj['aircraft']=trip.aircraft
            
            actypes=list(meta.Session.query(Aircraft).filter(Aircraft.aircraft==trip.aircraft).all())
            if len(actypes)==0:
                tripobj['atsradiotype']='?'
            else:
                tripobj['atsradiotype']=actypes[0].atsradiotype
            
            waypoints=[]
            def eitherf(x,fallback):
                try:
                    if x==None: return fallback
                    return float(x)
                except Exception:
                    return 0.0
            def da(x):
                try:
                    if x==None: return datetime(1970,1,1)
                    if type(x)==datetime: return x
                    return datetime(1970,1,1)
                except Exception:
                    return datetime(1970,1,1)
            def f(x):
                try:
                    if x==None: return 0.0
                    return float(x)
                except Exception:
                    return 0.0
            def i(x):
                try:
                    if x==None: return 0
                    return int(x)
                except Exception:
                    return 0
            def s(x):
                try:
                    if x==None: return ""
                    if type(x)==unicode: return x
                    return unicode(x,'utf8')
                except Exception:
                    return ""
            def add_wp(name,pos,startalt,endalt,winddir,windvel,gs,what,legpart,lastsub,d,tas,land_at_end,
                       endfuel,fuelburn,depart_dt,arrive_dt,altitude):
                assert depart_dt==None or type(depart_dt)==datetime                
                assert type(pos[0])in [float,int]
                assert type(pos[1])in [float,int]
                d=dict(lat=pos[0],lon=pos[1],
                    name=name,startalt=f(startalt),endalt=f(endalt),winddir=f(winddir),windvel=f(windvel),
                        gs=eitherf(gs,75),what=s(what),legpart=s(legpart),lastsub=i(lastsub),d=f(d),tas=eitherf(tas,75),land_at_end=i(land_at_end),
                        endfuel=f(endfuel),fuelburn=f(fuelburn),depart_dt=da(depart_dt),arrive_dt=da(arrive_dt),altitude=s(altitude)
                        )
                waypoints.append(d)
            
            try:

                rts,dummy=calc_route_info.get_route(user.user,trip.trip)
            except Exception:
                print traceback.format_exc()
                wpy=list(meta.Session.query(Waypoint).filter(sa.and_(
                         Waypoint.user==user.user,Waypoint.trip==trip.trip)).order_by(Waypoint.ordering).all())

                rts=[]                
                for wp1,wp2 in zip(wpy,wpy[1:]):
                    trts=meta.Session.query(Route).filter(sa.and_(
                        Route.user==user.user,Route.trip==trip.trip,
                        Route.waypoint1==wp1.id,Route.waypoint2==wp2.id)).all()
                    dummy,d=mapper.bearing_and_distance(wp1.pos,wp2.pos)                        
                    if len(trts)==0:
                        rts.append(Route(user=user.user,trip=trip.trip,waypoint1=wp1.id,waypoint2=wp2.id,winddir=None,windvel=None,tas=None,variation=None,altitude="1500"))
                    else:
                        rts.append(trts[0])
                
                if len(rts):
                    rt0=rts[0]                    
                    add_wp(rt0.a.waypoint,mapper.from_str(rt0.a.pos),1500,1500,rt0.winddir,rt0.windvel,0,
                            "start","start",1,0,rt0.tas,False,0,0,
                            None,None,rt0.altitude)
                    del rt0
                    for rt in rts:                        
                        land_at_end=not not (rt.b.stay)
                        #print "Land at end of leg:",rt.b.waypoint,":",land_at_end
                        dummy,d=mapper.bearing_and_distance(rt.a.pos,rt.b.pos)
                        add_wp(rt.a.waypoint,mapper.from_str(rt.a.pos),1500,1500,rt.winddir,rt.windvel,0,
                            "cruise","mid",1,d,rt.tas,land_at_end,0,0,
                            None,None,rt.altitude)
            
            else:
                if len(rts):
                    rt0=rts[0]                    
                    try:
                        startfuel=rt0.accum_fuel_left+rt0.fuel_burn
                    except Exception:
                        startfuel=None
                    print "Startfuel:",startfuel
                    add_wp(rt0.a.waypoint,rt0.startpos,rt0.startalt,rt0.endalt,rt0.winddir,rt0.windvel,rt0.gs,
                            "start","start",1,0,rt0.tas,False,startfuel,0,
                            rt0.depart_dt,rt0.depart_dt,rt0.altitude)
                    del rt0
                    for rt in rts:                        
                        land_at_end=not not (rt.b.stay and rt.lastsub)
                        #print "Land at end of leg:",rt.b.waypoint,":",land_at_end
                        add_wp(rt.b.waypoint,rt.endpos,rt.startalt,rt.endalt,rt.winddir,rt.windvel,rt.gs,rt.what,rt.legpart,rt.lastsub,rt.d,rt.tas,land_at_end,
                               rt.accum_fuel_left,rt.fuel_burn,rt.depart_dt,rt.arrive_dt,rt.altitude)
            
            tripobj['waypoints']=waypoints
        except Exception:
            print "While processing trip",trip.trip,":",traceback.format_exc()
            continue
        out.append(tripobj)
    return out

def cleanup_poly(latlonpoints,name="?"):
    
    for minstep in [0,10,100,1000,10000,100000]:
        mercpoints=[]
        lastmerc=None
        for latlon in latlonpoints:
            merc=mapper.latlon2merc(latlon,13)
            if lastmerc!=None:
                dist=math.sqrt(sum([(lastmerc[i]-merc[i])**2 for i in xrange(2)]))
                if dist<minstep:
                    continue
            if merc==lastmerc:
                continue
            lastmerc=merc
            mercpoints.append(Vertex(int(merc[0]),int(merc[1])))
        if len(mercpoints)<50:
            break
    if len(mercpoints)<=2: return None
    if mercpoints[0]==mercpoints[-1]:
        del mercpoints[-1]
    if len(mercpoints)<=2: return None
    poly=Polygon(vvector(mercpoints))
    if len(mercpoints)==4:
        swapped=[mercpoints[1],mercpoints[0]]+mercpoints[2:]
        swappedpoly=Polygon(vvector(swapped))
        print "Found 4-corner area: ",name," areas:",swappedpoly.calc_area(),poly.calc_area()
        if abs(swappedpoly.calc_area())>abs(1.1*poly.calc_area()):
            print "Untwisting an area",name
            mercpoints=swapped
            poly=swappedpoly
            
    backtomerc=[mapper.merc2latlon((m.get_x(),m.get_y()),13) for m in mercpoints]
    if poly.is_ccw():
        return backtomerc
    else:    
        #print "Reversed "+latlonpoints
        return reversed(backtomerc)

def get_proj(cksum0):
    projs=meta.Session.query(AirportProjection).filter(sa.and_(
                        AirportProjection.mapchecksum==cksum0,
                        sa.or_(AirportProjection.user=='ank',AirportProjection.user==request.params.get('user','ank'))
                        )).all()
    if len(projs)==0:
        return None
#Issues to solve:
#- It is a problem that AD-charts can change, and we don't have a new tranform. How do handle? Keep old chart for a short while? Ask user to "click the chart"? Send chart without transform?
#- We need more robust updating of client side. 
#  Update scenarios:
#  - New airfield (handled by stamp)
#  - New matrix (need stamp on matrix itself - already have - just use it!)
#  - Recover from aborted client download. Don't store client stamp for aborted downloads?
#  - Renaming map-clicker user? Need to update matrix stamps in this case.
#
#QUestion:
# Can we be more robust? Like sending complete list of client state to server?         
    for t in projs:
        if t.user!='ank':
            proj=t
            break
    else:
        proj=projs[0]
    return proj


class ApiController(BaseController):

    no_login_required=True #But we don't show personal data without user/pass

        
    def get_airspaces(self):
        print "Get airspaces called"
        
        getsectors=int(request.params.get("sectors","0"))
        
        out=[]
        if 1:
            for space in extracted_cache.get_airspaces()+get_notam_objs_cached()['areas']+extracted_cache.get_aip_sup_areas():
                lat,lon=mapper.from_str(space['points'][0])
                #if lat<57 or lat>62:
                #    continue
                if getsectors==0 and space.get('type',None)=='sector':
                    continue
                name=space['name']
                if space['type']=="notamarea":
                    name="NOTAM:"+name
                clnd=cleanup_poly([mapper.from_str(x) for x in space['points']],name)
                if not clnd:
                    print "Skipped area",name,space 
                    continue
                out.append(dict(
                    name=name,
                    freqs=space['freqs'] if space.get('freqs',"") else [],
                    floor=space.get('floor',""),
                    type=space['type'],
                    ceiling=space.get('ceiling',""),
                    points=[dict(lat=p[0],lon=p[1]) for p in clnd]))
            
        aiptexts=[]
        points=[]
        version=request.params.get("version",None)
        getaiptext=int(request.params.get("aip","0"))
        print "version",version
        if version and int(version.strip())>=5:
            user_aipgen=request.params.get("aipgen","")
        else:
            user_aipgen=""
        for airp in extracted_cache.get_airfields():
            lat,lon=mapper.from_str(airp['pos'])
            if lat<54 or lon<4 or lon>=30.5:
                try:
                    if not version or int(version.strip())<=7:
                        continue
                except:
                    continue

            #if lat<58.5 or lat>60.5:
            #    continue
            aname=airp['name']
            
            notams=[]
            icao=None
            taf=None
            metar=None
            kind='field'
            if airp.get('icao','zzzz').lower()!='zzzz':
                icao=airp['icao']
                notams=notam_geo_search.get_notam_for_airport(icao)
                metar=metartaf.get_metar(icao)
                taf=metartaf.get_taf(icao)
                kind='port'
                
            ap=dict(
                name=aname,
                lat=lat,
                lon=lon,
                kind=kind,
                notams=notams,
                remark=airp.get('remark',''),
                alt=float(airp.get('elev',0)))
            if 'runways' in airp:
                ap['runways']=airp['runways']
            if icao:
                ap['icao']=icao
                if taf.text:
                    ap['taf']=taf.text
                if metar.text:
                    ap['metar']=metar.text
            
                if getaiptext and 'aiptext' in airp:
                    for aiptext in airp['aiptext']:
                        aiptexts.append(
                            dict(name=icao+"_"+aiptext['category'],
                                 icao=icao,
                                 data=aiptext))
                    
            if 'adcharts' in airp and '' in airp['adcharts'] and airp['adcharts'][""]['blobname']:
                ret=airp['adcharts'][""]
                try:
                    cksum=ret['checksum']
                    try:
                        aprojmatrix=get_proj(cksum).matrix
                    except Exception:
                        #print traceback.format_exc()
                        #print "Using 0-proj for ",aname
                        aprojmatrix=[0 for x in xrange(6)]
                        
                    ap['adchart_matrix']=list(aprojmatrix)
                    ap['adchart_width']=ret['render_width']
                    ap['adchart_height']=ret['render_height']
                    ap['adchart_name']=ret['blobname']
                    ap['adchart_checksum']=cksum
                    ap['adchart_url']=ret['url']                    
                except Exception,cause:
                    print "Couldn't get projection for airport %s (%s)"%(aname,cause)
            
            points.append(ap)            
        for sigp in extracted_cache.get_sig_points():
            lat,lon=mapper.from_str(sigp['pos'])
            kind=sigp.get('kind','sigpoint')
            if kind=='sig. point':
                kind='sigpoint'
            if not kind in ['sigpoint','city','town']:
                kind='sigpoint'
            points.append(dict(
                name=sigp['name'],
                lat=lat,
                lon=lon,
                kind=kind,
                alt=-9999.0
                ))
        
        user=request.params.get('user',None)
        correct_pass=False
        if user:
            try:
                print "Received password",request.params['password'],"user:",repr(user)
                userobj,=meta.Session.query(User).filter(User.user==user).all()
                if userobj.password!=request.params['password'] and userobj.password!=md5str(request.params['password']):
                    raise Exception("Bad password")
                correct_pass=True
                trips=get_user_trips(user)
            except Exception:
                print traceback.format_exc()
                trips=[]
        else:
            trips=[]
        
        
            #print "Just added:",points[-1]
        #add sig. points!
        if 1:
            for obst in chain(notam_geo_search.get_notam_objs_cached()['obstacles'],
                    extracted_cache.get_obstacles()):
                lat,lon=mapper.from_str(obst['pos'])
                #if lat<58.5 or lat>59.5:
                #    continue
                tname=obst.get('name','Unknown')
                if obst.get('kind','').startswith("notam"):
                    tname="Notam Obst."
                points.append(dict(
                    name=tname,
                    lat=lat,
                    lon=lon,
                    kind="obstacle",
                    alt=float(obst['elev'])))
                    
        if request.params.get('csv','').strip()!="":
            #use CSV format
            meta.Session.flush()
            meta.Session.commit()
            buf=StringIO.StringIO()
            w=csv.writer(buf)            
            for space in out:
                freq=''
                if len(space['freqs'])>0:
                    freq=" ".join(u"%s"%(x[1],) for x in space['freqs'])
                    freq=freq
                line=[space['name'],'*',freq,'*',space['floor'],space['ceiling']]
                for point in space['points']:
                    lat,lon=point['lat'],point['lon']
                    line.append(lat)
                    line.append(lon)
                for i in xrange(len(line)):
                    if type(line[i])==unicode:
                        line[i]=line[i].encode('utf8')
                w.writerow(line)            
            response.headers['Content-Type'] = 'text/plain'           
            return buf.getvalue()
        elif request.params.get('binary','').strip()!='':
            response.headers['Content-Type'] = 'application/binary'
            ret=android_fplan_map_format(airspaces=out,points=points,aiptexts=aiptexts,trips=trips,version=version,user_aipgen=user_aipgen,correct_pass=correct_pass)
            
            print "meta.Session.flush/commit"
            meta.Session.flush()
            meta.Session.commit()
            if 'zip' in request.params:
                zobj = zlib.compressobj(9)#,zlib.DEFLATED,14)
                ret=zobj.compress(ret)
                ret+=zobj.flush()
            print "Android map download from:",request.environ.get("REMOTE_ADDR",'unknown')," size: ",len(ret),"bytes"
            return ret
        else:
            meta.Session.flush()
            meta.Session.commit()
            
            rawtext=json.dumps(dict(airspaces=out,points=points),indent=1)
            
            
            if 'zip' in request.params:
                response.headers['Content-Type'] = 'application/x-gzip-compressed'            
                return zlib.compress(rawtext)
            else:
                response.headers['Content-Type'] = 'text/plain'            
                return rawtext
                    
    

    def get_trips(self):
        try:
            print "Get trips",request.params
            users=meta.Session.query(User).filter(User.user==request.params['user']).all()
            if len(users)==0:
                return json.dumps(dict(error=u"No user with that name"))
            user,=users
            if user.password!=request.params['password'] and user.password!=md5str(request.params['password']):
                return json.dumps(dict(error=u"Wrong password"))
                
            out=[]        
            for trip in meta.Session.query(Trip).filter(Trip.user==user.user).order_by(Trip.trip).all():
                out.append(trip.trip)
            response.headers['Content-Type'] = 'text/plain'            
            s=json.dumps(dict(trips=out))
            print "Returning",repr(s)
            return s
        except Exception,cause:
            response.headers['Content-Type'] = 'text/plain'            
            return json.dumps(dict(error=repr(cause)))
        
    def get_elev_near_trip(self):
        users=meta.Session.query(User).filter(User.user==request.params['user']).all()
        if len(users)==0:
            return json.dumps(dict(error=u"No user with that name"))
        user,=users
        if user.password!=request.params['password'] and user.password!=md5str(request.params['password']):
            return json.dumps(dict(error=u"Wrong password"))
        trip=request.params['trip']

        rts=sorted(list(meta.Session.query(Route).filter(sa.and_(
            Route.user==request.params['user'],Route.trip==trip)).all()),key=lambda x:x.a.ordering)

        response.headers['Content-Type'] = 'application/binary'                            
        return android_fplan_bitmap_format(heightmap_tiles_near(rts,10))

    def get_map_near_trip(self):
        users=meta.Session.query(User).filter(User.user==request.params['user']).all()
        if len(users)==0:
            return json.dumps(dict(error=u"No user with that name"))
        user,=users
        if user.password!=request.params['password'] and user.password!=md5str(request.params['password']):
            return json.dumps(dict(error=u"Wrong password"))
        trip=request.params['trip']

        rts=sorted(list(meta.Session.query(Route).filter(sa.and_(
            Route.user==request.params['user'],Route.trip==trip)).all()),key=lambda x:x.a.ordering)

        response.headers['Content-Type'] = 'application/binary'                            
        return android_fplan_bitmap_format(map_tiles_near(rts,10))
        

                    
    def get_trip(self):
        try:
            print "Get trip",request.params
            users=meta.Session.query(User).filter(User.user==request.params['user']).all()
            if len(users)==0:
                return json.dumps(dict(error=u"No user with that name"))
            user,=users
            if user.password!=request.params['password'] and user.password!=md5str(request.params['password']):
                return json.dumps(dict(error=u"Wrong password"))
            
            trip,=meta.Session.query(Trip).filter(sa.and_(Trip.user==user.user,Trip.trip==request.params['trip'])).order_by(Trip.trip).all()
            
            tripobj=dict()
            tripobj['trip']=trip.trip
            waypoints=[]
            rts,dummy=calc_route_info.get_route(user.user,trip.trip)
            if len(rts):
                def either(x,fallback):
                    if x==None: return fallback
                    return x
                def add_wp(name,pos,startalt,endalt,winddir,windvel,gs,what,legpart,lastsub,d,tas,land_at_end):
                    d=dict(lat=pos[0],lon=pos[1],
                        name=name,startalt=startalt,endalt=endalt,winddir=winddir,windvel=windvel,
                            gs=either(gs,75),what=what,legpart=legpart,lastsub=lastsub,d=d,tas=either(tas,75),land_at_end=land_at_end)
                    waypoints.append(d)
                rt0=rts[0]
                
                add_wp(rt0.a.waypoint,rt0.startpos,rt0.startalt,rt0.endalt,rt0.winddir,rt0.windvel,rt0.gs,
                        "start","start",1,0,rt0.tas,False)
                                        
                for rt in rts:                        
                    land_at_end=not not (rt.b.stay and rt.lastsub)
                    print "Land at end of leg:",rt.b.waypoint,":",land_at_end
                    add_wp(rt.b.waypoint,rt.endpos,rt.startalt,rt.endalt,rt.winddir,rt.windvel,rt.gs,rt.what,rt.legpart,rt.lastsub,rt.d,rt.tas,land_at_end)

            tripobj['waypoints']=waypoints
            print "returning json:", waypoints
            response.headers['Content-Type'] = 'text/plain'            
            return json.dumps(tripobj)
        except Exception,cause:
            response.headers['Content-Type'] = 'text/plain'            
            print "Exception",cause
            return json.dumps(dict(error=repr(cause)))

    def checkpass(self):
        users=meta.Session.query(User).filter(User.user==request.params['user']).all()
        if len(users)==0:
            print "no user found with name",request.params['user']
            return False
        else:
            user,=users
            if user.password!=request.params['password'] and user.password!=md5str(request.params['password']):
                print "Attempted password: %s, user has: %s"%(request.params['password'],user.password)
                return False
        return True

    def get_sel_cksum(self,blobname):
        #Get the most suitable cksum version of map for this
        #blobname
        proj=None
        issues=sorted(parse_landing_chart.get_all_issues(blobname),
                   key=lambda x:-x['stamp'])
        if len(issues)==0:
            return None,proj
        
        for issue in issues:
            proj=get_proj(issue['cksum'])
            if proj:
                break
        else:                            
            issue=issues[0]
            proj=None                                            
        
        cksum=issue['cksum']
        return cksum,proj
     
    def getnewadchart(self):
        prevstamp=int(request.params["stamp"])
        print "getnewadchart, prevstamp:",prevstamp
        version=int(request.params["version"])
        #Make any sort of race impossible by substracting 5 minutes from now.
        #A race will now only happen if a file is modified on disk, after this
        #routine started, but ends up with a timestamp 5 minutes earlier in
        #time, but that can't happen.
        nowstamp=utcdatetime2stamp_inexact(datetime.utcnow())-60*5
        assert version in [1,2,3]
        
        
        def writeInt(x):
            response.write(struct.pack(">I",x))
        def writeLong(x):
            response.write(struct.pack(">Q",x))
        def writeUTF(s):
            if s==None: s=u""
            try:
                encoded=s.encode('utf8')
            except Exception,cause:
                print "While trying to encode: %s"%(s,)
                raise
            l=len(encoded)
            response.write(struct.pack(">H",l)) #short
            response.write(encoded)
            
        
        charts=[]
        print "Old stamp",prevstamp
        for ad in extracted_cache.get_airfields():
            if ad.get('icao','ZZZZ').upper()=='ZZZZ':continue #Ignore non-icao airports 
            if 'adcharts' in ad:
                for adc in ad['adcharts'].values():
                    newer=False
                    try:
                        cksum,proj=self.get_sel_cksum(adc['blobname'])
                        if proj and proj.updated>datetime.utcfromtimestamp(prevstamp):
                            newer=True 
                        #print "selected",cksum,"for",adc
                        if version<=2 and adc['variant']!='':
                            continue #Don't send all kinds of charts to old clients
                        if cksum==None: continue
                        for level in xrange(5):
                            cstamp=parse_landing_chart.get_timestamp(adc['blobname'],cksum,level)                        
                            #print "Read file stamp:",cstamp,"prevstamp:",prevstamp
                            if cstamp>prevstamp:
                                newer=True
                    except Exception,cause:                        
                        print traceback.format_exc()
                        continue
                    if newer:
                        charts.append((ad['name'],adc['blobname'],ad['icao'],cksum,adc['variant']))
            
        response.headers['Content-Type'] = 'application/binary'
           
        writeInt(0xf00d1011)
        writeInt(version) #version
        writeLong(nowstamp)
        writeInt(len(charts))
        #TODO: Fix problem with response.write not working
        for human,blob,icao,cksum,variant in charts:
            print "New AD-chart not present on device:",human,blob,icao
            writeUTF(blob)
            writeUTF(human)
            if version>=2:
                writeUTF(icao)
                writeUTF(cksum)
            if version>=3:
                writeUTF(variant)
        writeInt(0xaabbccda)
        #out.seek(0)
        #response.app_iter=out.read()

        

    def getadchart(self):
        def writeInt(x):
            response.write(struct.pack(">I",x))
        def writeFloat(f):
            response.write(struct.pack(">f",f))
        def writeDouble(f):
            response.write(struct.pack(">d",f))
        def writeUTF(s):
            if s==None: s=u""
            try:
                encoded=s.encode('utf8')
            except Exception,cause:
                print "While trying to encode: %s"%(s,)
                raise
            l=len(encoded)
            #print "Writing %s, length %d"%(repr(encoded),l)
            response.write(struct.pack(">H",l)) #short
            response.write(encoded)

        response.headers['Content-Type'] = 'application/binary'        

        version=int(request.params['version'])
        
        chartname=request.params["chart"]
        
        cksum=request.params.get("cksum")
        if cksum==None:
            cksum,proj=self.get_sel_cksum(chartname)
            assert cksum            
        
        writeInt(0xaabb1234)
        if version!=1 and version!=2:
            print "bad version"
            writeInt(2) #error, bad version
            return None        
        if not self.checkpass():
            print "badpassword"
            writeInt(1) #error, bad pass
            return None
        
        width,height=parse_landing_chart.get_width_height(chartname=chartname,cksum=cksum)
        
        dummy,cksum0=parse_landing_chart.get_chart(blobname=chartname,cksum=cksum,level=0)
        assert cksum0==cksum
        proj=get_proj(cksum0)
        if proj:
            matrix=proj.matrix
        else:
            matrix=[0.0 for x in xrange(6)]    
        zeromat=all([abs(x)<1e-13 for x in matrix])
        writeInt(0) #no error
        writeInt(version) #version
        
        writeInt(5) #numlevels
        
        if not zeromat:
            tf=customproj.Transform(matrix[0:4],matrix[4:6])
            Ai=tf.inverse_matrix()        
            writeDouble(Ai[0,0])
            writeDouble(Ai[1,0])
            writeDouble(Ai[0,1])
            writeDouble(Ai[1,1])
            print "Writing matrix",Ai," and offset",matrix[4:6],"to client"
        else:
            writeDouble(0)
            writeDouble(0)
            writeDouble(0)
            writeDouble(0)
            print "Dummy matrix"
            
        writeDouble(matrix[4])
        writeDouble(matrix[5])
        
        if version>=2:
            writeInt(width)
            writeInt(height)
            print "Writing width,height",chartname,width,height
            
        writeInt(0xaabbccde)
        for level in xrange(5):            
            chart,cksum=parse_landing_chart.get_chart(blobname=chartname,cksum=cksum,level=level)
            writeUTF(cksum)
            writeInt(len(chart))
            response.write(chart)
            writeInt(0xaabbccdf)
        writeInt(0xf111)
        return 
        
    def getmap(self):

        users=meta.Session.query(User).filter(User.user==request.params['user']).all()
        badpass=False
        if len(users)==0:
            badpass=True
        else:
            user,=users
            if user.password!=request.params['password'] and user.password!=md5str(request.params['password']):
                badpass=True
        maptype=request.params.get('maptype','nolabel')
        def writeInt(x):
            response.write(struct.pack(">I",x))
        def writeLong(x):
            response.write(struct.pack(">Q",x))
        response.headers['Content-Type'] = 'application/binary'        

        version,level,offset,maxlen,maxlevel=\
            [int(request.params[x]) for x in "version","level","offset","maxlen","maxlevel"];
        
        writeInt(0xf00df00d)
        writeInt(1) #version
        if badpass:
            print "badpassword"
            writeInt(1) #error, bad pass
            return None
        #print "Correct password"
        
        totalsize=0
        stamp=0
        for lev in xrange(maxlevel+1):
            tlevelfile=os.path.join(os.getenv("SWFP_DATADIR"),"tiles/"+maptype+"/level"+str(lev))
            totalsize+=os.path.getsize(tlevelfile)
            stamp=max(stamp,os.stat(tlevelfile)[stat.ST_MTIME])
        #print "Maxlevel: %d, stamp: %d"%(maxlevel,stamp)
        levelfile=os.path.join(os.getenv("SWFP_DATADIR"),"tiles/"+maptype+"/level"+str(level))
        curlevelsize=os.path.getsize(levelfile)    
        cursizeleft=curlevelsize-offset
        #print "cursize left:",cursizeleft
        #print "maxlen:",maxlen
        if cursizeleft<0:
            cursizeleft=0
        if maxlen>cursizeleft:
            maxlen=cursizeleft
        if maxlen>1000000:
            maxlen=1000000
        
         
        writeInt(0) #no error
        #print "No error"
        writeLong(stamp) #"data version"
        #print "stamp:",stamp
        writeLong(curlevelsize)
        writeLong(totalsize)
        writeLong(cursizeleft)
        writeInt(0xa51c2)
        latest=meta.Session.query(Download).filter(Download.user==user.user).order_by(sa.desc(Download.when)).first()
        if not latest or datetime.utcnow()-latest.when>timedelta(0,3600):
            down=Download(user.user, maxlen)
            meta.Session.add(down)
        else:
            down=latest
            down.bytes+=maxlen
        meta.Session.flush()
        meta.Session.commit()

        f=open(levelfile)

        if offset<curlevelsize:
            #print "seeking to %d of file %s, then reading %d bytes"%(offset,levelfile,maxlen)
            f.seek(offset)
            data=f.read(maxlen)
            #print "Writing %d bytes to client"%(len(data),)
            response.write(data)
        f.close()
        return None
    
    def uploadtrip(self):
        def writeInt(x):
            response.write(struct.pack(">I",x))
        
        #print "upload trip",request.params
        try:
            f=request.POST['upload'].file
            def readShort():
                return struct.unpack(">H",f.read(2))[0]
            def readUTF():
                len=readShort()
                print "Read string of length %d"%(len,)
                data=f.read(len)
                return unicode(data,"utf8")
            
            username=readUTF()
            password=readUTF()
            print "user,pass",username,password
            users=meta.Session.query(User).filter(User.user==username).all()
            if len(users)==0:
                raise BadCredentials("bad user")
            user=users[0]
            if user.password!=password and user.password!=md5str(password):
                raise BadCredentials("bad password")
            
            #print "POST:",request.params
            newrec=parseRecordedTrip(user.user,f)
            
            meta.Session.query(Recording).filter(
                sa.and_(Recording.start==newrec.start,
                        Recording.user==newrec.user)).delete()
            meta.Session.add(newrec)
            meta.Session.flush()
            meta.Session.commit()
            
            #print "GOt bytes: ",len(cont)
            #print "Upload!",request.params
        except BadCredentials,cause:
            response.headers['Content-Type'] = 'application/binary'        
            writeInt(0xf00db00f)
            writeInt(1) #version
            writeInt(1) #errorcode, bad user/pass
            return None
        except Exception,cause:
            print cause
            raise
        response.headers['Content-Type'] = 'application/binary'        
        writeInt(0xf00db00f)
        writeInt(1) #version
        writeInt(0) #errorcode, success
        return None
    
        
        
