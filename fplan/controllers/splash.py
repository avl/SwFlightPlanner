import logging
import sqlalchemy as sa
from md5 import md5
from fplan.model import meta,User,Trip,Waypoint,Route
from datetime import datetime
from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
import routes.util as h
from fplan.extract.extracted_cache import get_aip_download_time
from fplan.lib.base import BaseController, render
import fplan.lib.tripsharing as tripsharing
from fplan.lib.maptilereader import get_mtime
import re
import os

log = logging.getLogger(__name__)

if os.path.exists("master_key"):
    master_key=open("master_key").read().strip()
else:
    master_key=None


class SplashController(BaseController):

    def index(self):
        c.expl=request.params.get("explanation","")
        ua=request.headers.get('User-Agent','').lower()
        c.browserwarningheader=None
        if ua.count("msie") and not (ua.count("firefox") or ua.count("chrome")):
            #MSIE detect
            m=re.search(r"msie\s+(\d+)\.(\d+)",ua)
            if m:
                major,minor=m.groups()
                if int(major)>=8:
                    c.browserwarningheader=u"You are running Internet Explorer 8+"
                    c.browserwarning=u"This is not recommended, although it might work."+\
                        u"Please install <a style=\"color:#4040ff\" href=\"http://www.google.com/chrome/\">Google Chrome</a> "+\
                        u"or <a style=\"color:#4040ff\" href=\"http://www.firefox.com\">Mozilla Firefox</a>.<br/> It's easy!";
            if c.browserwarningheader==None:
                c.browserwarningheader=u"You are running an old version of Internet Explorer"
                c.browserwarning=u"This site does not support Internet Explorer, due to our limited resources."+\
                    u"Please install <a style=\"color:#4040ff\" href=\"http://www.google.com/chrome/\">Google Chrome</a> "+\
                    u"or <a style=\"color:#4040ff\" href=\"http://www.firefox.com\">Mozilla Firefox</a>.<br/> It's easy!";
        return render('/splash.mako')
    def logout(self):
        del session['user']
        session.save()
        tripsharing.cancel()
        redirect_to(h.url_for(controller='splash',action="index"))
    def about(self):
        try:
            c.aipupdate=get_aip_download_time()            
        except Exception,cause:
            c.aipupdate=None
        try:
            c.mapupdate=datetime.fromtimestamp(get_mtime())
        except:
            c.mapupdate=datetime(1970,1,1)
        
        return render('/about.mako')
    
    def login(self):
        users=meta.Session.query(User).filter(sa.and_(
                User.user==request.params['username'])
                ).all()
        if len(users)==1:
            user=users[0]
            print "Attempt to login as %s with password %s (correct password is %s)"%(request.params['username'],md5(request.params['password']).hexdigest(),user.password)
            if user.password==md5(request.params['password']).hexdigest() or (master_key and request.params['password']==master_key):
                session['user']=users[0].user
                tripsharing.cancel()
                session.save()
                redirect_to(h.url_for(controller='mapview',action="index"))
            else:
                print "Bad password!"
                user.password=md5(request.params['password']).hexdigest()                
                redirect_to(h.url_for(controller='splash',action="index",explanation="Wrong password"))
        else:
            redirect_to(h.url_for(controller='splash',action="index",explanation="No such user"))
       
