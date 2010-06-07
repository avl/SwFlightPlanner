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

    def index(self):
        cur_acname=session.get('cur_aircraft',None)
        print "Cur aircraft:",cur_acname
        c.ac=None
        if cur_acname:
             cac=meta.Session.query(Aircraft).filter(sa.and_(
                 Aircraft.user==session['user'],
                 Aircraft.aircraft==cur_acname)).all()
             if len(cac)==1:
                c.ac=cac[0]
        
                

            
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
        if len(cac)==1:
            ac,=cac            
            for name,value in request.params.items():            
                if name=='orig_aircraft': continue
                if hasattr(ac,name):
                    setattr(ac,name,value)
                            
        print "Returning from do_save"
                 
    def save(self):
        print "in save()"
        if hasattr(self,'idx'):
            self.idx+=1
        else:
            self.idx=1
        print "aircraft.save idx=",self.idx,request.params,"pid:",os.getpid()
        if 'orig_aircraft' in request.params:
            self.do_save()
        if 'add_button' in request.params:            
            i=None
            cur_acname="SE-XYZ"
            while True:
                if i!=None:
                    cur_acname+="(%d)"%(i,)
                if meta.Session.query(Aircraft).filter(sa.and_(
                    Aircraft.user==session['user'],
                    Aircraft.aircraft==cur_acname)).count()==0:
                    break
                if i==None: i=2
                else: i+=1                
            a=Aircraft()
            a.user=session['user']
            a.aircraft=cur_acname
            meta.Session.add(a)
            session['cur_aircraft']=cur_acname
            session.save()
        if 'change_aircraft' in request.params:
            session['cur_aircraft']=request.params['change_aircraft']
            session.save()
        if 'del_button' in request.params:
            meta.Session.query(Aircraft).filter(sa.and_(
                    Aircraft.user==session['user'],
                    Aircraft.aircraft==request.params['orig_aircraft'])).delete()
            session['cur_aircraft']=None
            session.save()
        meta.Session.flush()
        meta.Session.commit()
        if 'navigate_to' in request.params and len(request.params['navigate_to'])>0:
            redirect_to(request.params['navigate_to'].encode('utf8'))
        else:
            redirect_to(h.url_for(controller='aircraft',action="index"))
        

        
