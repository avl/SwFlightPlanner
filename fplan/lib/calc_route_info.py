#encoding=utf8
from fplan.model import meta,User,Trip,Waypoint,Route,Aircraft
import fplan.lib.mapper as mapper
import math
import sqlalchemy as sa
from fplan.lib.get_terrain_elev import get_terrain_elev
from fplan.extract.extracted_cache import get_airfields
from fplan.lib.airspace import get_pos_elev
from fplan.lib.helpers import parse_clock
from datetime import datetime,timedelta

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
    
    
class DummyAircraft(object):pass
def get_route(user,trip):
    #print "Getting ",user,trip
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
    for rt in routes:
        #print "D-calc: %s -> %s"%(rt.a.waypoint,rt.b.waypoint)
        rt.tt,D=mapper.bearing_and_distance(rt.a.pos,rt.b.pos)
        #print "Got D:",D
        rt.d=D

    #print "Looking for ac:",tripobj.aircraft
    acs=meta.Session.query(Aircraft).filter(sa.and_(
        Aircraft.user==user,Aircraft.aircraft==tripobj.aircraft)).all()
    if len(acs)==1:
        ac,=acs
    else:    
        ac=DummyAircraft()
        ac.cruise_speed=75
        ac.cruise_burn=0
        ac.climb_speed=60
        ac.descent_speed=90
        ac.climb_rate=300
        ac.descent_rate=500
        ac.climb_burn=0
        ac.descent_burn=0
        
    def calc_midburn(tas):
        if tas>ac.cruise_speed:
            f=(tas/ac.cruise_speed)**3
            return ac.cruise_burn*f
        f2=(tas/ac.cruise_speed)
        return ac.cruise_burn*f2
    res=[]
    accum_fuel=0
    accum_time=0
    accum_clock=0
    accum_dt=datetime.utcnow()
    tot_dist=0
    prev_alt=None    
    numroutes=len(routes)
    for idx,rt in enumerate(routes):
        if rt.a.stay:
            stay=rt.a.stay
            #print "Stay A:",stay.departure_time
            if stay.fuel!=None:
                try:
                    accum_fuel=stay.fuel
                except:
                    pass
            if stay.date_of_flight!=None:
                try:
                    pd=parse_date(stay.date_of_flight)
                    accum_dt=accum_dt.\
                        replace(year=pd.year).\
                        replace(month=pd.month).\
                        replace(day=pd.day)
                except Exception,cause:
                    print "Couldn't parse date",stay.date_of_flight
                    raise
                    pass                        
            if stay.departure_time!=None and stay.departure_time!="":
                try:
                    accum_clock=parse_clock(stay.departure_time)
                    accum_dt=accum_dt.replace(
                            hour=0,minute=0,second=0,microsecond=0)+\
                            timedelta(0,3600*accum_clock)
                    #print "accum dt:",accum_dt
                except Exception,cause:
                    print "Couldn't parse departure time %s"%(stay.departure_time)
                    pass
                
        rt.a.dt=accum_dt
        climb_gs,climb_wca=wind_computer(rt.winddir,rt.windvel,rt.tt,ac.climb_speed)
        descent_gs,descent_wca=wind_computer(rt.winddir,rt.windvel,rt.tt,ac.descent_speed)

        #print "idx: %d, prev_alt=%s"%(idx,prev_alt)
        def alt_change_dist(delta):
            if delta==0: return 0,cruise_gs,ac.cruise_burn,'',0
            if delta>0:
                t=(delta/float(ac.climb_rate))/60.0
                return t*climb_gs,climb_gs,ac.climb_burn,'climb',ac.climb_rate
            if delta<0:
                t=(-delta/float(ac.descent_rate))/60.0
                return t*descent_gs,descent_gs,ac.descent_burn,'descent',-ac.descent_rate
            assert 0


        if not rt.tas:
            rt.tas=ac.cruise_speed
        cruise_gs,cruise_wca=wind_computer(rt.winddir,rt.windvel,rt.tt,rt.tas)

        try:
            mid_alt=mapper.parse_elev(rt.altitude)
        except:
            mid_alt=1500
        if rt.a.stay:
            alt1=float(get_pos_elev(mapper.from_str(rt.a.pos)))
            if prev_alt==None: prev_alt=alt1
        else:                        
            if prev_alt==None or idx==0:
                prev_alt=get_pos_elev(mapper.from_str(rt.a.pos))                
                
            alt1=prev_alt
        if rt.b.stay:
            alt2=float(get_pos_elev(mapper.from_str(rt.b.pos)))
        else:            
            alt2=mid_alt
            if idx==numroutes-1:
                alt2=get_pos_elev(mapper.from_str(rt.b.pos))
        
        
        rt.performance="ok"
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
        if enddist+begindist>rt.d:
            factor=float(enddist+begindist)/float(rt.d)
            beginrate*=factor
            endrate*=factor
            beginburn*=factor
            endburn*=factor
            #beginspeed/=factor
            #endspeed/=factor
            begindist/=factor
            enddist/=factor
            rt.performance="notok"
                    
        del begindelta
        del enddelta
        del mid_alt        
        del alt1
        del alt2
            
            
        if beginspeed<1e-3:
            begintime=9999.0
        else:
            begintime=begindist/beginspeed
        if endspeed<1e-3:
            endtime=9999.0
        else:
            endtime=enddist/endspeed
        middist=rt.d-(begindist+enddist)
        #print "Mid-dist: %f, Mid-cruise: %f"%(middist,cruise_gs)
        if cruise_gs<1e-3:
            midtime=9999.0
        else:
            midtime=(rt.d-(begindist+enddist))/cruise_gs
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
            accum_clock+=begintime
            out.clock_hours=accum_clock%24.0
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
            accum_clock+=midtime
            accum_dt+=timedelta(0,3600*midtime)
            out.clock_hours=accum_clock%24
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
            accum_clock+=endtime
            accum_dt+=timedelta(0,3600*endtime)
            out.clock_hours=accum_clock%24
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
            out.relstartd=0
            out.subposa=merca
            out.subposb=mercb
            out.startalt=prev_alt
            out.endalt=prev_alt
            if prev_alt!=rt.altitude:
                out.performance="notok"
            out.accum_time=accum_time
            out.clock_hours=accum_clock%24
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
                out.gs=climb_gs
                out.wca=climb_wca
            elif out.what=="descent":
                out.tas=ac.descent_speed
                out.gs=descent_gs
                out.wca=descent_wca
            else:
                out.tas=rt.tas
                out.gs=cruise_gs
                out.wca=cruise_wca
            tot_dist+=out.d
            out.total_d=tot_dist
            out.ch=(out.tt+out.wca-val(rt.variation)-val(rt.deviation))%360.0
            out.a=rt.a
            out.b=rt.b
            out.id1=rt.waypoint1
            out.id2=rt.waypoint2
            out.winddir=rt.winddir
            out.windvel=rt.windvel
            res.append(out)
            accum_fuel-=out.fuel_burn
            out.accum_fuel_burn=accum_fuel
            #print "Processing out. %s-%s %s Alt: %s"%(
            #    out.a.waypoint,out.b.waypoint,out.what,out.startalt)
        #print "Times:",begintime,midtime,endtime
        if (begintime+midtime+endtime)>1e-3:
            rt.avg_gs=rt.d/(begintime+midtime+endtime)
        else:
            rt.avg_gs=cruise_gs
        rt.fuel_burn=begintime*beginburn+midtime*ac.cruise_burn+endtime*endburn
                        
        rt.gs,rt.wca=wind_computer(rt.winddir,rt.windvel,rt.tt,rt.tas)
                    
        rt.ch=(rt.tt+rt.wca-val(rt.variation)-val(rt.deviation))%360.0
        rt.accum_time_hours=accum_time
        rt.accum_dist=tot_dist
        rt.accum_fuel_burn=accum_fuel
        rt.clock_hours=accum_clock%24
        rt.b.dt=accum_dt
        if rt.gs>1e-3:
            rt.time_hours=begintime+midtime+endtime;
        else:
            rt.time_hours=None                          
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
    
    
    
    
