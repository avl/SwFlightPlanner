import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from fplan.model import meta,User,Trip,Waypoint,Route
from fplan.lib import mapper
import md5
import fplan.lib.calc_route_info as calc_route_info
from fplan.lib.base import BaseController, render
import json
log = logging.getLogger(__name__)
import sqlalchemy as sa
import fplan.extract.extracted_cache as extracted_cache
from pyshapemerge2d import Polygon,Vertex,vvector

def cleanup_poly(latlonpoints):
    mercpoints=[]
    lastmerc=None
    for latlon in latlonpoints:
        merc=mapper.latlon2merc(latlon,13)
        if merc==lastmerc:
            continue
        lastmerc=merc
        mercpoints.append(Vertex(int(merc[0]),int(merc[1])))
    assert len(mercpoints)>2
    if mercpoints[0]==mercpoints[-1]:
        del mercpoints[-1]
    poly=Polygon(vvector(mercpoints))
    backtomerc=[mapper.merc2latlon((m.get_x(),m.get_y()),13) for m in mercpoints]
    if poly.is_ccw():
        return backtomerc
    else:    
        print "Reversed "+latlonpoints
        return reversed(backtomerc)

class ApiController(BaseController):

    no_login_required=True #But we don't show personal data without user/pass

    def get_airspaces(self):
        print "Get airspaces called"
        out=[]
        if 1:
            for space in extracted_cache.get_airspaces():
                lat,lon=mapper.from_str(space['points'][0])
                #if lat<57 or lat>62:
                #    continue
                out.append(dict(
                    name=space['name'],
                    freqs=space['freqs'] if (space['freqs']!="" and space['freqs']!=None) else [],
                    floor=space['floor'],
                    ceiling=space['ceiling'],
                    points=[dict(lat=p[0],lon=p[1]) for p in cleanup_poly([mapper.from_str(x) for x in space['points']])]))
            
        points=[]
        for airp in extracted_cache.get_airfields():
            lat,lon=mapper.from_str(airp['pos'])
            #if lat<58.5 or lat>60.5:
            #    continue
            points.append(dict(
                name=airp['name'],
                lat=lat,
                lon=lon,
                kind="airport",
                alt=airp['elev']))
        if 1:
            for obst in extracted_cache.get_obstacles():
                lat,lon=mapper.from_str(obst['pos'])
                #if lat<58.5 or lat>59.5:
                #    continue
                points.append(dict(
                    name=obst['name'],
                    lat=lat,
                    lon=lon,
                    kind="obstacle",
                    alt=obst['height']))
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
            if user.password!=request.params['password'] and user.password!=md5.md5(request.params['password']).hexdigest():
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
            
    def get_trip(self):
        try:
            print "Get trip",request.params
            users=meta.Session.query(User).filter(User.user==request.params['user']).all()
            if len(users)==0:
                return json.dumps(dict(error=u"No user with that name"))
            user,=users
            if user.password!=request.params['password'] and user.password!=md5.md5(request.params['password']).hexdigest():
                return json.dumps(dict(error=u"Wrong password"))
            
            trip,=meta.Session.query(Trip).filter(sa.and_(Trip.user==user.user,Trip.trip==request.params['trip'])).order_by(Trip.trip).all()
            
            tripobj=dict()
            tripobj['trip']=trip.trip
            waypoints=[]
            rts=calc_route_info.get_route(user.user,trip.trip)
            if len(rts):
                def add_wp(name,pos,altitude,winddir,windvel,gs,what,legpart,lastsub,d,tas):
                    d=dict(lat=pos[0],lon=pos[1],
                        name=name,altitude=altitude,winddir=winddir,windvel=windvel,gs=gs,what=what,legpart=legpart,lastsub=lastsub,d=d,tas=tas)
                    waypoints.append(d)
                rt0=rts[0]
                add_wp(rt0.a.waypoint,rt0.startpos,rt0.startalt,rt0.winddir,rt0.windvel,rt0.gs,
                        "start","start",1,0,rt0.tas)                            
                for rt in rts:                        
                    add_wp(rt.b.waypoint,rt.endpos,rt.startalt,rt.winddir,rt.windvel,rt.gs,rt.what,rt.legpart,rt.lastsub,rt.d,rt.tas)

            tripobj['waypoints']=waypoints
            response.headers['Content-Type'] = 'text/plain'            
            return json.dumps(tripobj)
        except Exception,cause:
            response.headers['Content-Type'] = 'text/plain'            
            return json.dumps(dict(error=repr(cause)))
        
