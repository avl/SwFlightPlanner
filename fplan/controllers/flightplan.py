import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from fplan.model import meta,User,Trip,Waypoint,Route,Airport
from fplan.lib.base import BaseController, render
import sqlalchemy as sa
log = logging.getLogger(__name__)
import fplan.lib.mapper as mapper
import json
import re

class FlightplanController(BaseController):
    def search(self):
        searchstr=request.params.get('search','')

        latlon_match=re.match(r"(\d+)\.(\d+)([NS])(\d+)\.(\d+)([EW])",searchstr)
        print "latlon_match",latlon_match
        if latlon_match:
            latdeg,latdec,ns,londeg,londec,ew=latlon_match.groups()
            lat=float(latdeg)+float("0."+latdec)
            lon=float(londeg)+float("0."+londec)
            if ns in ['S','s']:
                lat=-lat
            if ew in ['W','w']:
                lon=-lon
            print "latlon",lat,lon
            return json.dumps([['Unknown Waypoint',[lat,lon]]])                


        print "Searching for ",searchstr
        airports=meta.Session.query(Airport).filter(
                sa.or_(Airport.airport.like('%%%s%%'%(searchstr,)),
                Airport.icao.like('%%%s%%'%(searchstr,)))
                ).limit(20).all()    
        if len(airports)==0:
            return ""        
        ret=json.dumps([[x.airport,mapper.from_str(x.pos)] for x in airports])
        print "returning json:",ret
        return ret   
  

    def index(self):
        # Return a rendered template
        #return render('/flightplan.mako')
        # or, return a response
        c.waypoints=list(meta.Session.query(Waypoint).filter(sa.and_(
             Waypoint.user==session['user'],Waypoint.trip==session['current_trip'])).all())
        
        
            
        def get(what,a,b):
            print "A:",a
            if what=='tt':
                bear,dist=mapper.bearing_and_distance(a.pos,b.pos)
                return "%03.0f"%(bear,)
            if what in ['winddir','windvel','temp','var','alt','tas']:
                routes=meta.Session.query(Route).filter(sa.and_(
                    Route.user==session['user'],Route.trip==session['current_trip'],
                    Route.waypoint1==a.pos,Route.waypoint2==b.pos)).all()
                
                if len(routes)==1:
                    route=routes[0]
                    if what=='winddir':
                        return route.winddir
                    elif what=='windvel':
                        return route.windvel
                    elif what=='var':
                        return route.variation
                    elif what=='alt':
                        return route.altitude                    
                    elif what=='tas':
                        return route.tas
                return ""            
                
            return "42"
        c.get=get

         
        c.cols=[
                dict(width=3,short='W',desc="Wind Direction (deg)",extra=""),
                dict(width=2,short='V',desc="Wind Velocity (kt)",extra=""),
                #dict(width=3,short='Temp',desc="Outside Air Temperature (C)",extra=""),
                dict(width=5,short='Alt',desc="Altitude/Flight Level",extra="(Altitude above mean sea level/flight level, e.g 4500ft or FL045)"),
                dict(width=3,short='TAS',desc="True Air Speed (kt)",extra="(the speed of the aircraft in relation to the air around it)"),
                dict(width=3,short='TT',desc="True Track (deg)",extra="(the true direction the aircraft is flying, relative to ground)"),
                dict(width=2,short='WCA',desc="Wind correction angle (deg)",extra=" (the compensation due to wind needed to stay on the True Track. Negative means you have to aim left, positive to aim right)"),
                dict(width=2,short='Var',desc="Variation (deg)",extra="(How much to the right of the true north pole, the compass is pointing. Negative numbers means the compass points to the left of the true north pole)"),
                dict(width=2,short='Dev',desc="Deviation (deg)",extra="(How much to the right of the magnetic north, the aircraft compass will be pointing, while travelling in the direction of the true track)"),
                dict(width=3,short='CH',desc="Compass Heading (deg)",extra="(The heading that should be flown on the airplane compass to end up at the right place)"),
                dict(width=3,short='D',desc="Distance (NM)",extra=""),
                dict(width=3,short='GS',desc="Ground Speed (kt)",extra=""),
                dict(width=3,short='Time',desc="Time (minutes)",extra="")
                ]
       
        
        
        return render('/flightplan.mako')