#encoding=utf8
import calc_route_info as calc
import os

class AC(object):pass
class RT(object):pass

def acrt():
    ac=AC()
    ac.adv_climb_speed=[75,75,75,75,75,75,75,75,75,75]
    ac.adv_climb_rate=[700,700,600,500, 400,300,200, 100,0,0]
    ac.adv_climb_burn=[15,15,15,15, 15,15,15, 15,15,15]
    ac.adv_descent_speed=[120,120,120, 120,120,120, 120,120, 120,120]
    ac.adv_descent_rate=[500,500,500, 500,500,500, 500,500,500,500]
    ac.adv_descent_burn=[15,15,15,15, 15,15,15, 15,15,15]
    ac.advanced_model=True
    
    rt=RT()
    rt.tt=0
    rt.winddir=0   
    rt.windvel=50
    
    return ac,rt

def test_adv_mid_cap():
    ac,rt=acrt()
    
    alt1=5000
    mid_alt=0
    alt2=5000
    d=200
    assert 0==calc.adv_cap_mid_alt(alt1,mid_alt,alt2,d,ac,rt)

    alt1=5000
    mid_alt=0
    alt2=5000
    d=5
    assert abs(3487-calc.adv_cap_mid_alt(alt1,mid_alt,alt2,d,ac,rt))<1

    alt1=5000
    mid_alt=0
    alt2=5000
    d=5
    rt.tt=180
    #tailwind - less time to sink
    assert abs(4540-calc.adv_cap_mid_alt(alt1,mid_alt,alt2,d,ac,rt))<1
    rt.tt=0
    
    alt1=0
    mid_alt=10000
    alt2=0
    d=200
    assert 8000==calc.adv_cap_mid_alt(alt1,mid_alt,alt2,d,ac,rt)

    alt1=0
    mid_alt=10000
    alt2=0
    d=5
    assert abs(1707-calc.adv_cap_mid_alt(alt1,mid_alt,alt2,d,ac,rt))<1

    alt1=0
    mid_alt=10000
    alt2=0
    d=5
    rt.tt=90
    #sidewind, less time to climb
    assert abs(1007-calc.adv_cap_mid_alt(alt1,mid_alt,alt2,d,ac,rt))<1
    rt.tt=0
    
    alt1=0
    mid_alt=1700
    alt2=0
    d=5
    assert abs(1700-calc.adv_cap_mid_alt(alt1,mid_alt,alt2,d,ac,rt))<1
    
    alt1=0
    mid_alt=50000 
    alt2=100000
    d=5
    #impossible to reach, but adv_cap_mid_alt only works for holes or bumps,
    #and this is neither, which means expected result is still 50000'. 
    assert abs(50000-calc.adv_cap_mid_alt(alt1,mid_alt,alt2,d,ac,rt))<1
    
    

def test_adv_climb_ratio():
    ac,rt=acrt()
    ratio=calc.calc_climb_ratio(ac, rt, 3000)
    
    climb_rate_ms=500*0.3048/60.0
    speed_ms=25*1.852/3.6
    print "ratio",ratio,"climb",climb_rate_ms,"m/s, speed:",speed_ms,"m/s"
    assert abs(ratio-(climb_rate_ms/speed_ms))<1e-4

def test_max_climb_feet():
    ac,rt=acrt()
    
    m=calc.max_climb_feet(500,20,ac,rt)
    print "In 20nm, climb to",m,'ft'
    assert m==8000
    m=calc.max_climb_feet(500,5,ac,rt)
    print "In 5nm, climb to",m,'ft'
    assert abs(m-6071.42857143)<1e-3
    m=calc.max_revclimb_feet(m,5,ac,rt)
    print "In 5nm, revclimb to",m,'ft'
    assert abs(m-500)<1e-3
    

    m=calc.max_descent_feet(8000,20,ac,rt)
    print "In 20nm, descend to",m,'ft'
    assert m<0
    m=calc.max_descent_feet(8000,5,ac,rt)
    print "In 5nm, descend to",m,'ft'
    assert m>5857 and m<5858

    m=calc.max_revdescent_feet(m,5,ac,rt)
    print "In 5nm, revdescend to",m,'ft'
    assert abs(m-8000)<1e-3
    
    fuel,m,time=calc.max_descent_nm(8000,5857,ac,rt)
    assert abs(m-5)<1e-1
    
    fuel,m,time=calc.max_climb_nm(500,6071.4,ac,rt)
    assert abs(m-5)<1e-1
    
    
    
def test_calc_total_tas():
    assert abs(150-calc.calc_total_tas(winddir=0,windvel=50,gs=100,tt=0))<1e-1    

    assert abs(111.803-calc.calc_total_tas(winddir=90,windvel=50,gs=100,tt=0))<1e-1    

def test_route_optimize():
    
    from fplan.config.environment import load_environment
    from fplan.model import meta
    from fplan.model import Waypoint,Route,Trip,User,Aircraft
    import sqlalchemy as sa

    from pylons import config
     
    # meta.Session.query(User).filter(User.user==u'testuser')
    
    u=User(u'testuser',u'password')
    meta.Session.add(u)
    meta.Session.flush();
    ac=Aircraft(u'testuser',u'eurocub')
    ac.adv_cruise_speed=    (75,75,75,76,76, 75,74,73,72,71)
    ac.adv_climb_speed=     (60,60,60,60,61, 61,61,62,63,64)
    ac.adv_descent_speed=   (80,80,81,81,82, 82,83,84,85,86)
    ac.adv_climb_rate=      (750,700,650,600,550,  500,450,300,200,000)
    ac.adv_descent_rate=    (500,500,500,500,525,  525,550,550,575,600)
    ac.adv_cruise_burn=     (16,16,16,16,15.5, 15.25,15.0,14.75,14.5,14.0)
    ac.adv_climb_burn=      (20,20,20,20,19, 19,18,17,15,14.0)
    ac.adv_descent_burn=    (14,14,14,14,14, 14,14,14,14,13.5)
    ac.advanced_model=True
    
    meta.Session.add(ac)
    meta.Session.flush();
    trip=Trip(u"testuser",u"mytrip",u'eurocub')
    meta.Session.add(trip)
    meta.Session.flush();
    wp1=Waypoint(u'testuser',u'mytrip','56,14',0,100,u'bromma')
    wp2=Waypoint(u'testuser',u'mytrip','58,14',1,101,u'arlanda')
    wp3=Waypoint(u'testuser',u'mytrip','59,14',2,102,u'gävle')
    wp4=Waypoint(u'testuser',u'mytrip','60,14',3,103,u'norr')
    wp5=Waypoint(u'testuser',u'mytrip','60.01,14',4,104,u'norr2')
    meta.Session.add(wp1)
    meta.Session.add(wp2)
    meta.Session.add(wp3)
    meta.Session.add(wp4)
    meta.Session.add(wp5)
    meta.Session.flush();
    rt1=Route(u'testuser',u'mytrip',0,1)
    rt1.altitude="0"
    rt2=Route(u'testuser',u'mytrip',1,2)
    rt2.altitude="0"
    rt3=Route(u'testuser',u'mytrip',2,3)
    rt3.altitude="0"
    rt4=Route(u'testuser',u'mytrip',3,4)
    rt4.altitude="0"
    for s in [wp1,wp2,wp3,wp4,rt1,rt2,rt3,rt4]:
        meta.Session.add(s)
    meta.Session.flush()    
    tripobj=meta.Session.query(Trip).filter(sa.and_(
            Trip.user==u'testuser',Trip.trip==u'mytrip')).one()
    print "Got tripobj",tripobj
    class Temp(object): pass
    res,routes=calc.get_optimized(u'testuser',u'mytrip','fuel')
    print [r.altitude for r in routes]
    
    
def test_adv_route_info():
    
    from fplan.config.environment import load_environment
    from fplan.model import meta
    from fplan.model import Waypoint,Route,Trip,User,Aircraft
    import sqlalchemy as sa

    from pylons import config
     
    # meta.Session.query(User).filter(User.user==u'testuser')
    
    u=User(u'testuser',u'password')
    meta.Session.add(u)
    meta.Session.flush();
    ac=Aircraft(u'testuser',u'eurocub')
    ac.adv_cruise_speed=    (75,75,75,76,76, 75,74,73,72,71)
    ac.adv_climb_speed=     (60,60,60,60,61, 61,61,62,63,64)
    ac.adv_descent_speed=   (80,80,81,81,82, 82,83,84,85,86)
    ac.adv_climb_rate=      (750,700,650,600,550,  500,450,300,200,000)
    ac.adv_descent_rate=    (500,500,500,500,525,  525,550,550,575,600)
    ac.adv_cruise_burn=     (16,16,16,16,15.5, 15.25,15.0,14.75,14.5,14.0)
    ac.adv_climb_burn=      (20,20,20,20,19, 19,18,17,15,14.0)
    ac.adv_descent_burn=    (14,14,14,14,14, 14,14,14,14,13.5)
    ac.advanced_model=True
    
    meta.Session.add(ac)
    meta.Session.flush();
    trip=Trip(u"testuser",u"mytrip",u'eurocub')
    meta.Session.add(trip)
    meta.Session.flush();
    wp1=Waypoint(u'testuser',u'mytrip','59,18',0,100,u'bromma')
    wp2=Waypoint(u'testuser',u'mytrip','60,18',1,101,u'arlanda')
    wp3=Waypoint(u'testuser',u'mytrip','61,18',2,102,u'gävle')
    wp4=Waypoint(u'testuser',u'mytrip','61.01,18',3,103,u'gävleclose')
    meta.Session.add(wp1)
    meta.Session.add(wp2)
    meta.Session.add(wp3)
    meta.Session.add(wp4)
    meta.Session.flush();
    rt1=Route(u'testuser',u'mytrip',0,1)
    rt1.altitude="1000"
    rt2=Route(u'testuser',u'mytrip',1,2)
    rt2.altitude="10000"
    rt2.windvel=25
    rt2.winddir=0
    rt3=Route(u'testuser',u'mytrip',2,3)
    rt3.altitude="0"
    for s in [wp1,wp2,wp3,rt1,rt2,rt3]:
        meta.Session.add(s)
    meta.Session.flush()    
    tripobj=meta.Session.query(Trip).filter(sa.and_(
            Trip.user==u'testuser',Trip.trip==u'mytrip')).one()
    print "Got tripobj",tripobj
    class Temp(object): pass
    dummy,route=calc.get_route(u'testuser',u'mytrip')
    D=60.153204103671705
    assert abs(route[0].d-D)<1e-5
    #print route[0].__dict__
    ch=route[0].ch
    assert abs(ch-355)<2 #This changes as earths magnetic field does
    #print "Climbtime: %f, Cruisetime: %f, expected tot: %f, calculated tot time: %f"%(climbtime,cruisetime,climbtime+cruisetime,route[0].time_hours)
    t=route[0].time_hours
    assert abs(t-0.806)<0.1
    m=route[0].mid_alt
    print "m:",m
    assert m==1000
    m=route[1].mid_alt
    print "m:",m
    assert m==9000
    #print route[1].wca
    
    m=route[2].subs[0].startalt
    print "last startalt",m
    #assert m==9000
    print "Last time",route[2].accum_time_hours
    assert abs(route[2].accum_time_hours-2.1281958051)<1e-9
    
    
if __name__=='__main__':
    from fplan.config.environment import load_environment
    from paste.deploy import appconfig
    import profile
    conf = appconfig('config:%s'%(os.path.join(os.getcwd(),"development.ini"),))
    load_environment(conf.global_conf, conf.local_conf)
    test_route_optimize()
    #print profile.run("test_route_optimize()")
    
    
    