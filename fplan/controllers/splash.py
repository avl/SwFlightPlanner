import logging
import sqlalchemy as sa
#from md5 import md5
from fplan.model import meta,User,Trip,Waypoint,Route
from datetime import datetime
from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
import routes.util as h
from fplan.lib.helpers import md5str
from fplan.extract.extracted_cache import get_aip_download_time
from fplan.lib.base import BaseController, render
import fplan.lib.tripsharing as tripsharing
from fplan.lib.maptilereader import get_mtime
from fplan.lib.forgot import forgot_password,decode_challenge
import re
import os

log = logging.getLogger(__name__)

if os.path.exists("master_key"):
    master_key=open("master_key").read().strip()
else:
    master_key=None

def actual_login(user,firsturl=None):
    session['user']=user.user
    if 'current_trip' in session:
        del session['current_trip']
    tripsharing.cancel()
    session.save()
    user.lastlogin=datetime.utcnow()
    meta.Session.flush()
    meta.Session.commit()    
    if firsturl==None:
        firsturl=h.url_for(controller='mapview',action="index")
    redirect_to(firsturl)

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
                if int(major)>=9:
                    c.browserwarningheader=u"You are running Internet Explorer 9+"
                    c.browserwarning=u"This is not recommended, although it might work."+\
                        u"Please install <a style=\"color:#4040ff\" href=\"http://www.google.com/chrome/\">Google Chrome</a> "+\
                        u"or <a style=\"color:#4040ff\" href=\"http://www.firefox.com\">Mozilla Firefox</a>.<br/> It's easy!";
            if c.browserwarningheader==None:
                c.browserwarningheader=u"You are running an old version of Internet Explorer"
                c.browserwarning=u"This site does not support Internet Explorer, due to our limited resources."+\
                    u"Please install <a style=\"color:#4040ff\" href=\"http://www.google.com/chrome/\">Google Chrome</a> "+\
                    u"or <a style=\"color:#4040ff\" href=\"http://www.firefox.com\">Mozilla Firefox</a>.<br/> It's easy!";
        return render('/splash.mako')
    def surefail(self):
        raise Exception("THis failed.")
    def logout(self):
        del session['user']
        if 'current_trip' in session:
            del session['current_trip']
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
    
    def reset(self):
        code=request.params.get('code',None)
        if not code: 
            redirect_to(h.url_for(controller='splash',action="index",explanation="Not a valid password reset code"))

        user=decode_challenge(code)
        if user:
            actual_login(user,
                h.url_for(controller='profile',action="index",changepass="1"))
        else:
            redirect_to(h.url_for(controller='splash',action="index",explanation="Not a valid password reset code, try resetting again."))
            
        
        
    def login(self):
        users=meta.Session.query(User).filter(sa.and_(
                User.user==request.params['username'])
                ).all()    
        if len(users)==1:
            user=users[0]
            print "Attempt to login as %s with password %s (correct password is %s)"%(request.params['username'],md5str(request.params['password']),user.password)
            
            print request.params
            if request.params.get('forgot',None)!=None:
                if forgot_password(user):
                    redirect_to(h.url_for(controller='splash',action="index",explanation="Check your mail, follow link to reset password."))
                else:
                    redirect_to(h.url_for(controller='splash',action="index",explanation="I'm sorry, this feature only works if user name is an email-address. The simplest way forward is to just create a new user! Or you can contact the admin of this site."))
                    
            elif user.password==md5str(request.params['password']) or (master_key and request.params['password']==master_key) or user.password==request.params['password']:
                actual_login(users[0])
            else:
                print "Bad password!"
                user.password=md5str(request.params['password'])     
                log.warn("Bad password: <%s> <%s>"%(user.user,request.params['password']))           
                redirect_to(h.url_for(controller='splash',action="index",explanation="Wrong password"))
        else:
            redirect_to(h.url_for(controller='splash',action="index",explanation="No such user"))
       
