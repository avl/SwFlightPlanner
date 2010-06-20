#encoding=utf8
from fplan.model import meta,User,Trip,Waypoint,Route,Aircraft
import fplan.lib.mapper as mapper
import math
import sqlalchemy as sa

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
def get_route(user,trip):
    print "Getting ",user,trip
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

    print "Looking for ac:",tripobj.aircraft
    ac=meta.Session.query(Aircraft).filter(sa.and_(
        Aircraft.user==user,Aircraft.aircraft==tripobj.aircraft)).one()

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
    prev_alt=0
    for rt in routes:

        climb_gs,climb_wca=wind_computer(rt.winddir,rt.windvel,rt.tt,ac.climb_speed)
        descent_gs,descent_wca=wind_computer(rt.winddir,rt.windvel,rt.tt,ac.descent_speed)

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
        begindelta=mid_alt-prev_alt

        if hasattr(rt,'nextrt'):
            enddelta=0
        else:
            enddelta=-mid_alt
            
        begindist,beginspeed,beginburn,beginwhat,beginrate=alt_change_dist(begindelta)
        enddist,endspeed,endburn,endwhat,endrate=alt_change_dist(enddelta)
        print "Begindist: delta=%s %s, dist: %f, enddist: delta: %s ft %s, dist:%f"%(begindelta,beginwhat,begindist,enddelta,endwhat,enddist)
        if begindist>rt.d and enddist==0:
            rt.climbperformance="notok"
            begindist=rt.d                 
        elif begindist+enddist>rt.d+1e-3:
            rt.climbperformance="notok"
            ratio=rt.d/(begindist+enddist)
            begindist*=ratio
            enddist*=ratio
        else:
            rt.climbperformance="ok"
        begintime=begindist/beginspeed
        endtime=enddist/endspeed
        middist=rt.d-(begindist+enddist)
        print "Mid-dist: %f, Mid-cruise: %f"%(middist,cruise_gs)
        if cruise_gs<1e-3:
            midtime=999
        else:
            midtime=(rt.d-(begindist+enddist))/cruise_gs
        print "d: %f, Begintime: %s midtime: %s endtime: %s"%(rt.d,begintime,midtime,endtime)
        def timefmt(h):
            totmin=int(60*h)
            h=int(totmin//60)
            min_=totmin-h*60
            return "%dh%02dm"%(h,min_)
            

        sub=[]
        if abs(begintime)>1e-5:
            out=TechRoute()
            out.tt=rt.tt
            out.d=begindist
            accum_time+=begintime
            out.startalt=prev_alt
            prev_alt+=beginrate*begintime*60
            out.endalt=prev_alt
            out.accum_time=timefmt(accum_time)
            out.time=timefmt(begintime)
            out.fuel_burn=begintime*beginburn
            out.what=beginwhat
            sub.append(out)
        if abs(midtime)>1e-5:
            out=TechRoute()
            out.tt=rt.tt
            out.d=middist
            accum_time+=midtime
            out.startalt=prev_alt
            out.endalt=prev_alt
            out.accum_time=timefmt(accum_time)
            out.time=timefmt(midtime)
            out.fuel_burn=midtime*calc_midburn(rt.tas)
            out.what="cruise"
            sub.append(out)
        if abs(endtime)>1e-5:
            out=TechRoute()
            out.tt=rt.tt
            out.d=enddist
            accum_time+=endtime
            out.startalt=prev_alt
            prev_alt+=endrate*endtime*60
            out.endalt=prev_alt
            out.accum_time=timefmt(accum_time)
            out.time=timefmt(endtime)
            out.what=endwhat
            out.fuel_burn=endtime*endburn
            sub.append(out)
        def val(x):
            if x==None: return 0.0
            return x
        for out in sub:    
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
            res.append(out)
            accum_fuel+=out.fuel_burn
            out.accum_fuel_burn=accum_fuel
            print "Processing out. %s-%s %s Alt: %s"%(
                out.a.waypoint,out.b.waypoint,out.what,out.startalt)
        print "Times:",begintime,midtime,endtime
        if (begintime+midtime+endtime)>1e-3:
            rt.avg_gs=rt.d/(begintime+midtime+endtime)
        else:
            rt.avg_gs=cruise_gs
        rt.fuel_burn=begintime*beginburn+midtime*ac.cruise_burn+endtime*endburn
                        
        rt.gs,rt.wca=wind_computer(rt.winddir,rt.windvel,rt.tt,rt.tas)
                    
        rt.ch=rt.tt+rt.wca-val(rt.variation)-val(rt.deviation)

        if rt.gs>1e-3:
            rt.time_hours=rt.d/rt.gs;
        else:
            rt.time_hours=None                          
    
    return res

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
    route=get_route(u'anders',u'mytrip')['routes']
    D=60.153204103671705
    assert abs(route[0].d-D)<1e-5
    print route[0].__dict__
    assert route[0].ch==-4
    climbtime=10000/500.0/60.0
    climbdist=50.0*climbtime
    cruisedist=D-climbdist
    print "Climbdist: %f, Cruisedist: %f"%(climbdist,cruisedist)
    cruisetime=cruisedist/75.0
    tottime=cruisetime+climbtime
    print "Climbtime: %f, Cruisetime: %f, expected tot: %f, calculated tot time: %f"%(climbtime,cruisetime,climbtime+cruisetime,route[0].time_hours)
    assert abs(route[0].time_hours-tottime)<0.01
    print route[1].wca
    
    
    
    
