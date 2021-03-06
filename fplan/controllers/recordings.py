import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect
from fplan.model import meta,User,Recording,recording_epoch

#from md5 import md5
from fplan.lib.base import BaseController, render
import routes.util as h
from fplan.lib.helpers import md5str
import sqlalchemy as sa
from fplan.lib.recordings import load_recording
from datetime import datetime
log = logging.getLogger(__name__)

class RecordingsController(BaseController):

    def index(self):
        if not 'user' in session:
            redirect(h.url_for(controller='mapview',action="index"))
            return None
        
        c.trips=meta.Session.query(Recording).filter(
            Recording.user==session['user']).order_by(sa.desc(Recording.start)).all()
        return render('/recordings.mako')

    def kml(self,starttime):
        if not 'user' in session:
            return None
        user=session['user']
        print "Rpar:",request.params
        start=int(starttime)
        startd=datetime.utcfromtimestamp(start)
        rec,=meta.Session.query(Recording).filter(sa.and_(
            Recording.user==session['user'],
            Recording.start==startd)).all()
        c.rec=load_recording(rec)
        c.start=startd
        c.zip=zip
        response.content_type = 'application/octet-stream'               
        response.charset="utf8"
        return render("/kml.mako")
        
    def load(self):
        for key,val in request.params.items():
            if key.startswith("view_"):
                start=int(key[5:])
                startd=datetime.utcfromtimestamp(start)
                break
        rec,=meta.Session.query(Recording).filter(sa.and_(
            Recording.user==session['user'],
            Recording.start==startd)).all()
            
        session['showtrack']=load_recording(rec)
        session['showarea']=''
        session['showarea_id']=''
        session.save()
        redirect(h.url_for(controller='mapview',action="zoom",zoom='auto'))
        
                
