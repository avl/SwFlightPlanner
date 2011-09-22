"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to templates as 'h'.
"""
# Import helpers as desired, or define your own, ie:
#from webhelpers.html.tags import checkbox, password
from routes.util import url_for
from itertools import count,izip,chain
import cgi
from md5 import md5
from pylons import request, response, session, tmpl_context as c
from datetime import datetime,timedelta
import mapper
import math
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
    if h==None:
        return "--"
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

def utcdatetime2stamp(d):
    assert d.microsecond==0
    delta=d-datetime(1970,1,1)
    stamp=int(delta.days*86400+delta.seconds)
    check=datetime.utcfromtimestamp(stamp)
    if check-d!=timedelta(0):
        raise Exception("Unexpected internal error converting times")
    return stamp
def utcdatetime2stamp_inexact(d):
    delta=d-datetime(1970,1,1)
    stamp=int(delta.days*86400+delta.seconds)    
    return stamp
def degmin(dec):
    if dec==None: return ""    
    neg=""
    if dec<0:
        neg="-1"
        dec=-dec
    deg,min=mapper._to_deg_min(dec+(1e-7))
    ret=("%s%d %07.4f"%(neg,deg,min))
    ret=ret.rstrip("0")
    if ret.endswith("."):
        ret=ret[:-1]
    return ret

def foldable_links(htmlid,urls):    
    out=["""<div id="%(id)s" class="foldable"><div>
    <a href="#" onclick="show_foldedlink('%(id)s');return false;"><u>Show Links...</u></a>
    </div><div style="display:none">
    Links:<br/>
    <ul>
    """%dict(id=htmlid)]
    
    for url,desc in urls:
        if not url: continue            
        out.append("<li><u><a href=\"%s\">%s</a></u></li>"%(cgi.escape(url),cgi.escape(desc)))
    out.append("</ul></div></div>")
    return "\n".join(out)
    
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

def calc_air_density(altitude):
    return 1.22521 * ((288.15+-0.0065*(altitude*0.3048))/(288.15))**((-1*9.80665*0.0289644/( 8.31432 *-0.0065))-1.0)
def calc_tas(cas,alt):
    return cas*math.sqrt(1.22521/calc_air_density(alt))
def calc_cas(tas,alt):
    return tas/math.sqrt(1.22521/calc_air_density(alt))
