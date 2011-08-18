import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from fplan.model import meta,User,Aircraft
import sqlalchemy as sa
import routes.util as h
from fplan.lib.base import BaseController, render
import os

log = logging.getLogger(__name__)

advprops=[
                    'adv_climb_rate',                        
                    'adv_climb_burn',                        
                    'adv_climb_speed',                        
                    'adv_cruise_burn',                        
                    'adv_cruise_speed',                        
                    'adv_descent_rate',                        
                    'adv_descent_burn',                        
                    'adv_descent_speed'                                                 
                     ]

class AircraftController(BaseController):
    def index(self,bad_values=dict(),orig=None):
        cur_acname=session.get('cur_aircraft',None)
        print "Cur aircraft:",cur_acname
        c.ac=None
        if cur_acname:
            cac=meta.Session.query(Aircraft).filter(sa.and_(
                 Aircraft.user==session['user'],
                 Aircraft.aircraft==cur_acname)).all()
            if len(cac)==1:
                c.ac=cac[0]
        if c.ac and c.ac.advanced_model:
            for prop in advprops:
                val=getattr(c.ac,prop)
                if val==None:
                    val=[]
                    l=0
                else:
                    val=list(val)
                    l=len(val)
                val.extend([0 for x in xrange(10-l)])
                setattr(c.ac,prop,tuple(val))
        
                
        def get_msgerror(x):
            msgs=set()
            for alt in xrange(0,10000,1000):
                print "Get",(x,alt),"from",bad_values
                msg=bad_values.get((x,alt),None)
                print "Out",msg
                if msg:
                    msgs.add(msg)
            print "Fetching msgerror for",x,"from",bad_values
            return ", ".join(msgs)
                
        c.msgerror=get_msgerror
        c.fmterror=lambda x,alt=0:'style="background:#ff8080;' if bad_values.get((x,alt),None) else ''
        
        c.newly_added=False
        if request.params.get('flash','')=='new':
            c.flash='A new aircraft was added! Enter its registration/name and other info below.'
            c.newly_added=True
        else:
            c.flash=''
        
        c.all_aircraft=meta.Session.query(Aircraft).filter(sa.and_(
                 Aircraft.user==session['user'])).all()
        if len(c.all_aircraft) and c.ac==None:
            c.ac=c.all_aircraft[0]
        if c.ac:
            c.orig_aircraft=c.ac.aircraft
        else:
            c.orig_aircraft=''
        if orig!=None:
            c.orig_aircraft=orig
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
            if 'advanced_model' in request.params:
                ac.advanced_model=True
                allvalues=dict()
                for prop in advprops:
                    allvalues[prop]=[0 for x in xrange(10)]
                for name,value in request.params.items():
                    print "Processing",name            
                    if name in ('orig_aircraft','advanced_model'): continue
                    if name in ['aircraft','atstype','markings']:
                        setattr(ac,name,value)
                    else:
                        if name.count("_"):
                            prop,alt=name.rsplit("_",1)
                            if hasattr(ac,prop):
                                alt=int(alt)
                                altidx=alt/1000
                                try:
                                    fvalue=float(value)
                                except:
                                    print "Bad:",value
                                    bad_values[(prop,alt)]=u'Must be a decimal number.'
                                    continue
                                allvalues[prop][altidx]=fvalue
                for prop in advprops:
                    setattr(ac,prop,tuple(allvalues[prop]))
                
            else:            
                ac.advanced_model=False
                for name,value in request.params.items():            
                    if name in ('orig_aircraft','advanced_model'): continue
                    if hasattr(ac,name):
                        if name in ['aircraft','atstype','markings']:
                            setattr(ac,name,value)
                        else:
                            try:
                                fvalue=float(value)
                            except:
                                bad_values[(name,0)]=u'Must be a decimal number, like 42.3, not "%s"'%(value,)
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
            print "Bad:",bad
            if bad:
                return self.index(bad,orig=request.params['orig_aircraft'])


            
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
            cur_acname="SE-ABC"
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
            flash='new'
            session['cur_aircraft']=cur_acname
            print "cur_aircraft=",session['cur_aircraft']
            session.save()
        meta.Session.flush()
        meta.Session.commit()
        if 'navigate_to' in request.params and len(request.params['navigate_to'])>0:
            redirect_to(request.params['navigate_to'].encode('utf8'))
        else:
            redirect_to(h.url_for(controller='aircraft',action="index",flash=flash))
        

        
