import math

def calc_density(altitude):
    return 1.22521 * ((288.15+-0.0065*(altitude*0.3048))/(288.15))**((-1*9.80665*0.0289644/( 8.31432 *-0.0065))-1.0)
def calc_tas(cas,air_density):
    return cas*math.sqrt(1.22521/air_density)
def calc_cas(tas,air_density):
    return tas/math.sqrt(1.22521/air_density)


def run_model():
    
    #70% power cruise
    
    
    table={
           2000:dict(ktas=116,gph=8.4),
           4000:dict(ktas=118,gph=8.4),
           6000:dict(ktas=120,gph=8.4),
           8000:dict(ktas=122,gph=8.4),
           10000:dict(ktas=122,gph=8.0),           
           12000:dict(ktas=118,gph=7.2)           
           }
    
    
    
    
def run_model_old():
    
    frontACd=1.0*0.01        
    wingACL=1.2*8*.15
    
    std_air_density=1.22521
    air_density= 1.22521
    glide_ratio = 6.5*1852.0 / (4000.0*0.3048)
    print "Glide ratio",glide_ratio
    stall_speed=50*1.852/3.6
    best_glide_speed=65*1.852/3.6
    max_speed=125*1.852/3.6
    mass=2300*0.4536
    max_power=160*736#hp
    g=9.81
    
    front_area=10.0*0.3+1.25*1.7
    
    glide_angle=math.atan2(1,glide_ratio)
    print "Glide angle",glide_angle*180.0/math.pi
    best_glide_descent=math.sin(glide_angle)*best_glide_speed
    print "Glide speed",best_glide_speed,"glide descent",best_glide_descent
    glide_power=best_glide_descent*mass*g
    glide_force=glide_power/best_glide_speed
    Lift = g*mass
    print "Glide power:",glide_power/736.0,"hp"
    print "Glide force 1",glide_power/best_glide_speed
    print "Glide force 2",mass*g*math.sin(glide_angle)
    
    # F = A*density*V^2*Cd/2 => Cd = F/(A*density*V^2/2)
    Cd = (glide_force/2.0)/(front_area*air_density*best_glide_speed**2.0/2.0)
    #Cdinduced=Cdtot/2.0
    prop_eff=0.68
    print "Cd",Cd
    
    # Induced drag = Lift**2 / (induced_k * best_glide_speed**2)
    # induced_k = Lift**2/(best_glide_speed**2 * induced_drag) 
    # induced_k = Lift**2/(best_glide_speed**2 * (glide_force/2.0))
    induced_k = Lift**2/(best_glide_speed**2 * (glide_force/2.0))
     
    
    # F = max_power/V = A*density*V^2*Cd/2
    # F = max_power = A*density*V^3*Cd/2
    # V = (max_power/(A*density*Cd/2))**(1/3.0)
    altitude_air_density=0.96
    max_speed=best_glide_speed
    for i in xrange(10):
        aerodrag=front_area*altitude_air_density*Cd/2.0*max_speed**2
        induceddrag=Lift**2/(induced_k*max_speed**2)        
        print "Max speed",max_speed*3.6/1.852,"knots","aerodrag",aerodrag,"induced",induceddrag
        max_speed = 0.5*(max_speed+prop_eff*max_power/(aerodrag+induceddrag))
        print "   TAS",calc_tas(max_speed,altitude_air_density)*3.6/1.852,"knots"
    
    
    for startalt in xrange(0,13000,1000):
        rates=[]
        for speed in xrange(65,80):
            initial_climb_speed=speed*1.852/3.6
            air_density=calc_density(startalt)
            density_factor=air_density/std_air_density
            climb_drag_force=front_area*air_density*(Cd)*initial_climb_speed**2.0/2.0 + Lift**2/(induced_k*initial_climb_speed**2)
            climb_drag_power=climb_drag_force*initial_climb_speed
            power_factor=min(1,density_factor*1.25)
            extra_power=prop_eff*(density_factor**1.32)*max_power*power_factor-climb_drag_power
            print "speed",speed,"extra_power",extra_power
            extra_climb = extra_power/(g*mass)
            rates.append((extra_climb,speed))
        rate,speed=max(rates)
        print "Climb at %.0f climb rate"%startalt,rate/0.3048*60,"fpm","speed",speed
    
    
    

if __name__=='__main__':
    run_model()