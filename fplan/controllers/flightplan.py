import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from fplan.model import meta,User,Trip,Waypoint
from fplan.lib.base import BaseController, render
import sqlalchemy as sa
log = logging.getLogger(__name__)

class FlightplanController(BaseController):

    def index(self):
        # Return a rendered template
        #return render('/flightplan.mako')
        # or, return a response
        c.waypoints=list(meta.Session.query(Waypoint).filter(sa.and_(
             Waypoint.user==session['user'],Waypoint.trip==session['current_trip'])).all())
        
        def get(what,a,b):
            return "42"
        c.get=get
        return render('/flightplan.mako')