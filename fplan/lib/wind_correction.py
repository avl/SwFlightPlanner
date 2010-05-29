import math



"""

                             .
                            /
           TAS             / 
                          / WIND VEL
                         V
------------------------>
         TT GS
"""          
f=1.0/(180.0/math.pi)

tt=90
wind=0
windvel=25
tas=75


winddir=(wind+180) - tt;
print "winddir",winddir
wind_x=math.cos(winddir*f)*windvel
wind_y=math.sin(winddir*f)*windvel
print "wind_x: %f, wind_y: %f"%(wind_x,wind_y)             

#sin(wca)*tas = wind_y 
wca=-math.asin(wind_y/tas)/f
print "wca:",wca
tas_x=math.cos(wca*f)*tas
tas_y=math.sin(wca*f)*tas
print "tas_x: %f, tas_y: %f"%(tas_x,tas_y)
print "TAS is still:",math.sqrt(tas_x**2+tas_y**2)
GS = math.sqrt((tas_x+wind_x)*(tas_x+wind_x)+(tas_y+wind_y)*(tas_y+wind_y));

print "GS: %f"%(GS,)



"""
  def calculate_wca(self): #wind correction angle
        wind=self.get_wind_vector()
        ttdir=self.get_ttdir()
        tas=self.get_tas()        
        headwind=(-1.0)*(ttdir.normalized()*wind)
        print "Headind component:",headwind
        crosswind=ttdir.normalized().crossprod(Vector(0,0,1))*wind
        print "Crosswind component:",crosswind
        if abs(crosswind)>tas:
            raise Exception("Crosswind is greater than TAS!")
        if headwind>tas:
            raise Exception("Headwind is greater than TAS!")
        if abs(tas)<1e-7: raise Exception("TAS too small")        
        steer_angle=-asin(crosswind/tas)
        
        print "Steer angle:",(180/math.pi)*steer_angle,"deg"
        
        gsplushead=tas*cos(steer_angle)
        gs=gsplushead-headwind
        dist=float(self.d.GetValue())
        self.gs.SetValue("%.1f (%.0f km/h"%(gs,gs*1.852))
        self.time_exact=dist/gs
        time_min=math.floor(0.5+60.0*dist/gs)
        self.time.SetValue("%dh%dm"%(time_min/60,time_min%60))
        #gs=        
        return steer_angle
"""
