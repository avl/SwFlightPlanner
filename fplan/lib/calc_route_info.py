#encoding=utf8
from fplan.model import meta,User,Trip,Waypoint,Route,Aircraft
import fplan.lib.mapper as mapper
import math
import sqlalchemy as sa
from fplan.lib.get_terrain_elev import get_terrain_elev
from fplan.extract.extracted_cache import get_airfields
from fplan.lib.airspace import get_pos_elev
from fplan.lib.helpers import parse_clock
from fplan.lib.geomag import calc_declination
from datetime import datetime,timedelta
from copy import copy
from time import time

def parse_date(s):
    if s.count("-")==2:
        y,m,d=s.split("-")
        return datetime(int(y),int(m),int(d),0,0,0,0)
    if s.isdigit() and len(s)==8:
        return datetime(int(s[0:4]),int(s[4:6]),int(s[6,8]),0,0,0,0)
    raise Exception("Couldn't parse date %s"%(s,))

def wind_computer(winddir,windvel,tt,tas):
    f=1.0/(180.0/math.pi)
    wca=0
    GS=0

    winddir=(winddir+180) - tt
    windx=math.cos(winddir*f)*windvel
    windy=math.sin(winddir*f)*windvel
    if abs(windy)>tas:
        if windy>tas:
            wca=-90
        else:
            wca=90
        GS=0
    else:
        if (-windx<tas):
            wca=-math.asin(windy/tas)/f                
            tas_x=math.cos(wca*f)*tas
            tas_y=math.sin(wca*f)*tas
            GS = math.sqrt((tas_x+windx)*(tas_x+windx)+(tas_y+windy)*(tas_y+windy))
        else:
            wca=0
            GS=0
    return GS,wca

class TechRoute(object):
    pass
    
def from_feet(x): return x*0.3048
def to_feet(x): return x/0.3048
def from_nm(x): return x*1852.0
def from_fpm(x): return x*0.3048/60.0
def to_nm(x): return x/1852.0
def feet_to_nm(x): return x/(1852.0*0.3048)
def nm_to_feet(x): return x*(1852.0*0.3048)

def adv_cap_mid_alt(alt1,mid_alt,alt2,d,ac,rt):
    if alt1<=mid_alt and mid_alt<=alt2: return to_feet(mid_alt)
error continue here.
    if alt1<mid_alt:
        #climb
        meetalt=None
        while True:
            d=rt.d
            climb_ratio=calc_climb_ratio(ac,rt,alt1)
            descent_ratio=calc_descent_ratio(ac,rt,alt2)
            na1=int(alt1)-int(alt1)%1000+1000
            na2=int(alt2)-int(alt2)%1000+1000
            next_d1=na1/climb_ratio
            next_d2=na2/descent_ratio
            meetpoint=feet_to_nm((descent_ratio*nm_to_feet(d) + alt2 - alt1)/float(climb_ratio + descent_ratio))
            meet_d1=meetpoint
            meet_d2=d-meetpoint
            cont=False
            if na1<=na2 and meet_d1>next_d1:
                #Step alt1 to next vertical level
                alt1=na1
                d-=meet_d1
                cont=True
            if na2<=na1 and meet_d2>next_d2:
                #Step alt2 to next vertical level
                alt2=na2
                d-=meet_d1
                cont=True
            if cont: continue
            meetalt1=nm_to_feet(meet_d1*climb_ratio)
            meetalt2=nm_to_feet(meet_d2*descent_ratio)
            assert abs(meetalt1-meetalt2)<1e-3
            meetalt=0.5*(meetalt1+meetalt2)
            break
        return min(meetalt,mid_alt)
    else:
        assert 0 #Descent not supported yet.
        
def adv_cap_mid_alt(alt1,mid_alt,alt2,d,ac,rt):
    if alt1<=mid_alt and mid_alt<=alt2: return to_feet(mid_alt)
    #print "climb ratio",climb_ratio,"descent_ratio",descent_ratio
    if mid_alt>alt1:
        #bump
        while True:
            
            
            meetpoint=(descent_ratio*d + alt2 - alt1)/float(climb_ratio + descent_ratio)
            if meetpoint<0:
                assert meetpoint>-1e-3
                meetpoint=0                
            if meetpoint>d:
                assert meetpoint<1.00001*d
                meetpoint=d                      
            newmid=climb_ratio*meetpoint+alt1
            return to_feet(min(newmid,mid_alt))
    else:
        #hole
        meetpoint = (alt2 - alt1-climb_ratio*d) / (-descent_ratio-climb_ratio)
        if meetpoint<0:
            assert meetpoint>-1e-3
            meetpoint=0                
        if meetpoint>d:
            assert meetpoint<1.00001*d
            meetpoint=d                      
        newmid=alt1-descent_ratio*meetpoint
        return to_feet(max(newmid,mid_alt))

    
def cap_mid_alt(alt1,mid_alt,alt2,d,climb_ratio,descent_ratio):
    alt1=from_feet(alt1)
    alt2=from_feet(alt2)
    mid_alt=from_feet(mid_alt)
    d=from_nm(d)
    if alt1<=mid_alt and mid_alt<=alt2: return to_feet(mid_alt)
    #print "climb ratio",climb_ratio,"descent_ratio",descent_ratio
    if mid_alt>alt1:
        # y = k*x + m = climb_ratio*x + alt1
        # y = k*x + m = descent_ratio*(d-x) + alt2
        # climb_ratio*x + alt1 = descent_ratio*(d-x) + alt2
        # climb_ratio*x + alt1 = descent_ratio*d-descent_ratio*x + alt2
        # climb_ratio*x + descent_ratio*x = descent_ratio*d + alt2 - alt1
        # (climb_ratio + descent_ratio)*x = descent_ratio*d + alt2 - alt1
        # x = (descent_ratio*d + alt2 - alt1)/(climb_ratio + descent_ratio)
        meetpoint=(descent_ratio*d + alt2 - alt1)/float(climb_ratio + descent_ratio)
        if meetpoint<0:
            assert meetpoint>-1e-3
            meetpoint=0                
        if meetpoint>d:
            assert meetpoint<1.00001*d
            meetpoint=d                      
        newmid=climb_ratio*meetpoint+alt1
        return to_feet(min(newmid,mid_alt))
    else:
        # y = k*x + m = alt1-descent_ratio*x 
        # y = k*x + m = alt2-climb_ratio*(d-x) 
        # alt1-descent_ratio*x = alt2-climb_ratio*(d-x)
        # x*(-descent_ratio-climb_ratio) = alt2 - alt1-climb_ratio*d
        # x = (alt2 - alt1-climb_ratio*d) / (-descent_ratio-climb_ratio) 
        meetpoint = (alt2 - alt1-climb_ratio*d) / (-descent_ratio-climb_ratio)
        #print "meet",meetpoint
        if meetpoint<0:
            assert meetpoint>-1e-3
            meetpoint=0                
        if meetpoint>d:
            assert meetpoint<1.00001*d
            meetpoint=d                      
        newmid=alt1-descent_ratio*meetpoint
        return to_feet(max(newmid,mid_alt))
        
def cap_mid_alt_if_required(alt1,mid_alt,alt2,d,rt,ac):
    if not ac.advanced_performance_model:
        result=cap_mid_alt(alt1,mid_alt,alt2,d,rt.climb_ratio,rt.descent_ratio)
    else:
        result=adv_cap_mid_alt(alt1,mid_alt,alt2,d,rt,ac)
    d=abs(result-mid_alt)
    if d>1.0:
        return result,True
    return result,False
def altrange(alt1,alt2):
    def sub():
        yield alt1
        
        a1=alt1-alt1%1000
        if alt2>alt1:
            a1+=1000
            while a1<alt2:
                yield a1
                a1+=1000
        if alt1>alt2:       
            while a1>alt2:
                yield a1
                a1-=1000
        yield alt2
    
    last=None
    for x in sub():
        if last:
            yield last,x
        last=x
def calc_x_ratio(ac,rt,a1,speed,rate):
    assert ac.advanced_performance_model
    ialt=int(math.floor(a1/1000))
    if ialt<0: 
        ialt=0
    if ialt>=10: 
        return 0
    climb_gs,climb_wca=wind_computer(rt.winddir,rt.windvel,rt.tt,speed[ialt])    
    
    climb_speed_ms=climb_gs*1.852/3.6
    climb_rate_ms=(rate[ialt]/60.0)*0.3048
    climb_ratio=climb_rate_ms/climb_speed_ms
    if climb_ratio<=0: climb_ratio=0
    return climb_ratio
def calc_climb_ratio(ac,rt,a1):
    return calc_x_ratio(ac,rt,a1,ac.adv_climb_speed,ac.adv_climb_rate)
def calc_descent_ratio(ac,rt,a1):
    return calc_x_ratio(ac,rt,a1,ac.adv_descent_speed,ac.adv_descent_rate)


def max_x_feet(start_alt,dist_nm,rt,ac,fn,targ):
        dist=dist_nm
        for a1,a2 in altrange(start_alt,targ):
            cr=fn(ac,rt,0.5*sum([a1,a2]))
            if cr<1e-3:
                return a1
            forward=abs((0.3048/1852.0)*(a2-a1)/cr)
            if forward<dist:
                dist-=forward
                print "from",a1,"-",a2,forward,"nm","remain",dist,"used",dist_nm-dist,"cr",cr          
            else:
                frac=dist/forward
                print "from",a1,"-",a2,forward,"nm","remain",0,"used",dist_nm-0,"cr",cr
                return a1+frac*(a2-a1)
        return targ
        
def max_descent_feet(start_alt,dist_nm,rt,ac):
    if ac.advanced_performance_model:
        return max_x_feet(start_alt,dist_nm,rt,ac,calc_descent_ratio,-10000)
    else:
        descent_nm=dist_nm*rt.descent_ratio
        return start_alt-descent_nm*1852.0/0.3048

def max_revdescent_feet(end_alt,dist_nm,rt,ac):
    if ac.advanced_performance_model:
        return max_x_feet(end_alt,dist_nm,rt,ac,calc_descent_ratio,100000)
    else:
        climb_nm=dist_nm*rt.descent_ratio
        return end_alt+climb_nm*1852.0/0.3048

def getalti(alt):
    if type(alt) in [str,unicode]:
        a=mapper.parse_elev(alt)
    else:
        a=alt
    idx=int(math.floor(a))/1000
    if idx<0: idx=0
    if idx>=10: idx=9
    return idx

def max_climb_feet(start_alt,dist_nm,rt,ac):
    if ac.advanced_performance_model:
        return max_x_feet(start_alt,dist_nm,rt,ac,calc_climb_ratio,100000)
    else:
        climb_nm=dist_nm*rt.climb_ratio
        return start_alt+climb_nm*1852.0/0.3048
    
def max_revclimb_feet(end_alt,dist_nm,rt,ac):
    if ac.advanced_performance_model:
        return max_x_feet(end_alt,dist_nm,rt,ac,calc_climb_ratio,-10000)
    else:
        descent_nm=dist_nm*rt.climb_ratio
        return end_alt-descent_nm*1852.0/0.3048        
        

    
class DummyAircraft(object):pass
def get_route(user,trip):
    start=time()
    tripobj=meta.Session.query(Trip).filter(sa.and_(
            Trip.user==user,Trip.trip==trip)).one()

    waypoints=list(meta.Session.query(Waypoint).filter(sa.and_(
             Waypoint.user==user,Waypoint.trip==trip)).order_by(Waypoint.ordering).all())
    
    routes=[]
    for a,b in zip(waypoints[:-1],waypoints[1:]):
        rts=list(meta.Session.query(Route).filter(sa.and_(
            Route.user==user,Route.trip==trip,
            Route.waypoint1==a.id,Route.waypoint2==b.id)).all())
        assert len(rts)<2 and len(rts)>=0
        if len(rts)==0:
            rt=Route(user=user,trip=trip,waypoint1=a.id,waypoint2=b.id,winddir=None,windvel=None,tas=None,variation=None,altitude="1000")
            meta.Session.add(rt)
        else:
            rt=rts[0]
        rt.a=a
        rt.b=b        
        routes.append(rt)
    
    for prev,next in zip(routes[:-1],routes[1:]):
        next.prevrt=prev
        prev.nextrt=next
    
    #print "Looking for ac:",tripobj.aircraft
    acs=meta.Session.query(Aircraft).filter(sa.and_(
        Aircraft.user==user,Aircraft.aircraft==tripobj.aircraft)).all()
    if len(acs)==1:
        ac,=acs
    else:    
        ac=DummyAircraft()
        ac.advanced_performance_model=False
        ac.cruise_speed=75
        ac.cruise_burn=0
        ac.climb_speed=60
        ac.descent_speed=90
        ac.climb_rate=300
        ac.descent_rate=500
        ac.climb_burn=0
        ac.descent_burn=0
    
        
    for rt in routes:
        rt.tt,D=mapper.bearing_and_distance(rt.a.pos,rt.b.pos)
        rt.d=D


        if not ac.advanced_performance_model:
            rt.climb_gs,rt.climb_wca=wind_computer(rt.winddir,rt.windvel,rt.tt,ac.climb_speed)
            rt.descent_gs,rt.descent_wca=wind_computer(rt.winddir,rt.windvel,rt.tt,ac.descent_speed)
            rt.cruise_gs,rt.cruise_wca=wind_computer(rt.winddir,rt.windvel,rt.tt,rt.tas)
            
            climb_speed_ms=rt.climb_gs*1.852/3.6
            climb_rate_ms=(ac.climb_rate/60.0)*0.3048
            rt.climb_ratio=climb_rate_ms/climb_speed_ms
            descent_speed_ms=rt.descent_gs*1.852/3.6
            descent_rate_ms=(ac.descent_rate/60.0)*0.3048
            rt.descent_ratio=descent_rate_ms/descent_speed_ms
        else:
            rt.tas=ac.adv_cruise_speed[getalti(rt.altitude)]
            rt.cruise_gs,rt.cruise_wca=wind_computer(rt.winddir,rt.windvel,rt.tt,rt.tas)
            



        
    
            
    
    cone_min=None
    cone_max=None
    cone_start=None
    cone_dist=None
    for idx,rt in enumerate(reversed(routes)):
        if rt.b.stay:
            cone_start=cone_min=cone_max=float(get_pos_elev(mapper.from_str(rt.b.pos)))
            cone_dist=0.0
        elif cone_min==None:
            cone_start=cone_min=cone_max=float(get_pos_elev(mapper.from_str(rt.b.pos)))
            cone_dist=0.0
        else:
            cone_max=max_revdescent_feet(cone_start,cone_dist,rt,ac)
            cone_min=max_revclimb_feet(cone_start,cone_dist,rt,ac)        
        rt.cone_min=cone_min
        rt.cone_max=cone_max
        cone_dist+=rt.d


        
        
    def calc_midburn(tas):
        assert not ac.advanced_performance_model
        if tas>ac.cruise_speed:
            f=(tas/ac.cruise_speed)**3
            return ac.cruise_burn*f        
        f2=(tas/ac.cruise_speed)
        if f2<0.75:
            f2=0.75 #Don't assume we can fly slower than 75% of cruise, and still not waste fuel
        return f2*ac.cruise_burn
    res=[]
    accum_fuel=0
    accum_time=0
    #accum_clock=0
    accum_dt=datetime.utcnow()
    tot_dist=0
    prev_alt=None    
    numroutes=len(routes)
    for idx,rt in enumerate(routes):
        

        
        if rt.a.stay:
            stay=rt.a.stay
            if stay.fuel!=None:
                accum_fuel=stay.fuel
            else:
                if stay.fueladjust!=None:
                    accum_fuel+=stay.fueladjust
            if stay.date_of_flight!=None and stay.date_of_flight.strip()!="":
                try:
                    pd=parse_date(stay.date_of_flight.strip())
                    accum_dt=accum_dt.\
                        replace(year=pd.year).\
                        replace(month=pd.month).\
                        replace(day=pd.day)
                except Exception,cause:
                    print "Couldn't parse date",stay.date_of_flight
            if stay.departure_time!=None and stay.departure_time.strip()!="":
                try:
                    tempclock=parse_clock(stay.departure_time.strip())
                    accum_dt=accum_dt.replace(
                            hour=0,minute=0,second=0,microsecond=0)+\
                            timedelta(0,3600*tempclock)
                except Exception,cause:
                    print "Couldn't parse departure time %s"%(stay.departure_time)
                    pass
                
                
                
        
        rt.a.dt=copy(accum_dt)

        try:
            mid_alt=mapper.parse_elev(rt.altitude)
        except:
            mid_alt=1500
        if rt.a.stay:
            alt1=float(get_pos_elev(mapper.from_str(rt.a.pos)))
            if prev_alt==None: prev_alt=alt1
        else:                        
            if prev_alt==None or idx==0:
                prev_alt=float(get_pos_elev(mapper.from_str(rt.a.pos)))                            
            alt1=prev_alt
        if rt.b.stay:
            alt2=float(get_pos_elev(mapper.from_str(rt.b.pos)))
        else:            
            alt2=mid_alt
            if idx==numroutes-1:
                alt2=float(get_pos_elev(mapper.from_str(rt.b.pos)))
            if alt2>rt.cone_max: alt2=rt.cone_max
            if alt2<rt.cone_min: alt2=rt.cone_min
            if alt2>alt1:
                alt2=min(alt2,max_climb_feet(alt1,rt.d,rt,ac))
            elif alt2<alt1:
                alt2=max(alt2,max_descent_feet(alt1,rt.d,rt,ac))
        
        mid_alt,was_capped=cap_mid_alt_if_required(prev_alt,mid_alt,alt2,rt.d,rt,ac)
        
        

        if ac.advanced_performance_model:
            speed,alt_rate,mid_burn=calculate_speed_and_climb(ac,alt1,mid_alt)
        else:
    
            #print "idx: %d, prev_alt=%s"%(idx,prev_alt)
            def alt_change_dist(delta):
                """
                Given a delta in feet, calculate
                how many NM are required to achieve this change.
                """
                if ac.advanced_performance_model:
                    pass
                else:
                    if delta==0: return 0,rt.cruise_gs,ac.cruise_burn,'',0                
                    if delta>0:
                        t=(delta/float(max(1e-3,ac.climb_rate)))/60.0
                        return t*rt.climb_gs,rt.climb_gs,ac.climb_burn,'climb',ac.climb_rate
                    if delta<0:
                        t=(-delta/float(max(1e-3,ac.descent_rate)))/60.0
                        return t*rt.descent_gs,rt.descent_gs,ac.descent_burn,'descent',-ac.descent_rate
                    assert 0
    
    
    
            if not rt.tas:
                rt.tas=ac.cruise_speed
                
            
    
                    
            if not was_capped:
                rt.performance="ok"
            else:
                rt.performance="notok"
            begindelta=mid_alt-prev_alt
            enddelta=alt2-mid_alt
            
            
            
            begindist,beginspeed,beginburn,beginwhat,beginrate=alt_change_dist(begindelta)
            enddist,endspeed,endburn,endwhat,endrate=alt_change_dist(enddelta)
    
            #if begindist>rt.d:
            #    ratio=rt.d/float(begindist)
            #    begindist=rt.d
            #    rt.performance="notok"
            #    begindelta*=ratio
            #    mid_alt=prev_alt+begindelta                    
            print "begindist",begindist,"enddist",enddist,"d",rt.d
            if enddist+begindist>rt.d:
                if rt.d>1e-3:
                    overcommit=(enddist+begindist)/rt.d
                    if overcommit<1.0001:
                        begindist/=overcommit
                        enddist/=overcommit
                    else:
                        beginspeed=0 #make the route impossible, to flag error
                        rt.performance="notok"
                else:
                    beginrate=0
                    endrate=0
                    beginburn=0
                    endburn=0
                    begindist=0
                    enddist=0
                    rt.performance="notok"
                        
            del begindelta
            del enddelta
        rt.mid_alt=mid_alt
        del mid_alt        
        del alt1
        del alt2
        
        
            
        if beginspeed<1e-3:
            begintime=None
        else:
            begintime=begindist/beginspeed
        if endspeed<1e-3:
            endtime=None
        else:
            endtime=enddist/endspeed
        middist=rt.d-(begindist+enddist)
        #print "Mid-dist: %f, Mid-cruise: %f"%(middist,cruise_gs)
        if rt.cruise_gs<1e-3:
            midtime=None
        else:
            midtime=(rt.d-(begindist+enddist))/rt.cruise_gs
        #print "d: %f, Begintime: %s midtime: %s endtime: %s"%(rt.d,begintime,midtime,endtime)
    
        merca=mapper.latlon2merc(mapper.from_str(rt.a.pos),13)
        mercb=mapper.latlon2merc(mapper.from_str(rt.b.pos),13)
                    

        def interpol(where,tot,a,b):
            if abs(tot)<=1e-5:
                f=0.0
            else:
                f=where/float(tot)
            x=(1.0-f)*merca[0]+f*mercb[0]
            y=(1.0-f)*merca[1]+f*mercb[1]
            return (x,y)

        sub=[]
        if begintime==None or midtime==None or endtime==None or accum_dt==None:
            out=TechRoute()
            out.performance=rt.performance
            out.tt=rt.tt
            out.d=rt.d
            out.relstartd=0
            out.subposa=merca
            out.subposb=mercb
            out.startdt=accum_dt
            accum_time=None
            #accum_clock=None
            accum_dt=None
            out.clock_hours=None
            out.dt=None
            out.startalt=prev_alt
            prev_alt=None
            out.endalt=None
            out.altrate=0
            out.accum_time=None
            out.time=None
            out.what="cruise"
            out.legpart="mid"
            out.fuel_burn=None
            out.lastsub=0
            sub.append(out)
        else:
            if abs(begintime)>1e-5:
                out=TechRoute()
                out.performance=rt.performance
                out.tt=rt.tt
                out.d=begindist
                out.relstartd=0
                out.subposa=interpol(out.relstartd,rt.d,merca,mercb)
                out.subposb=interpol(out.relstartd+out.d,rt.d,merca,mercb)
                accum_time+=begintime
                out.startdt=accum_dt
                accum_dt+=timedelta(0,3600*begintime)
                #accum_clock+=begintime
                #out.clock_hours=accum_clock%24.0
                out.dt=accum_dt
                out.startalt=prev_alt
                prev_alt+=beginrate*begintime*60
                out.endalt=prev_alt
                out.altrate=beginrate
                out.accum_time=accum_time
                out.time=begintime
                out.fuel_burn=begintime*beginburn
                out.what=beginwhat
                out.legpart="begin"
                out.lastsub=0
                sub.append(out)
            if abs(midtime)>1e-5:
                out=TechRoute()
                out.performance=rt.performance
                out.tt=rt.tt
                out.d=middist
                out.relstartd=begindist
                out.subposa=interpol(out.relstartd,rt.d,merca,mercb)
                out.subposb=interpol(out.relstartd+out.d,rt.d,merca,mercb)
                out.startdt=accum_dt
                accum_time+=midtime
                #accum_clock+=midtime
                accum_dt+=timedelta(0,3600*midtime)
                #out.clock_hours=accum_clock%24
                out.dt=accum_dt
                out.startalt=prev_alt
                out.endalt=prev_alt
                out.altrate=0
                out.accum_time=accum_time
                out.time=midtime
                out.fuel_burn=midtime*calc_midburn(rt.tas)
                out.what="cruise"
                out.legpart="mid"
                out.lastsub=0
                sub.append(out)
            if abs(endtime)>1e-5:
                out=TechRoute()
                out.performance=rt.performance
                out.tt=rt.tt
                out.d=enddist
                out.relstartd=begindist+middist
                out.subposa=interpol(out.relstartd,rt.d,merca,mercb)
                out.subposb=interpol(out.relstartd+out.d,rt.d,merca,mercb)
                out.startdt=accum_dt
                accum_time+=endtime
                #accum_clock+=endtime
                accum_dt+=timedelta(0,3600*endtime)
                #out.clock_hours=accum_clock%24
                out.dt=accum_dt
                out.startalt=prev_alt
                prev_alt+=endrate*endtime*60
                out.endalt=prev_alt
                if abs(out.endalt)<1e-6:
                    out.endalt=0
                out.altrate=endrate
                out.accum_time=accum_time
                out.time=endtime
                out.what=endwhat
                out.legpart="end"
                out.fuel_burn=endtime*endburn
                out.lastsub=0
                sub.append(out)
        if len(sub):
            sub[-1].lastsub=1        
        else:
            out=TechRoute()
            out.performance=rt.performance
            out.tt=rt.tt
            out.d=0
            out.time=0
            out.relstartd=0
            out.subposa=merca
            out.subposb=mercb
            out.startalt=prev_alt
            out.endalt=prev_alt
            out.accum_time=accum_time
            #out.clock_hours=accum_clock%24
            out.startdt=accum_dt
            out.dt=accum_dt
            out.what="cruise"
            out.legpart="mid"
            out.fuel_burn=0
            out.lastsub=0
            sub.append(out)
        
        
        
        def val(x):
            if x==None: return 0.0
            return x
        for out in sub:    
            if rt.d<1e-5:
                out.startpos=mapper.from_str(rt.a.pos)
                out.endpos=mapper.from_str(rt.a.pos)
            else:
                drel1=out.relstartd/rt.d
                drel2=(out.relstartd+out.d)/rt.d
                mercs=[((1.0-rel)*merca[0]+rel*mercb[0],(1.0-rel)*merca[1]+rel*mercb[1]) for rel in [drel1,drel2]]
                out.startpos=mapper.merc2latlon(mercs[0],13)
                out.endpos=mapper.merc2latlon(mercs[1],13)
                #print "Name:",rt.a.waypoint,"Startpos:",out.startpos,"endpos:",out.endpos,"segment:",out.what
                
            if out.what=="climb":
                out.tas=ac.climb_speed
                out.gs=rt.climb_gs
                out.wca=rt.climb_wca
            elif out.what=="descent":
                out.tas=ac.descent_speed
                out.gs=rt.descent_gs
                out.wca=rt.descent_wca
            else:
                out.tas=rt.tas
                out.gs=rt.cruise_gs
                out.wca=rt.cruise_wca
            tot_dist+=out.d
            out.total_d=tot_dist
            out.a=rt.a
            out.b=rt.b
            out.id1=rt.waypoint1
            out.id2=rt.waypoint2
            out.winddir=rt.winddir
            out.windvel=rt.windvel
            res.append(out)
            if out.fuel_burn!=None:
                accum_fuel-=out.fuel_burn
            out.accum_fuel_burn=accum_fuel
            #print "Processing out. %s-%s %s Alt: %s"%(
            #    out.a.waypoint,out.b.waypoint,out.what,out.startalt)
        
        rt.gs,rt.wca=wind_computer(rt.winddir,rt.windvel,rt.tt,rt.tas)
        
        if begintime==None or midtime==None or endtime==None:
            rt.avg_gs=None
            rt.fuel_burn=None
            rt.time_hours=None
        else:
            if (begintime+midtime+endtime)>1e-3:
                rt.avg_gs=rt.d/(begintime+midtime+endtime)
            else:
                rt.avg_gs=rt.cruise_gs
            rt.fuel_burn=begintime*beginburn+midtime*ac.cruise_burn+endtime*endburn
            if rt.gs>1e-3:
                rt.time_hours=begintime+midtime+endtime;
            else:
                rt.time_hours=None                          
                        
        rt.subs=sub     
        rt.accum_time_hours=accum_time
        rt.accum_dist=tot_dist
        rt.accum_fuel_burn=accum_fuel
        
        rt.depart_dt=rt.a.dt
        if rt.time_hours!=None and rt.a.dt!=None:
            rt.arrive_dt=rt.a.dt+timedelta(hours=rt.time_hours)
        else:
            rt.arrive_dt=None
        #if accum_clock!=None:
        #    rt.clock_hours=accum_clock%24
        #else:
        #    rt.clock_hours=None
            
    if len(routes):
        last=routes[-1]
        last.b.dt=accum_dt
        
    for rt in routes: 
        rt.variation=0
        if rt.depart_dt==None or rt.arrive_dt==None: 
            continue
        startvar=calc_declination(mapper.from_str(rt.a.pos),rt.depart_dt,rt.subs[0].startalt)
        endvar=calc_declination(mapper.from_str(rt.b.pos),rt.arrive_dt,rt.subs[-1].endalt)
        if startvar!=None and endvar!=None:
            rt.variation=0.5*(startvar+endvar)
        rt.ch=(rt.tt+rt.wca-val(rt.variation)-val(rt.deviation))%360.0
        for sub in rt.subs:
            sub.ch=(sub.tt+sub.wca-val(rt.variation)-val(rt.deviation))%360.0

            
                
    #print "Elapsed ms",1000.0*(time()-start)
    return res,routes

def test_route_info():
    from fplan.config.environment import load_environment
    from fplan.model import meta
    from fplan.model import *

    from pylons import config
    u=User(u'anders',u'password')
    ac=Aircraft(u'anders',u'eurocub')
    ac.cruise_speed=75
    ac.climb_speed=50
    ac.descent_speed=100
    ac.climb_rate=500
    ac.descent_rate=1000
    ac.cruise_burn=15
    ac.climb_burn=20
    ac.descent_burn=10
    
    meta.Session.add(ac)
    trip=Trip(u"anders",u"mytrip",u'eurocub')
    wp1=Waypoint(u'anders',u'mytrip','59,18',0,u'bromma')
    wp2=Waypoint(u'anders',u'mytrip','60,18',1,u'arlanda')
    wp3=Waypoint(u'anders',u'mytrip','61,18',2,u'gävle')
    rt1=Route(u'anders',u'mytrip',0,1)
    rt1.altitude=10000
    rt2=Route(u'anders',u'mytrip',1,2)
    rt2.altitude=10000
    rt1.variation=4
    rt2.windvel=25
    rt2.winddir=0
    for s in [u,ac,trip,wp1,wp2,wp3,rt1,rt2]:
        meta.Session.add(s)
    meta.Session.flush()    
    tripobj=meta.Session.query(Trip).filter(sa.and_(
            Trip.user==u'anders',Trip.trip==u'mytrip')).one()
    class Temp(object): pass
    route,dummy=get_route(u'anders',u'mytrip')['routes']
    D=60.153204103671705
    assert abs(route[0].d-D)<1e-5
    #print route[0].__dict__
    assert route[0].ch==-4
    climbtime=10000/500.0/60.0
    climbdist=50.0*climbtime
    cruisedist=D-climbdist
    #print "Climbdist: %f, Cruisedist: %f"%(climbdist,cruisedist)
    cruisetime=cruisedist/75.0
    tottime=cruisetime+climbtime
    #print "Climbtime: %f, Cruisetime: %f, expected tot: %f, calculated tot time: %f"%(climbtime,cruisetime,climbtime+cruisetime,route[0].time_hours)
    assert abs(route[0].time_hours-tottime)<0.01
    #print route[1].wca
    
    
    
    
