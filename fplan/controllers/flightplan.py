import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from fplan.model import meta,User,Trip,Waypoint,Route
from fplan.lib.base import BaseController, render
import sqlalchemy as sa
log = logging.getLogger(__name__)
import fplan.lib.mapper as mapper

class FlightplanController(BaseController):

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
                dict(short='winddir',desc="Wind Direction (deg)",extra=""),
                dict(short='windvel',desc="Wind Velocity (kt)",extra=""),
                dict(short='temp',desc="Outside Air Temperature (C)",extra=""),
                dict(short='alt',desc="Altitude/Flight Level",extra="(Altitude above mean sea level/flight level, e.g 4500ft or FL045)"),
                dict(short='tas',desc="True Air Speed (kt)",extra="(the speed of the aircraft in relation to the air around it)"),
                dict(short='tt',desc="True Track (deg)",extra="(the true direction the aircraft is flying, relative to ground)"),
                dict(short='wca',desc="Wind correction angle (deg)",extra=" (the compensation due to wind needed to stay on the True Track. Negative means you have to aim left, positive to aim right)"),
                dict(short='var',desc="Variation (deg)",extra="(How much to the right of the true north pole, the compass is pointing. Negative numbers means the compass points to the left of the true north pole)"),
                dict(short='dev',desc="Deviation (deg)",extra="(How much to the right of the magnetic north, the aircraft compass will be pointing, while travelling in the direction of the true track)"),
                dict(short='ch',desc="Compass Heading (deg)",extra="(The heading that should be flown on the airplane compass to end up at the right place)"),
                dict(short='dist',desc="Distance (NM)",extra=""),
                dict(short='gs',desc="Ground Speed (kt)",extra=""),
                dict(short='time',desc="Time (minutes)")
                ]
       
        
        
        return render('/flightplan.mako')