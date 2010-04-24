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
        return render('/flightplan.mako')