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

def calc_total_tas(winddir,windvel,tt,gs):    
    gs_x=gs*math.cos(tt*(math.pi/180.0))
    gs_y=gs*math.sin(tt*(math.pi/180.0))
    wind_x=windvel*math.cos(winddir*(math.pi/180.0))
    wind_y=windvel*math.sin(winddir*(math.pi/180.0))
    tas_x=gs_x+wind_x
    tas_y=gs_y+wind_y
    return math.sqrt(tas_x**2.0+tas_y**2.0)
    

def from_feet(x): return x*0.3048
def to_feet(x): return x/0.3048
def from_nm(x): return x*1852.0
def from_fpm(x): return x*0.3048/60.0
def to_nm(x): return x/1852.0
def feet_to_nm(x): return x/(1852.0/0.3048)
def nm_to_feet(x): return x*(1852.0/0.3048)

def adv_cap_mid_alt(alt1,mid_alt,alt2,d,ac,rt):
    """
    Precondition: Climb from alt1 to alt2 is possible in distance d.
    Returns maximum altitude attainable in between alt1 and alt2
    """
    if alt1<=mid_alt and mid_alt<=alt2: return mid_alt
    if alt2<=mid_alt and mid_alt<=alt1: return mid_alt
    if alt1<=mid_alt:
        #climb
        meetalt=None
        iter=0
        while True:            
            iter+=1
            na1=int(alt1)-int(alt1)%1000+1000
            na2=int(alt2)-int(alt2)%1000+1000
            climb_ratio=calc_climb_ratio(ac,rt,alt1)
            descent_ratio=calc_descent_ratio(ac,rt,alt2)
            if climb_ratio<1e-6 or descent_ratio<1e-6:
                return min(mid_alt,max(alt1,alt2))
            next_d1=feet_to_nm((na1-alt1)/climb_ratio)
            next_d2=feet_to_nm((na2-alt2)/descent_ratio)
            meetpoint=feet_to_nm((descent_ratio*nm_to_feet(d) + alt2 - alt1)/float(climb_ratio + descent_ratio))
            meet_d1=meetpoint
            meet_d2=d-meetpoint
            assert meet_d1>=-1e-3
            assert meet_d2>=-1e-3
            meetalt1=alt1+nm_to_feet(meet_d1*climb_ratio)
            meetalt2=alt2+nm_to_feet(meet_d2*descent_ratio)
            assert abs(meetalt1-meetalt2)<1e-3
            meetalt=0.5*(meetalt1+meetalt2)
            
            cont=False
            if na1!=na2 or meetalt>min(na1,na2): 
                if na1<=na2 and meet_d1>next_d1:
                    #Step alt1 to next vertical level
                    alt1=na1
                    d-=next_d1
                    cont=True
                if na2<=na1 and meet_d2>next_d2:
                    #Step alt2 to next vertical level
                    alt2=na2
                    d-=next_d2
                    cont=True
                continue
            break
        return min(meetalt,mid_alt)
    else:
        #descent
        meetalt=None
        iter=0
        while True:            
            iter+=1
            na1=int(alt1)-int(alt1)%1000
            if na1==int(alt1): na1=int(alt1)-1000
            na2=int(alt2)-int(alt2)%1000
            if na2==int(alt2): na2=int(alt2)-1000
            descent_ratio=calc_descent_ratio(ac,rt,na1)
            climb_ratio=calc_climb_ratio(ac,rt,na2)
            if climb_ratio<1e-5 or descent_ratio<1e-5:
                return min(mid_alt,max(alt1,alt2))
            next_d1=feet_to_nm((alt1-na1)/descent_ratio)
            next_d2=feet_to_nm((alt2-na2)/climb_ratio)
            #meetpoint=  feet_to_nm((descent_ratio*nm_to_feet(d) + alt2 - alt1)/float(climb_ratio + descent_ratio))
            meetpoint = feet_to_nm((alt2 - alt1 - climb_ratio*nm_to_feet(d)) / float(-descent_ratio-climb_ratio))
            meet_d1=meetpoint
            meet_d2=d-meetpoint
            assert meet_d1>=-1e-3
            assert meet_d2>=-1e-3
            meetalt1=alt1-nm_to_feet(meet_d1*descent_ratio)
            meetalt2=alt2-nm_to_feet(meet_d2*climb_ratio)
            assert abs(meetalt1-meetalt2)<1e-3
            meetalt=0.5*(meetalt1+meetalt2)
            
            cont=False
            if na1!=na2 or meetalt<max(na1,na2): 
                if na1>=na2 and meet_d1>next_d1:
                    #Step alt1 to next vertical level
                    alt1=na1
                    d-=next_d1
                    cont=True
                if na2>=na1 and meet_d2>next_d2:
                    #Step alt2 to next vertical level
                    alt2=na2
                    d-=next_d2
                    cont=True
                continue
            break        
        return max(meetalt,mid_alt)
            

    
def cap_mid_alt(alt1,mid_alt,alt2,d,climb_ratio,descent_ratio):
    alt1=from_feet(alt1)
    alt2=from_feet(alt2)
    mid_alt=from_feet(mid_alt)
    d=from_nm(d)
    if alt1<=mid_alt and mid_alt<=alt2: return to_feet(mid_alt)
    if climb_ratio<1e-3 or descent_ratio<1e-3:
        if mid_alt>alt1:
            return max(alt1,alt2)
        else:
            return min(alt1,alt2)
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
        if meetpoint<0:
            assert meetpoint>-1e-3
            meetpoint=0                
        if meetpoint>d:
            assert meetpoint<1.00001*d
            meetpoint=d                      
        newmid=alt1-descent_ratio*meetpoint
        return to_feet(max(newmid,mid_alt))
        
def cap_mid_alt_if_required(alt1,mid_alt,alt2,d,ac,rt):
    if not ac.advanced_model:
        result=cap_mid_alt(alt1,mid_alt,alt2,d,rt.climb_ratio,rt.descent_ratio)
    else:
        result=adv_cap_mid_alt(alt1,mid_alt,alt2,d,ac,rt)
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
def calc_x_ratio(ac,rt,a1,speed,rate,burn,extrainfo=False):
    assert ac.advanced_model
    ialt=int(math.floor(a1/1000))
    if ialt<0: 
        ialt=0
    if ialt>=10: 
        if not extrainfo:
            return None
        else:
            return None,None,None,None 
    currate=rate[ialt]
    curburn=burn[ialt]
    climb_gs,climb_wca=wind_computer(rt.winddir,rt.windvel,rt.tt,speed[ialt])    
    if climb_gs<1e-3:
        if not extrainfo:
            return None
        else:
            return None,None,None,None 
        
        
    climb_speed_ms=climb_gs*1.852/3.6
    climb_rate_ms=(currate/60.0)*0.3048
    climb_ratio=climb_rate_ms/climb_speed_ms
    if climb_ratio<=0: climb_ratio=0
    if not extrainfo:
        return climb_ratio
    else:
        curspeed=climb_gs
        return climb_ratio,curspeed,curburn,currate
        
def calc_climb_ratio(ac,rt,a1,extrainfo=False):
    return calc_x_ratio(ac,rt,a1,ac.adv_climb_speed,ac.adv_climb_rate,ac.adv_climb_burn,extrainfo)
def calc_descent_ratio(ac,rt,a1,extrainfo=False):
    if a1>10000-1:
        #even if above 10000, always descend as if at 9999
        a1=10000-1    
    return calc_x_ratio(ac,rt,a1,ac.adv_descent_speed,ac.adv_descent_rate,ac.adv_descent_burn,extrainfo)


def max_x_feet(start_alt,dist_nm,ac,rt,fn,targ):
    #fuel,dist,time_h
    dist=dist_nm
    accudist=0.0
    fuel=0.0
    time_h=0.0
    for a1,a2 in altrange(start_alt,targ):
        cr,speed,burn,rate=fn(ac,rt,0.5*sum([a1,a2]),extrainfo=True)
        print "max_x_feet",start_alt,targ,"cr:",cr,"speed:",speed
        if cr==None or cr<1e-3 or speed<1e-3:
            #Reached aircraft's ceiling before desired altitude
            return a1,None,None,None
        forward=abs((0.3048/1852.0)*(a2-a1)/cr)
        if forward<dist:
            dist-=forward
            accudist+=forward
            t=forward/speed
            time_h+=t
            fuel+=t*burn            
        else:
            frac=dist/forward
            t=dist/speed
            time_h+=t
            fuel+=t*burn            
            accudist=dist_nm
            return a1+frac*(a2-a1),dist_nm
    return targ,fuel,accudist,time_h
    
def max_descent_feet(start_alt,dist_nm,ac,rt):
    if ac.advanced_model:
        return max_x_feet(start_alt,dist_nm,ac,rt,calc_descent_ratio,-10000)[0]
    else:
        descent_nm=dist_nm*rt.descent_ratio
        return start_alt-descent_nm*1852.0/0.3048
def max_descent_nm(start_alt,end_alt,ac,rt):
    """returns fuel,dist,time_h"""    
    assert ac.advanced_model
    return max_x_feet(start_alt,60*360,ac,rt,calc_descent_ratio,end_alt)[1:]
def max_climb_nm(start_alt,end_alt,ac,rt):
    """returns fuel,dist,time_h"""    
    assert ac.advanced_model
    return max_x_feet(start_alt,60*360,ac,rt,calc_climb_ratio,end_alt)[1:]

def max_revdescent_feet(end_alt,dist_nm,ac,rt):
    if ac.advanced_model:
        return max_x_feet(end_alt,dist_nm,ac,rt,calc_descent_ratio,100000)[0]
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

def alt_change_dist(ac,rt,startalt,delta):
    """
    Given a delta in feet, calculate
    how many NM are required to achieve this change.
    """
    print locals()
    if ac.advanced_model:
        if delta==0: 
            tas=ac.adv_cruise_speed[getalti(startalt)]
            burn=ac.adv_cruise_burn[getalti(startalt)]
            cruise_gs,cruise_wca=wind_computer(rt.winddir,rt.windvel,rt.tt,tas)
            return 0,cruise_gs,burn,'',0                
        if delta<0:
            fuel,dist,time_h=max_descent_nm(startalt,startalt+delta,ac,rt)
            what="descent"
        else:
            fuel,dist,time_h=max_climb_nm(startalt,startalt+delta,ac,rt)
            what="climb"
        if time_h==None:
            return None,None,None,"cruise",None
        print "Time_h",time_h
        if time_h<1e-5:
            #very unusual special case
            if dist<1e-3:                
                if delta<0:
                    rate=-ac.adv_descent_rate[getalti(startalt)]
                else:
                    rate=ac.adv_climb_rate[getalti(startalt)]
                gs=ac.adv_cruise_speed[getalti(startalt)]
                burn=ac.adv_cruise_burn[getalti(startalt)]
            else:
                rate=0
                gs=0
                burn=0
        else:
            #normal case
            burn=fuel/time_h
            gs=dist/time_h
            rate=delta/time_h/60.0 #fpm
            print dist,"NM in ",time_h,"is",gs,"knots","what:",what,"rate:",rate
        return dist,gs,burn,what,rate
    else:
        if delta==0: return 0,rt.cruise_gs,ac.cruise_burn,'',0                
        if delta>0:
            t=(delta/float(max(1e-3,ac.climb_rate)))/60.0
            return t*rt.climb_gs,rt.climb_gs,ac.climb_burn,'climb',ac.climb_rate
        if delta<0:
            t=(-delta/float(max(1e-3,ac.descent_rate)))/60.0
            return t*rt.descent_gs,rt.descent_gs,ac.descent_burn,'descent',-ac.descent_rate
        assert 0



def max_climb_feet(start_alt,dist_nm,ac,rt):
    if ac.advanced_model:
        return max_x_feet(start_alt,dist_nm,ac,rt,calc_climb_ratio,100000)[0]
    else:
        climb_nm=dist_nm*rt.climb_ratio
        return start_alt+climb_nm*1852.0/0.3048
    
def max_revclimb_feet(end_alt,dist_nm,ac,rt):
    if ac.advanced_model:
        return max_x_feet(end_alt,dist_nm,ac,rt,calc_climb_ratio,-10000)[0]
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
    
    acs=meta.Session.query(Aircraft).filter(sa.and_(
        Aircraft.user==user,Aircraft.aircraft==tripobj.aircraft)).all()
    dummyac=False
    if len(acs)==1:
        ac,=acs
    else:    
        ac=DummyAircraft()
        ac.advanced_model=False
        ac.cruise_speed=75
        ac.cruise_burn=0
        ac.climb_speed=60
        ac.descent_speed=100
        ac.climb_rate=300
        ac.descent_rate=500
        ac.climb_burn=0
        ac.descent_burn=0
        dummyac=True
    
        
    for rt in routes:
        rt.tt,D=mapper.bearing_and_distance(rt.a.pos,rt.b.pos)
        rt.d=D
        if dummyac:
            tas=rt.tas
            ac.cruise_speed=tas
            ac.climb_speed=tas
            ac.descent_speed=tas


        if not ac.advanced_model:
            rt.climb_gs,rt.climb_wca=wind_computer(rt.winddir,rt.windvel,rt.tt,ac.climb_speed)
            rt.descent_gs,rt.descent_wca=wind_computer(rt.winddir,rt.windvel,rt.tt,ac.descent_speed)
            rt.cruise_gs,rt.cruise_wca=wind_computer(rt.winddir,rt.windvel,rt.tt,rt.tas)
            
            climb_speed_ms=rt.climb_gs*1.852/3.6
            climb_rate_ms=(ac.climb_rate/60.0)*0.3048
            if climb_speed_ms>1e-3:
                rt.climb_ratio=climb_rate_ms/climb_speed_ms
            else:
                rt.climb_ratio=0
            descent_speed_ms=rt.descent_gs*1.852/3.6
            descent_rate_ms=(ac.descent_rate/60.0)*0.3048
            if descent_speed_ms>1e-3:
                rt.descent_ratio=descent_rate_ms/descent_speed_ms
            else:
                rt.descent_ratio=0
            



        
    
            
    
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
            #this can be optimized, since the next calculation basically
            #needs to recalculate 50% of the route on average for each call.
            #(It calculates from the last stay upt o the current waypoint).
            cone_max=max_revdescent_feet(cone_start,cone_dist,ac,rt)
            cone_min=max_revclimb_feet(cone_start,cone_dist,ac,rt)
        rt.cone_min=cone_min
        rt.cone_max=cone_max
        cone_dist+=rt.d


        
        
    def calc_midburn(tas,alt):
        if ac.advanced_model:            
            return ac.adv_cruise_burn[getalti(alt)]
        else:
            if tas>ac.cruise_speed:
                f=(tas/ac.cruise_speed)**3
                return ac.cruise_burn*f        
            f2=(tas/ac.cruise_speed)
            if f2<0.75:
                f2=0.75 #Don't assume we can fly slower than 75% of cruise, and still not waste fuel
            return f2*ac.cruise_burn
    res=[]
    accum_fuel=0
    accum_fuel_used=0
    accum_time=0
    #accum_clock=0
    accum_dt=datetime.utcnow()
    tot_dist=0
    prev_alt=None    
    numroutes=len(routes)
    for idx,rt in enumerate(routes):
        print "rt.tas",rt.tas
        if dummyac:
            tas=rt.tas
            ac.cruise_speed=tas
            ac.climb_speed=tas
            ac.descent_speed=tas
        

        if rt.a.stay:
            stay=rt.a.stay
            if stay.fuel!=None:
                accum_fuel=stay.fuel
            else:
                if stay.fueladjust!=None and accum_fuel!=None:
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
                m=max_climb_feet(alt1,rt.d,ac,rt)
                alt2=min(alt2,m)
            elif alt2<alt1:
                m=max_descent_feet(alt1,rt.d,ac,rt)
                alt2=max(alt2,m)
        
        mid_alt,was_capped=cap_mid_alt_if_required(prev_alt,mid_alt,alt2,rt.d,ac,rt)
        
        print "capped mid_alt",mid_alt,was_capped

        if True:    
            
                    
            if not was_capped:
                rt.performance="ok"
            else:
                rt.performance="notok"
            begindelta=mid_alt-prev_alt
            enddelta=alt2-mid_alt
            
            
            begindist,beginspeed,beginburn,beginwhat,beginrate=alt_change_dist(ac,rt,alt1,begindelta)
            enddist,endspeed,endburn,endwhat,endrate=alt_change_dist(ac,rt,mid_alt,enddelta)
            
            print "begindist",begindist
            print "enddist",enddist
            
            #if begindist>rt.d:
            #    ratio=rt.d/float(begindist)
            #    begindist=rt.d
            #    rt.performance="notok"
            #    begindelta*=ratio
            #    mid_alt=prev_alt+begindelta                    
            if enddist==None or begindist==None:
                beginrate=0
                endrate=0
                beginburn=0
                endburn=0
                begindist=0
                enddist=0
                rt.performance="notok"
            else:
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
        if ac.advanced_model:
            tas=ac.adv_cruise_speed[getalti(rt.mid_alt)]
            cruise_gs,cruise_wca=wind_computer(rt.winddir,rt.windvel,rt.tt,tas)
        else:
            cruise_gs=rt.cruise_gs
        if cruise_gs<1e-3:
            midtime=None
        else:
            midtime=(rt.d-(begindist+enddist))/cruise_gs
        
    
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
            out.gs=None
            out.relstartd=0
            out.outer_d=rt.d
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
                out.outer_d=rt.d
                out.subposa=interpol(out.relstartd,rt.d,merca,mercb)
                out.subposb=interpol(out.relstartd+out.d,rt.d,merca,mercb)
                out.gs=beginspeed
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
                out.gs=cruise_gs
                out.relstartd=begindist
                out.outer_d=rt.d
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
                out.fuel_burn=midtime*calc_midburn(rt.tas,rt.mid_alt)                
                out.what="cruise"
                out.legpart="mid"
                out.lastsub=0
                sub.append(out)
            if abs(endtime)>1e-5:
                out=TechRoute()
                out.performance=rt.performance
                out.tt=rt.tt
                out.d=enddist
                out.gs=endspeed
                out.relstartd=begindist+middist
                out.outer_d=rt.d
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
            out.gs=None
            out.time=0
            out.relstartd=0
            out.outer_d=0
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
            out.wca=0    
            if rt.d<1e-5:
                out.startpos=mapper.from_str(rt.a.pos)
                out.endpos=mapper.from_str(rt.a.pos)
            else:
                drel1=out.relstartd/rt.d
                drel2=(out.relstartd+out.d)/rt.d
                mercs=[((1.0-rel)*merca[0]+rel*mercb[0],(1.0-rel)*merca[1]+rel*mercb[1]) for rel in [drel1,drel2]]
                out.startpos=mapper.merc2latlon(mercs[0],13)
                out.endpos=mapper.merc2latlon(mercs[1],13)
                
            if out.time and out.time>1e-3:
                out.tas=calc_total_tas(rt.winddir,rt.windvel,rt.tt,out.gs)
                dummygs,out.wca=wind_computer(rt.winddir,rt.windvel,rt.tt,out.tas)
                assert abs(dummygs-out.gs)<1e-3
            else:
                out.tas=0
                out.wca=0
                                
            tot_dist+=out.d
            out.total_d=tot_dist
            out.a=rt.a
            out.b=rt.b
            out.id1=rt.waypoint1
            out.id2=rt.waypoint2
            out.winddir=rt.winddir
            out.windvel=rt.windvel

            if accum_fuel!=None and out.fuel_burn!=None:
                accum_fuel-=out.fuel_burn
            else:
                accum_fuel=None
                
            if accum_fuel_used!=None and out.fuel_burn!=None:
                accum_fuel_used+=out.fuel_burn
            else:
                accum_fuel_used=None
                
            out.accum_fuel_left=accum_fuel
            out.accum_fuel_used=accum_fuel_used
        
            res.append(out)
        
        
        if begintime==None or midtime==None or endtime==None:
            rt.gs=None
            rt.fuel_burn=None
            rt.time_hours=None
        else:
            if (begintime+midtime+endtime)>1e-4:
                rt.gs=rt.d/(begintime+midtime+endtime)
            else:
                #microshort leg (just a few seconds!)
                if ac.advanced_model:
                    rt.gs=ac.adv_cruise_speed[getalti(rt.subs[0].startalt)]
                else:
                    rt.gs=rt.cruise_gs

            rt.fuel_burn=0
            for out in sub:
                if out.fuel_burn==None: 
                    rt.fuel_burn=None
                    break
                rt.fuel_burn+=out.fuel_burn
                
            if rt.gs>1e-3:
                rt.time_hours=begintime+midtime+endtime;
            else:
                rt.time_hours=None                          
                        
        rt.subs=sub     
        rt.accum_time_hours=accum_time
        rt.accum_dist=tot_dist
        rt.accum_fuel_left=accum_fuel
        rt.accum_fuel_used=accum_fuel_used
        
        rt.depart_dt=rt.a.dt
        if rt.time_hours!=None and rt.a.dt!=None:
            rt.arrive_dt=rt.a.dt+timedelta(hours=rt.time_hours)
        else:
            rt.arrive_dt=None
        #if accum_clock!=None:

        if ac.advanced_model:
            if rt.gs==None:
                rt.tas=0
            else:
                rt.tas=calc_total_tas(rt.winddir,rt.windvel,rt.tt,rt.gs)
                print "TAS:",rt.tas,"GS:",rt.gs            
        else:
            if not rt.tas:
                rt.tas=ac.cruise_speed
        dummygs,rt.wca=wind_computer(rt.winddir,rt.windvel,rt.tt,rt.tas)

        #    rt.clock_hours=accum_clock%24
        #else:
        #    rt.clock_hours=None
            
    if len(routes):
        last=routes[-1]
        last.b.dt=accum_dt
        
    for rt in routes: 
        rt.variation=0
        if rt.depart_dt!=None and rt.arrive_dt!=None: 
            startvar=calc_declination(mapper.from_str(rt.a.pos),rt.depart_dt,rt.subs[0].startalt)
            endvar=calc_declination(mapper.from_str(rt.b.pos),rt.arrive_dt,rt.subs[-1].endalt)
            if startvar!=None and endvar!=None:
                rt.variation=0.5*(startvar+endvar)
        rt.ch=(rt.tt+rt.wca-val(rt.variation)-val(rt.deviation))%360.0
        #for sub in rt.subs:
        #    sub.ch=(sub.tt+sub.wca-val(rt.variation)-val(rt.deviation))%360.0

            
                
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
    assert route[0].ch==-4
    climbtime=10000/500.0/60.0
    climbdist=50.0*climbtime
    cruisedist=D-climbdist
    cruisetime=cruisedist/75.0
    tottime=cruisetime+climbtime
    assert abs(route[0].time_hours-tottime)<0.01
    
    
    
    
