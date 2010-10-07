import logging
from fplan.model import meta,User,Trip,Waypoint,Route

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from md5 import md5
from fplan.lib.base import BaseController, render
import routes.util as h
from fplan.extract.extracted_cache import get_aip_download_time

log = logging.getLogger(__name__)

class ProfileController(BaseController):

    def index(self):
        user=meta.Session.query(User).filter(
                User.user==session['user']).one()
        print "index as user:",user.user,user.isregistered
        c.splash=request.params.get('splash','')
        c.user=user.user
        c.password=''
        print "User realname:",user.realname
        c.phonenr=user.phonenr
        c.realname=user.realname
        c.initial=not user.isregistered
        c.notfastmap=not user.fastmap
        try:
            c.aipupdate=get_aip_download_time()
        except Exception,cause:
            c.aipupdate=None
        return render('/profile.mako')
    def save(self):
        print "in save:",request.params
        user=meta.Session.query(User).filter(
                User.user==session['user']).one()
        print "As user:",user.user
        
        name_busy=False
        if meta.Session.query(User).filter(User.user==request.params.get("username")).count():
            name_busy=True
        else:
            user.user=request.params.get('username',user.user)
        user.phonenr=request.params.get('phonenr',user.phonenr)
        user.realname=request.params.get('realname',user.realname)
        if request.params.get("password1",'')!='' and request.params.get('password2','')!='':
            if request.params["password1"]==request.params["password2"]:
                user.password=md5(request.params['password1']).hexdigest()
            else:
                redirect_to(h.url_for(controller='profile',action="index",splash=u"Passwords do not match! Enter the same password twice."))
        user.isregistered=True
        if 'notfastmap' in request.params:
            user.fastmap=False
        else:
            user.fastmap=True
        
        session['user']=user.user
        session.save()
        meta.Session.flush()
        meta.Session.commit();
        if name_busy:
            redirect_to(h.url_for(controller='profile',action="index",splash=u"That username is already taken. Try some other name."))
            return 
        
        redirect_to(h.url_for(controller='profile',action="index"))
        
            
