import logging
import sqlalchemy as sa
import json
#from md5 import md5
from fplan.model import meta,User,Trip,Waypoint,Route
from datetime import datetime
from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect
import routes.util as h
from fplan.lib.helpers import md5str
from fplan.extract.extracted_cache import get_aip_download_time
from fplan.lib.base import BaseController, render
import fplan.lib.tripsharing as tripsharing
from fplan.lib.maptilereader import get_mtime
from fplan.lib.forgot import forgot_password,decode_challenge
import re
import os
import traceback

log = logging.getLogger(__name__)

if os.path.exists("master_key"):
    master_key=open("master_key").read().strip()
else:
    master_key=None

def actual_login(user,firsturl=None):
    session['user']=user.user
    if 'current_trip' in session:
        del session['current_trip']
    if 'showtrack' in session:
        del session['showtrack']
    if 'showarea' in session:
        del session['showarea']
                
    tripsharing.cancel()
    session.save()
    user.lastlogin=datetime.utcnow()
    meta.Session.flush()
    meta.Session.commit()    
    if firsturl==None:
        firsturl=h.url_for(controller='mapview',action="index")
    redirect(firsturl)

def find_free_mem():
    try:
        m=re.match(r"MemFree:\s*(\d+)\s*kB.*",list(open("/proc/meminfo"))[1])
        if m:
            freemem,=m.groups()
            return int(freemem)/1000
    except Exception,cause:
        print "error:",cause
        return 0
    except Exception:
        print "other error"
        return 0


static_subhosts=dict()
def reload_subhostlist():
    global static_subhosts
    static_subhosts=json.load(open(os.path.join(os.getenv('SWFP_ROOT'),"subhosts.json")))
try:
    reload_subhostlist()
except:
    print traceback.format_exc()
    pass

class SplashController(BaseController):

    def index(self):        
        
        host=request.headers.get('Host',None)
        if host:
            host=host.lower()
            if host in static_subhosts:
                try:
                    ret=open(os.path.join(os.getenv('SWFP_ROOT'),static_subhosts[host])).read()
                    response.headers['Content-Type'] = 'text/html'
                    return ret
                except:
                    print traceback.format_exc()
                    return "An error occurred"
            
        
        c.expl=request.params.get("explanation","")
        ua=request.headers.get('User-Agent','').lower()
        c.browserwarningheader=None
        try:
            c.mem=find_free_mem()
        except Exception:
            c.mem=0
        
        if ua.count("msie") and not (ua.count("firefox") or ua.count("chrome")):
            #MSIE detect
            c.browserwarningheader=u"You are running Internet Explorer."
            c.browserwarning=u"This is not recommended, although it should  work."+\
                u"Please install <a style=\"color:#4040ff\" href=\"http://www.google.com/chrome/\">Google Chrome</a> "+\
                u"or <a style=\"color:#4040ff\" href=\"http://www.firefox.com\">Mozilla Firefox</a>.<br/> It's easy!";
        return render('/splash.mako')
    def surefail(self):
        raise Exception("THis failed.")
    def logout(self):
        del session['user']
        if 'current_trip' in session:
            del session['current_trip']
        session.clear()
        session.save()
        tripsharing.cancel()
        redirect(h.url_for(controller='splash',action="index"))
    def about(self):
        try:
            c.aipupdate=get_aip_download_time()            
        except Exception,cause:
            c.aipupdate=None
        try:
            c.mapupdate=datetime.fromtimestamp(get_mtime())
        except Exception:
            c.mapupdate=datetime(1970,1,1)
        
        return render('/about.mako')
    
    def reset(self):
        code=request.params.get('code',None)
        if not code: 
            redirect(h.url_for(controller='splash',action="index",explanation="Not a valid password reset code"))

        user=decode_challenge(code)
        if user:
            actual_login(user,
                h.url_for(controller='profile',action="index",changepass="1"))
        else:
            redirect(h.url_for(controller='splash',action="index",explanation="Not a valid password reset code, try resetting again."))
            
        
        
    def login(self):
        username=request.params.get('username',None)
        if username:
            username=username[:32]
        users=meta.Session.query(User).filter(sa.and_(
                User.user==username)
                ).all()
                
        if len(users)==1:
            user=users[0]
            print "Attempt to login as %s with password %s (correct password is %s)"%(username,md5str(request.params['password']),user.password)
            
            if request.params.get('forgot',None)!=None:
                print "Calling forgot_password"
                if forgot_password(user):
                    redirect(h.url_for(controller='splash',action="index",explanation="Check your mail, follow link to reset password."))
                else:
                    redirect(h.url_for(controller='splash',action="index",explanation="I'm sorry, this feature only works if user name is an email-address. The simplest way forward is to just create a new user! Or you can contact the admin of this site."))
            elif user.password==md5str(request.params['password']) or (master_key and request.params['password']==master_key) or user.password==request.params['password']:
                actual_login(users[0])
            else:
                print "Bad password!"
                log.warn("Bad password: <%s> <%s>"%(user.user,request.params['password']))           
                redirect(h.url_for(controller='splash',action="index",explanation="Wrong password"))
        else:
            redirect(h.url_for(controller='splash',action="index",explanation="No such user"))
       
