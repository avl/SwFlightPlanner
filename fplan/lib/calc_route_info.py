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
        rt.tt,D=mapper.bearing_and_distance(rt.a.pos,rt.b.pos)
        rt.d=D/1.852

    print "Looking for ac:",tripobj.aircraft
    ac=meta.Session.query(Aircraft).filter(sa.and_(
        Aircraft.user==user,Aircraft.aircraft==tripobj.aircraft)).one()

    climb_gs,climb_wca=wind_computer(rt.winddir,rt.windvel,rt.tt,ac.climb_speed)
    descent_gs,descent_wca=wind_computer(rt.winddir,rt.windvel,rt.tt,ac.descent_speed)

    def alt_change_dist(delta):
        if delta==0: return 0,cruise_gs,ac.cruise_burn,''
        if delta>0:
            t=(delta/ac.climb_rate)/60.0
            return t*climb_gs,climb_gs,ac.climb_burn,'climb'
        if delta<0:
            t=(-delta/ac.descent_rate)/60.0
            return t*descent_gs,descent_gs,ac.descent_burn,'descent'
    
    for rt in routes:
        if not rt.tas:
            rt.tas=ac.cruise_speed
        cruise_gs,cruise_wca=wind_computer(rt.winddir,rt.windvel,rt.tt,rt.tas)


        if hasattr(rt,'prevrt'):
            prev_alt=mapper.parse_elev(rt.prevrt.altitude)
        else:
            prev_alt=0
        if hasattr(rt,'nextrt'):
            next_alt=mapper.parse_elev(rt.nextrt.altitude)
            mid_alt=mapper.parse_elev(rt.altitude)
        else:
            next_alt=0
            mid_alt=mapper.parse_elev(rt.altitude)
        begindelta=mid_alt-prev_alt
        enddelta=next_alt-mid_alt
        begindist,beginspeed,beginburn,beginwhat=alt_change_dist(begindelta)
        enddist,endspeed,endburn,endwhat=alt_change_dist(enddelta)
        print "Begindist: delta=%s %s, dist: %f, enddist: delta: %s ft %s, dist:%f"%(begindelta,beginwhat,begindist,enddelta,endwhat,enddist)
        if begindist>rt.d and enddist==0:
            rt.climbperformance="notok"
            begindist=rt.d                 
        elif begindist+enddist>rt.d:
            rt.climbperformance="notok"
            ratio=rt.d/(begindist+enddist)
            begindist*=ratio
            enddist*=ratio
        else:
            rt.climbperformance="ok"
        begintime=begindist/beginspeed
        endtime=enddist/endspeed
        print "Mid-dist: %f, Mid-cruise: %f"%(rt.d-(begindist+enddist),cruise_gs)
        midtime=(rt.d-(begindist+enddist))/cruise_gs
        print "Begintime: %s midtime: %s endtime: %s"%(begintime,midtime,endtime)
        rt.avg_tas=rt.d/(begintime+midtime+endtime)
        rt.fuel_burn=begintime*beginburn+midtime*ac.cruise_burn+endtime*endburn
                        
        rt.gs,rt.wca=wind_computer(rt.winddir,rt.windvel,rt.tt,rt.tas)
                    
        def val(x):
            if x==None: return 0.0
            return x
        rt.ch=rt.tt+rt.wca-val(rt.variation)-val(rt.deviation)

        if rt.gs>0.0:
            rt.time_hours=rt.d/rt.gs;
        else:
            rt.time_hours=None                          
    
    return dict(waypoints=waypoints,
                routes=routes)

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
    
    
    
    
