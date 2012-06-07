import logging
import subprocess
import tempfile
from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect
from fplan.model import meta,CustomSet,CustomSets
import sqlalchemy as sa
import routes.util as h
from fplan.lib.base import BaseController, render
from datetime import datetime
import os
import re
import fplan.lib.userdata as userdata

log = logging.getLogger(__name__)

class CustomsetsController(BaseController):
    def index(self):
        
        c.items=[]
        c.flash=""
        maxver = meta.Session.query(CustomSet.setname.label('setname'),
                                    sa.func.max(CustomSet.version).label('maxver')).group_by(CustomSet.setname).subquery()
        
        
        
        c.newset=datetime.strftime(datetime.utcnow(),"%Y-%m-%d %H:%M")
        
        for res in meta.Session.query(CustomSets,maxver).filter(
                    sa.and_(
                        CustomSets.user==session['user'],
                        CustomSets.setname==maxver.c.setname)).all():
            print repr(res)
            custom,setname,maxver=res
            assert setname==custom.setname
            c.items.append(dict(
                    setname=custom.setname,
                    active=custom.active,
                    ready=custom.ready,
                    current=maxver))
        
        return render('/customsets.mako')
    def view(self,setname,version,flash="",data=None):
        version=int(version)
        c.flash=flash
        hits=meta.Session.query(CustomSet).filter(sa.and_(
                                                    CustomSet.user==session['user'],
                                                    CustomSet.setname==setname,
                                                    CustomSet.version==version)).all()
        prev=meta.Session.query(CustomSet).filter(sa.and_(
                                                    CustomSet.user==session['user'],
                                                    CustomSet.setname==setname,
                                                    CustomSet.version==version-1)).all()
                                                    
        next=meta.Session.query(CustomSet).filter(sa.and_(
                                                    CustomSet.user==session['user'],
                                                    CustomSet.setname==setname,
                                                    CustomSet.version==version+1)).all()
        try:
            customset,=meta.Session.query(CustomSets).filter(sa.and_(
                                                    CustomSets.user==session['user'],
                                                    CustomSets.setname==setname)).all()
        except:
            customset=None
                                                    
        print "pn",repr(prev),repr(next)
        if data!=None:
            c.data=data
        else:
            if len(hits)==0:
                c.data="""
{
"obstacles":[
{"name":"Construction Work",
 "pos":"59,18",
 "kind":"Crane",
 "elev":1234,
 "height":123
}
],
"sigpoints":[
{"name":"TestPunkt",
 "pos":"5920N1810E",
 "kind":"sig.point"
}
],
"airfields":[
{"name":"TestPunkt",
 "pos":"5920N1810E",
 "kind":"sig.point",
 "icao":"ABCD",
 "elev":123
}],
"airspaces":[
{
"points":"590000N0180000E-600000N0180000E-600000N0183000E-590000N0183000E",
"name":"Test-area",
"floor":"GND",
"ceiling":"FL55",
"type":"TMA",
"freqs":[["Pahittat Callsign",123.456],["Ett annat pahittat callsign",111.111]]
}
]


}
"""
            else:
                c.data=hits[0].data
        c.cur=version
        c.setname=setname
        if customset:
            c.active=(customset.active==version)
            c.ready=(customset.ready==version)
        else:
            c.active=False
            c.ready=False
        c.haveprev=len(prev)>0
        c.havenext=len(next)>0
        print "Havenext:",c.havenext
        return render('/customset.mako')
            
    def save(self,setname,version):
        version=int(version)
        data=request.params['data']
        
        userdata.purge_user_data(session['user'])
            
        
        def handle_nav():
            if 'prev_button' in request.params:
                redirect(h.url_for(controller='customsets',action="view",setname=setname,version=version-1))
                return True
            if 'next_button' in request.params:
                redirect(h.url_for(controller='customsets',action="view",setname=setname,version=version+1))
                return True
            return False
        
        customsets=meta.Session.query(CustomSets).filter(sa.and_(
                                                    CustomSets.user==session['user'],
                                                    CustomSets.setname==setname)).all()
                                                    
        print "Num matching customsets:",len(customsets),session['user'],setname
        if len(customsets)==0:
            customset=CustomSets(session['user'],setname)
            meta.Session.add(customset)
        else:
            customset,=customsets
            #meta.Session.add(customset)
        
        prevs=meta.Session.query(CustomSet).filter(sa.and_(
                                                    CustomSet.user==session['user'],
                                                    CustomSet.setname==setname,
                                                    CustomSet.version==version)).all()
        if prevs:
            prev,=prevs
            print "PRevdata == data: ",prev.data==data
            print "Prev:",repr(prev.data)
            print "Data:",repr(data)
            if prev.data.strip()==data.strip():
                if handle_nav(): return
                if 'ready' in request.params:
                    customset.ready=version
                else:
                    if customset.ready==version: customset.ready=None
                if 'active' in request.params:
                    customset.active=version
                else:
                    if customset.active==version: customset.active=None

                meta.Session.flush()
                meta.Session.commit()
                    
                return redirect(h.url_for(controller='customsets',action="view",setname=setname,version=version))                    
        
        highver = meta.Session.query(sa.func.max(CustomSet.version).label('highver')).\
            filter(CustomSet.setname==setname).all()
        if not highver or highver[0].highver==None:
            highver=1
        else:
            highver=highver[0].highver+1
            assert type(highver) in [int,long]
        cs=CustomSet(session['user'],setname,highver,data,datetime.utcnow())
        
        
        
        meta.Session.add(cs)
        meta.Session.flush()
        
        print "Updating customsets"
        if 'ready' in request.params:
            customset.ready=highver
        else:
            if customset.ready==version: customset.ready=None
        #if 'active' in request.params:
        customset.active=highver
        #else:
        #    if customset.active==version: customset.active=None
            
        f = tempfile.NamedTemporaryFile(delete=True)
        f.write(data)
        f.flush()
        print "File:",f.name
        p = subprocess.Popen("jsonlint -v "+f.name, shell=True,
                  stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
        (child_stdin,
         child_stdout,
         child_stderr) = (p.stdin, p.stdout, p.stderr)
        child_stdin.close()        
                
        out=child_stderr.read().split(":",1)[-1].strip()
        f.close()
        if out!="":
            return self.view(setname,version,flash="Bad data format: "+out,data=data)
            
        orders=[cs]
        ud=userdata.UserData(session['user'],orders)
        if len(ud.log):
            return self.view(setname,version,flash="Bad data format: "+"<br/>".join(ud.log[0:10]),data=data)
        
        meta.Session.flush()
        meta.Session.commit()
        
        if handle_nav(): return
        
        return redirect(h.url_for(controller='customsets',action="view",setname=setname,version=highver))
