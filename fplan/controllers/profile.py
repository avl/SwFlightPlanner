import logging
from fplan.model import meta,User,Trip,Waypoint,Route

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from md5 import md5
from fplan.lib.base import BaseController, render
import routes.util as h

log = logging.getLogger(__name__)

class ProfileController(BaseController):

    def index(self):
        user=meta.Session.query(User).filter(
                User.user==session['user']).one()
        print "index as user:",user.user,user.isregistered
        c.splash=request.params.get('splash','')
        c.user=user.user
        c.password=''
        c.initial=not user.isregistered
        return render('/profile.mako')
    def save(self):
        print "in save:",request.params
        user=meta.Session.query(User).filter(
                User.user==session['user']).one()
        print "As user:",user.user
        user.user=request.params.get('username',user.user)
        if request.params.get("password1",'')!='':
            if request.params["password1"]==request.params["password2"]:
                user.password=md5(request.params['password1']).hexdigest()
            else:
                redirect_to(h.url_for(controller='profile',action="index",splash=u"Passwords do not match! Enter the same password twice."))
        user.isregistered=True
            
        
        session['user']=user.user
        session.save()
        meta.Session.flush()
        meta.Session.commit();
        redirect_to(h.url_for(controller='profile',action="index"))
        
            