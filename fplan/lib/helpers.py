"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to templates as 'h'.
"""
# Import helpers as desired, or define your own, ie:
#from webhelpers.html.tags import checkbox, password
from routes.util import url_for
from itertools import count,izip
import cgi
from md5 import md5
from pylons import request, response, session, tmpl_context as c

def md5str(anystr):
    if type(anystr)==unicode:
        return md5(anystr.encode('utf8')).hexdigest()
    return md5(anystr).hexdigest()

def get_username():
    if session.get('isreg',False):
        return "Logged in as %s&nbsp;&nbsp;"%(cgi.escape(session['user']),)
    return "Anonymous <a href=\"%s\">Create User</a>"%(url_for(controller="profile",action="index"),)
def real_user():        
    if session.get('isreg',False):
        return True
    return False

def fmt_freq(f):
    s="%.3f"%(f,)
    if s.endswith("00"):
        s=s[:-2]
    return s    
def short(x,l):
    """Shorten string x to l chars"""
    if len(x)<l: return x
    return x[:l]+"..." 
        
def jsescape(s):
    return s.replace("'","\\'")
def timefmt(h):
    totmin=int(60*h)
    h=int(totmin//60)
    min_=totmin-h*60
    return "%dh%02dm"%(h,min_)
def clockfmt(h):
    totmin=int(60*h)
    h=int(totmin//60)
    min_=totmin-h*60
    return "%02d:%02d"%(h,min_)
def lfvclockfmt(h):
    totmin=int(60*h)
    h=int(totmin//60)
    min_=totmin-h*60
    return "%02d%02d"%(h,min_)

def parse_clock(s):
    if s.endswith("Z") or s.endswith("z"):
        s=s[:-1]
    if s.count(":"):
        h,m=s.split(":")
        return float(h)+float(m)/60.0
    if s.isdigit():
        if len(s)==4:
            return float(s[0:2])+float(s[2:4])/60.0
        return float(s[0:2])
    raise Exception("Bad clock string:"+s)

