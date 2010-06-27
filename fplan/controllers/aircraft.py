import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from fplan.model import meta,User,Aircraft
import sqlalchemy as sa
import routes.util as h
from fplan.lib.base import BaseController, render
import os

log = logging.getLogger(__name__)

class AircraftController(BaseController):

    def index(self,bad_values=dict()):
        cur_acname=session.get('cur_aircraft',None)
        print "Cur aircraft:",cur_acname
        c.ac=None
        if cur_acname:
             cac=meta.Session.query(Aircraft).filter(sa.and_(
                 Aircraft.user==session['user'],
                 Aircraft.aircraft==cur_acname)).all()
             if len(cac)==1:
                c.ac=cac[0]
        
                
        c.msgerror=lambda x:bad_values.get(x,'')
        c.fmterror=lambda x:'style="background:#ff8080;' if bad_values.get(x,None) else ''
        c.flash=request.params.get('flash','')
        c.all_aircraft=meta.Session.query(Aircraft).filter(sa.and_(
                 Aircraft.user==session['user'])).all()
        if len(c.all_aircraft) and c.ac==None:
            c.ac=c.all_aircraft[0]
        return render('/aircraft.mako')
    
    def do_save(self):
        acname=request.params['orig_aircraft']
        print "In DO-save"
        cac=meta.Session.query(Aircraft).filter(sa.and_(
            Aircraft.user==session['user'],
            Aircraft.aircraft==acname)).all()
        print "Num matching craft:",len(cac)
        bad_values=dict()
        if len(cac)==1:
            ac,=cac            
            for name,value in request.params.items():            
                if name=='orig_aircraft': continue
                if hasattr(ac,name):
                    if name=='aircraft':
                        ac.aircraft=value
                    else:
                        try:
                            fvalue=float(value)
                        except:
                            bad_values[name]=u'Must be a decimal number, like 42.3, not "%s"'%(value,)
                            continue
                        setattr(ac,name,fvalue)
            session['cur_aircraft']=request.params['aircraft']
            session.save()                  
        print "Returning from do_save"
        return bad_values
                 
    def save(self):
        print "in save()"
        if hasattr(self,'idx'):
            self.idx+=1
        else:
            self.idx=1
        print "aircraft.save idx=",self.idx,request.params,"pid:",os.getpid()
        if 'orig_aircraft' in request.params:
            bad=self.do_save()
            if bad:
                return self.index(bad)
            
        if request.params.get('del_button',False):
            print "del button"
            meta.Session.query(Aircraft).filter(sa.and_(
                    Aircraft.user==session['user'],
                    Aircraft.aircraft==request.params['orig_aircraft'])).delete()
            session['cur_aircraft']=None
            session.save()
            
        if request.params.get('change_aircraft',None)!=request.params.get('orig_aircraft',None) and request.params.get('change_aircraft',False):
            print "Change aircraft"
            session['cur_aircraft']=request.params['change_aircraft']
            session.save()
        print "Request params:",request.params
        flash=None
        if request.params.get('add_button',False):
            print "add button"
            i=None
            cur_acname="Enter name"
            while True:
                if i!=None:
                    cur_acname+="(%d)"%(i,)
                if meta.Session.query(Aircraft).filter(sa.and_(
                    Aircraft.user==session['user'],
                    Aircraft.aircraft==cur_acname)).count()==0:
                    break
                if i==None: i=2
                else: i+=1                
            a=Aircraft(session['user'],cur_acname)
            meta.Session.add(a)
            flash='A new aircraft was added! Enter its registration/name and other info below.'
            session['cur_aircraft']=cur_acname
            print "cur_aircraft=",session['cur_aircraft']
            session.save()
        meta.Session.flush()
        meta.Session.commit()
        if 'navigate_to' in request.params and len(request.params['navigate_to'])>0:
            redirect_to(request.params['navigate_to'].encode('utf8'))
        else:
            redirect_to(h.url_for(controller='aircraft',action="index",flash=flash))
        

        
