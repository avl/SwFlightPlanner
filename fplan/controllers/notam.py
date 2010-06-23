import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from fplan.model import *
from fplan.lib.base import BaseController, render
import sqlalchemy as sa
log = logging.getLogger(__name__)

class NotamController(BaseController):

    def index(self):
        c.notamupdates=\
            list(meta.Session.query(NotamUpdate).filter(
                NotamUpdate.disappearnotam==sa.null()).order_by([sa.desc(NotamUpdate.appearnotam),sa.asc(NotamUpdate.appearline)]).all())
        return render('/notam.mako')

