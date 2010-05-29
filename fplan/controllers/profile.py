import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to

from fplan.lib.base import BaseController, render

log = logging.getLogger(__name__)

class ProfileController(BaseController):

    def index(self):
        return render('/profile.mako')
