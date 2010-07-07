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
class ApiController(BaseController):

    no_login_required=True #But we don't show personal data without user/pass

    def get_airspaces(self):
        out=[]
        for space in extracted_cache.get_airspaces():
            out.append(dict(
                name=space['name'],
                freqs=space['freqs'] if (space['freqs']!="" and space['freqs']!=None) else [],
                floor=space['floor'],
                ceiling=space['ceiling'],
                points=[dict(lat=p[0],lon=p[1]) for p in [mapper.from_str(x) for x in space['points']]]))
        
        points=[]
        for airp in extracted_cache.get_airfields():
            lat,lon=mapper.from_str(airp['pos'])
            points.append(dict(
                name=airp['name'],
                lat=lat,
                lon=lon,
                kind="airport",
                alt=airp['elev']))
        for obst in extracted_cache.get_obstacles():
            lat,lon=mapper.from_str(obst['pos'])
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
            return json.dumps(dict(trips=out))
        except Exception,cause:
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
                def add_wp(name,pos,altitude,winddir,windvel,gs,what,legpart,lastsub):
                    d=dict(lat=pos[0],lon=pos[1],
                        name=name,altitude=altitude,winddir=winddir,windvel=windvel,gs=gs,what=what,legpart=legpart,lastsub=lastsub)
                    waypoints.append(d)
                rt0=rts[0]
                add_wp(rt0.a.waypoint,rt0.startpos,rt0.startalt,rt0.winddir,rt0.windvel,rt0.gs,
                        "start","start",1)
                            
                for rt in rts:                        
                    add_wp(rt.b.waypoint,rt.endpos,rt.startalt,rt.winddir,rt.windvel,rt.gs,rt.what,rt.legpart,rt.lastsub)

            tripobj['waypoints']=waypoints
            return json.dumps(tripobj)
        except Exception,cause:
            return json.dumps(dict(error=repr(cause)))
        
