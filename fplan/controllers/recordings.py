import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from fplan.model import meta,User,Recording

#from md5 import md5
from fplan.lib.base import BaseController, render
import routes.util as h
from fplan.lib.helpers import md5str
import sqlalchemy as sa

log = logging.getLogger(__name__)

class RecordingsController(BaseController):

    def index(self):
        if not 'user' in session:
            redirect_to(h.url_for(controller='mapview',action="index"))
            return None
        
        c.trips=meta.Session.query(Recording).filter(
            Recording.user==session['user']).order_by(sa.desc(Recording.start)).all()
        return render('/recordings.mako')
