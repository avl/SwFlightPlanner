import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from fplan.model import meta,User,Aircraft
import sqlalchemy as sa
import routes.util as h
from fplan.lib.base import BaseController, render
import os
import re

log = logging.getLogger(__name__)

advprops=[
                    'adv_cruise_speed',                        
                    'adv_cruise_burn',                        
                    'adv_climb_speed',                        
                    'adv_climb_rate',                        
                    'adv_climb_burn',                        
                    'adv_descent_speed',                                                 
                    'adv_descent_rate',                        
                    'adv_descent_burn',                        
                     ]

class AircraftController(BaseController):
    def index(self,bad_values=dict(),orig=None):
        cur_acname=session.get('cur_aircraft',None)
        c.ac=None
        if cur_acname:
            cac=meta.Session.query(Aircraft).filter(sa.and_(
                 Aircraft.user==session['user'],
                 Aircraft.aircraft==cur_acname)).all()
            if len(cac)==1:
                c.ac=cac[0]
        if c.ac and c.ac.advanced_model:
            
            print "adv climb rate",c.ac.adv_climb_rate
            for prop in advprops:
                print "prop",prop,"val:",getattr(c.ac,prop)
            if all(getattr(c.ac,prop)==() for prop in advprops):
                #Default-values for Cessna 172 with 160hp engine.
                c.ac.adv_climb_rate=   [770,725,675,630,580,535,485,440,390,345]                        
                c.ac.adv_climb_burn=   [62, 60, 55, 50, 45, 42, 40, 37, 35, 33]
                c.ac.adv_climb_speed=  [73, 73, 72, 72, 71, 71, 70, 69, 69, 68]
                c.ac.adv_cruise_burn=  [32, 32, 32, 32, 32, 32, 32, 32,31.5,31]
                c.ac.adv_cruise_speed= [116,117,118,119,120,121,122,122,122,122]                        
                c.ac.adv_descent_rate= [400,400,400,400,400,400,400,400,400,400]
                c.ac.adv_descent_burn= [25, 25, 25, 25, 25, 25, 25, 25, 25, 25]                       
                c.ac.adv_descent_speed=[116,117,118,119,120,121,122,122,122,122]                                                
            
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
            c.adv_props=[
                ("Cruise Speed (kt TAS)","adv_cruise_speed"),
                ("Cruise Consumption (L/h)","adv_cruise_burn"),
                ("Climb Speed (kt TAS)","adv_climb_speed"),
                ("Climb Rate (fpm)","adv_climb_rate"),                        
                ("Climb Consumption (L/h)","adv_climb_burn"),                        
                ("Descent Speed (kt TAS)","adv_descent_speed"),                                                 
                ("Descent Rate (fpm)","adv_descent_rate"),                        
                ("Descent Consumption (L/h)","adv_descent_burn")                        
                ]
            def getval(prop,alt):
                ialt=alt/1000
                raw=getattr(c.ac,prop)[ialt]
                s="%.1f"%(raw,)
                if s.endswith(".0"):
                    return s[:-2]
                return s
            c.getval=getval
                
        def get_msgerror(x):
            msgs=set()
            for alt in xrange(0,10000,1000):
                msg=bad_values.get((x,alt),None)
                if msg:
                    msgs.add(msg)
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
        cac=meta.Session.query(Aircraft).filter(sa.and_(
            Aircraft.user==session['user'],
            Aircraft.aircraft==acname)).all()
                    
        bad_values=dict()
        if len(cac)==1:
            ac,=cac
            if ac.advanced_model:
                if 'add_from_text' in request.params:
                    add_from_text=request.params['add_from_text'].strip()!=""
                else:
                    add_from_text=False
                allvalues=dict()
                for prop in advprops:
                    allvalues[prop]=[0 for x in xrange(10)]
                print "Using advanced model"
                for name,value in request.params.items():
                    if name in ('orig_aircraft','advanced_model'): continue
                    if name in ['aircraft','atstype','markings']:
                        setattr(ac,name,value)
                    else:
                        if not add_from_text and name.count("_"):
                            prop,alt=name.rsplit("_",1)
                            if hasattr(ac,prop):
                                alt=int(alt)
                                altidx=alt/1000
                                try:
                                    fvalue=float(value)
                                except:
                                    bad_values[(prop,alt)]=u'Must be a decimal number.'
                                    continue
                                allvalues[prop][altidx]=fvalue
                if add_from_text:
                    lines=[x.strip() for x in request.params['add_from_text'].split("\n") if x.strip()]
                    for line,prop in zip(lines,advprops):
                        print "Finding line",line
                        for idx,nums in enumerate(re.findall(r"\b\d+\.?\d*\b",line)):
                            print "Finding nums",nums
                            num=float(nums)
                            allvalues[prop][idx]=num                                
                            
                for prop in advprops:
                    setattr(ac,prop,tuple(allvalues[prop]))
                    
                    
                
            else:            
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
            if 'advanced_model' in request.params:
                ac.advanced_model=True
            else:
                ac.advanced_model=False
            
            session['cur_aircraft']=request.params['aircraft']
            session.save()                  
        return bad_values
                 
    def save(self):
        if hasattr(self,'idx'):
            self.idx+=1
        else:
            self.idx=1
        if 'orig_aircraft' in request.params:
            bad=self.do_save()
            if bad:
                return self.index(bad,orig=request.params['orig_aircraft'])


            
        if request.params.get('del_button',False):
            meta.Session.query(Aircraft).filter(sa.and_(
                    Aircraft.user==session['user'],
                    Aircraft.aircraft==request.params['orig_aircraft'])).delete()
            session['cur_aircraft']=None
            session.save()
            
        if request.params.get('change_aircraft',None)!=request.params.get('orig_aircraft',None) and request.params.get('change_aircraft',False):
            session['cur_aircraft']=request.params['change_aircraft']
            session.save()
        flash=None
        if request.params.get('add_button',False):
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
            a.advanced_model=False
            meta.Session.add(a)
            flash='new'
            session['cur_aircraft']=cur_acname
            session.save()
        meta.Session.flush()
        meta.Session.commit()
        if 'navigate_to' in request.params and len(request.params['navigate_to'])>0:
            redirect_to(request.params['navigate_to'].encode('utf8'))
        else:
            redirect_to(h.url_for(controller='aircraft',action="index",flash=flash))
        

        
