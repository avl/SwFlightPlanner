import logging
import StringIO
from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect
from fplan.model import meta,User,Trip,Waypoint,Route,Download,Recording
from fplan.lib import mapper
from datetime import datetime,timedelta
from fplan.lib.recordings import parseRecordedTrip


#import md5
from fplan.lib.helpers import md5str
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

def cleanup_poly(latlonpoints):
    
    for minstep in [0,10,100,1000,10000,100000]:
        mercpoints=[]
        lastmerc=None
        for latlon in latlonpoints:
            merc=mapper.latlon2merc(latlon,13)
            if lastmerc!=None:
                dist=math.sqrt(sum([(lastmerc[i]-merc[i])**2 for i in xrange(2)]))
                print "Dist:",dist
                if dist<minstep:
                    continue
            if merc==lastmerc:
                continue
            lastmerc=merc
            mercpoints.append(Vertex(int(merc[0]),int(merc[1])))
        if len(mercpoints)<50:
            break
    assert len(mercpoints)>2
    if mercpoints[0]==mercpoints[-1]:
        del mercpoints[-1]
    poly=Polygon(vvector(mercpoints))
    backtomerc=[mapper.merc2latlon((m.get_x(),m.get_y()),13) for m in mercpoints]
    if poly.is_ccw():
        return backtomerc
    else:    
        #print "Reversed "+latlonpoints
        return reversed(backtomerc)

class ApiController(BaseController):

    no_login_required=True #But we don't show personal data without user/pass

        
    def get_airspaces(self):
        print "Get airspaces called"
        out=[]
        if 1:
            for space in extracted_cache.get_airspaces()+get_notam_objs_cached()['areas']+extracted_cache.get_aip_sup_areas():
                lat,lon=mapper.from_str(space['points'][0])
                #if lat<57 or lat>62:
                #    continue
                name=space['name']
                if space['type']=="notamarea":
                    name="NOTAM:"+name
                out.append(dict(
                    name=name,
                    freqs=space['freqs'] if space.get('freqs',"") else [],
                    floor=space.get('floor',""),
                    type=space['type'],
                    ceiling=space.get('ceiling',""),
                    points=[dict(lat=p[0],lon=p[1]) for p in cleanup_poly([mapper.from_str(x) for x in space['points']])]))
            
        points=[]
        for airp in extracted_cache.get_airfields():
            lat,lon=mapper.from_str(airp['pos'])
            #if lat<58.5 or lat>60.5:
            #    continue
            aname=airp['name']+"*" if airp.get('icao','ZZZZ').upper()!='ZZZZ' else airp['name']
            points.append(dict(
                name=aname,
                lat=lat,
                lon=lon,
                kind="airport",
                alt=float(airp.get('elev',0))))
        for sigp in extracted_cache.get_sig_points():
            lat,lon=mapper.from_str(sigp['pos'])
            kind=sigp.get('kind','sigpoint')
            if not kind in ['sigpoint','city','town']:
                kind='sigpoint'
            points.append(dict(
                name=sigp['name'],
                lat=lat,
                lon=lon,
                kind=kind,
                alt=-9999.0
                ))
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
            ret=android_fplan_map_format(airspaces=out,points=points,version=request.params.get("version",None))
            print "Android map download from:",request.environ.get("REMOTE_ADDR",'unknown')
            return ret
        else:
            rawtext=json.dumps(dict(airspaces=out,points=points))
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
                def add_wp(name,pos,startalt,endalt,winddir,windvel,gs,what,legpart,lastsub,d,tas):
                    d=dict(lat=pos[0],lon=pos[1],
                        name=name,startalt=startalt,endalt=endalt,winddir=winddir,windvel=windvel,gs=gs,what=what,legpart=legpart,lastsub=lastsub,d=d,tas=tas)
                    waypoints.append(d)
                rt0=rts[0]
                add_wp(rt0.a.waypoint,rt0.startpos,rt0.startalt,rt0.endalt,rt0.winddir,rt0.windvel,rt0.gs,
                        "start","start",1,0,rt0.tas)                            
                for rt in rts:                        
                    add_wp(rt.b.waypoint,rt.endpos,rt.startalt,rt.endalt,rt.winddir,rt.windvel,rt.gs,rt.what,rt.legpart,rt.lastsub,rt.d,rt.tas)

            tripobj['waypoints']=waypoints
            response.headers['Content-Type'] = 'text/plain'            
            return json.dumps(tripobj)
        except Exception,cause:
            response.headers['Content-Type'] = 'text/plain'            
            return json.dumps(dict(error=repr(cause)))
        
    def getmap(self):

        users=meta.Session.query(User).filter(User.user==request.params['user']).all()
        badpass=False
        if len(users)==0:
            badpass=True
        else:
            user,=users
            if user.password!=request.params['password'] and user.password!=md5str(request.params['password']):
                badpass=True
        def writeInt(x):
            response.write(struct.pack(">I",x))
        def writeLong(x):
            response.write(struct.pack(">Q",x))
        response.headers['Content-Type'] = 'application/binary'        
        writeInt(0xf00df00d)
        writeInt(1) #version
        if badpass:
            print "badpassword"
            writeInt(1) #error, bad pass
            return None
        print "Correct password"
        version,level,offset,maxlen,maxlevel=\
            [int(request.params[x]) for x in "version","level","offset","maxlen","maxlevel"];
        
        totalsize=0
        stamp=0
        for lev in xrange(maxlevel+1):
            tlevelfile=os.path.join(os.getenv("SWFP_DATADIR"),"tiles/nolabel/level"+str(lev))
            totalsize+=os.path.getsize(tlevelfile)
            stamp=max(stamp,os.stat(tlevelfile)[stat.ST_MTIME])
        print "Maxlevel: %d, stamp: %d"%(maxlevel,stamp)
        levelfile=os.path.join(os.getenv("SWFP_DATADIR"),"tiles/nolabel/level"+str(level))
        curlevelsize=os.path.getsize(levelfile)    
        cursizeleft=curlevelsize-offset
        print "cursize left:",cursizeleft
        print "maxlen:",maxlen
        if cursizeleft<0:
            cursizeleft=0
        if maxlen>cursizeleft:
            maxlen=cursizeleft
        if maxlen>1000000:
            maxlen=1000000
        
         
        writeInt(0) #no error
        print "No error"
        writeLong(stamp) #"data version"
        print "stamp:",stamp
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
        
        f=open(levelfile)
        meta.Session.flush()
        meta.Session.commit()
        
        if offset<curlevelsize:
            print "seeking to %d of file %s, then reading %d bytes"%(offset,levelfile,maxlen)
            f.seek(offset)
            data=f.read(maxlen)
            print "Writing %d bytes to client"%(len(data),)
            response.write(data)
        f.close()
        return None
    
    def uploadtrip(self):
        def writeInt(x):
            response.write(struct.pack(">I",x))
        
        print "upload trip",request.params
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
            
            print "POST:",request.POST
            newrec=parseRecordedTrip(user.user,f)
            
            meta.Session.query(Recording).filter(
                sa.and_(Recording.start==newrec.start,
                        Recording.user==newrec.user)).delete()
            meta.Session.add(newrec)
            meta.Session.flush()
            meta.Session.commit()
            
            #print "GOt bytes: ",len(cont)
            print "Upload!",request.params
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
    
        
        
