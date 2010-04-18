import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from fplan.model import meta,User
import fplan.lib.mapper as mapper
from fplan.lib.base import BaseController, render

log = logging.getLogger(__name__)

class MapviewController(BaseController):

    def index(self):
        # Return a rendered template
        user=meta.Session.query(User).filter(
                User.user==session['user']).one()
        
        c.pos=mapper.to_aviation_format(mapper.from_str(user.last_map_pos))
        c.size=user.last_map_size
        return render('/mapview.mako')
        # or, return a response
        #return 'Hello World'
