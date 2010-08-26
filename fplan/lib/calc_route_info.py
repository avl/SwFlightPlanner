#encoding=utf8
from fplan.model import meta,User,Trip,Waypoint,Route,Aircraft
import fplan.lib.mapper as mapper
import math
import sqlalchemy as sa
from fplan.lib.get_terrain_elev import get_terrain_elev
from fplan.extract.extracted_cache import get_airfields

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
def get_pos_elev(latlon):
    for airf in get_airfields():
        #print "Considering:",airf
        apos=mapper.from_str(airf['pos'])
        dx=apos[0]-latlon[0]
        dy=apos[1]-latlon[1]
        if abs(dx)+abs(dy)<0.25*1.0/60.0 and 'elev' in airf:
            return airf['elev']
    return get_terrain_elev(latlon)

class DummyAircraft(object):pass
def get_route(user,trip):
    #print "Getting ",user,trip
    tripobj=meta.Session.query(Trip).filter(sa.and_(
            Trip.user==user,Trip.trip==trip)).one()
     
    waypoints=list(meta.Session.query(Waypoint).filter(sa.and_(
             Waypoint.user==user,Waypoint.trip==trip)).order_by(Waypoint.ordinal).all())
    
    routes=[]
    for a,b in zip(waypoints[:-1],waypoints[1:]):
        rts=list(meta.Session.query(Route).filter(sa.and_(
            Route.user==user,Route.trip==trip,
            Route.waypoint1==a.ordinal,Route.waypoint2==b.ordinal)).all())
        assert len(rts)<2 and len(rts)>=0
        if len(rts)==0:
            rt=Route(user=user,trip=trip,waypoint1=a.ordinal,waypoint2=b.ordinal,winddir=None,windvel=None,tas=None,variation=None,altitude="1000")
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
        rt.d=D/1.852

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
    tot_dist=0
    prev_alt=None    
    numroutes=len(routes)
    for idx,rt in enumerate(routes):
        
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

        mid_alt=mapper.parse_elev(rt.altitude)
        if rt.a.altitude.strip()!='':
            alt1=float(mapper.parse_elev(rt.a.altitude))
            if prev_alt==None: prev_alt=alt1
        else:                        
            if prev_alt==None or idx==0:
                prev_alt=get_pos_elev(mapper.from_str(rt.a.pos))                
                
            alt1=prev_alt
        if rt.b.altitude.strip()!='':
            alt2=float(mapper.parse_elev(rt.b.altitude))
        else:            
            alt2=mid_alt
            if idx==numroutes-1:
                alt2=get_pos_elev(mapper.from_str(rt.b.pos))
        
        
        rt.performance="ok"
        begindelta=mid_alt-prev_alt
        begindist,beginspeed,beginburn,beginwhat,beginrate=alt_change_dist(begindelta)
        if begindist>rt.d:
            #print "Begin delta ",begindelta," not fulfilled"
            ratio=rt.d/float(begindist)
            begindist=rt.d
            rt.performance="notok"
            begindelta*=ratio
            mid_alt=prev_alt+begindelta                    

        #print "mid_alt",mid_alt
        enddelta=alt2-mid_alt
                
        enddist,endspeed,endburn,endwhat,endrate=alt_change_dist(enddelta)
        #print "begindist: %f, enddist: %f, rt.d: %f"%(begindist,enddist,rt.d)
        if enddist+begindist>rt.d:
            #print "End delta ",enddelta," not fulfilled"
            enddist=rt.d-begindist            
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
        def timefmt(h):
            totmin=int(60*h)
            h=int(totmin//60)
            min_=totmin-h*60
            return "%dh%02dm"%(h,min_)
    
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
            out.startalt=prev_alt
            prev_alt+=beginrate*begintime*60
            out.endalt=prev_alt
            out.accum_time=timefmt(accum_time)
            out.time=timefmt(begintime)
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
            accum_time+=midtime
            out.startalt=prev_alt
            out.endalt=prev_alt
            out.accum_time=timefmt(accum_time)
            out.time=timefmt(midtime)
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
            accum_time+=endtime
            out.startalt=prev_alt
            prev_alt+=endrate*endtime*60
            out.endalt=prev_alt
            if abs(out.endalt)<1e-6:
                out.endalt=0
            out.accum_time=timefmt(accum_time)
            out.time=timefmt(endtime)
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
            out.accum_time=timefmt(accum_time)
            out.time=timefmt(0)
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
            out.ch=out.tt+out.wca-val(rt.variation)-val(rt.deviation)
            out.a=rt.a
            out.b=rt.b
            out.ordinal1=rt.waypoint1
            out.ordinal2=rt.waypoint2
            out.winddir=rt.winddir
            out.windvel=rt.windvel
            res.append(out)
            accum_fuel+=out.fuel_burn
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
                    
        rt.ch=rt.tt+rt.wca-val(rt.variation)-val(rt.deviation)
        rt.accum_time=timefmt(accum_time)
        rt.accum_time_hours=accum_time
        rt.accum_dist=tot_dist
        rt.accum_fuel_burn=accum_fuel
        if rt.gs>1e-3:
            rt.time_hours=rt.d/rt.gs;
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
    
    
    
    
