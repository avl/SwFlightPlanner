import calc_route_info as calc


class AC(object):pass
class RT(object):pass

def acrt():
    ac=AC()
    ac.adv_climb_speed=[75,75,75,75,75,75,75,75,75,75]
    ac.adv_climb_rate=[700,700,600,500, 400,300,200, 100,0,0]
    ac.adv_descent_speed=[120,120,120, 120,120,120, 120,120, 120,120]
    ac.adv_descent_rate=[500,500,500, 500,500,500, 500,500,500,500]
    ac.advanced_performance_model=True
    
    rt=RT()
    rt.tt=0
    rt.winddir=0   
    rt.windvel=50
    
    return ac,rt
def test_adv_climb_ratio():
    ac,rt=acrt()
    ratio=calc.calc_climb_ratio(ac, rt, 3000)
    
    climb_rate_ms=500*0.3048/60.0
    speed_ms=25*1.852/3.6
    print "ratio",ratio,"climb",climb_rate_ms,"m/s, speed:",speed_ms,"m/s"
    assert abs(ratio-(climb_rate_ms/speed_ms))<1e-4

def test_max_climb_feet():
    ac,rt=acrt()
    
    m=calc.max_climb_feet(500,20,rt,ac)
    print "In 20nm, climb to",m,'ft'
    assert m==8000
    m=calc.max_climb_feet(500,5,rt,ac)
    print "In 5nm, climb to",m,'ft'
    assert abs(m-6071.42857143)<1e-3
    m=calc.max_revclimb_feet(m,5,rt,ac)
    print "In 5nm, revclimb to",m,'ft'
    assert abs(m-500)<1e-3
    

    m=calc.max_descent_feet(8000,20,rt,ac)
    print "In 20nm, descend to",m,'ft'
    assert m<0
    m=calc.max_descent_feet(8000,5,rt,ac)
    print "In 5nm, descend to",m,'ft'
    assert m>5857 and m<5858
    
    m=calc.max_revdescent_feet(m,5,rt,ac)
    print "In 5nm, revdescend to",m,'ft'
    assert abs(m-8000)<1e-3
    
    
    
    