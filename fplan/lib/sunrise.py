from datetime import datetime,timedelta
import math
def fromrad(rad):
    return rad*(180.0/math.pi)
def torad(ang):
    return ang*(math.pi/180.0)
def sin(ang):
    return math.sin(torad(ang))
def cos(ang):
    return math.cos(torad(ang))
def arcsin(x):
    return fromrad(math.asin(x))
def arccos(x):
    return fromrad(math.acos(x))
def atan2(x,y):
    return fromrad(math.atan2(y,x))



offset=2455591-4046.5
fake_epoch=datetime(2000,1,1,00,00)

def dt2julian_day(dt):
    delta=(dt-fake_epoch)
    return offset+delta.days+delta.seconds/86400.0+delta.microseconds/(86400*1e6)
def julian_day2dt(jd):    
    delta=timedelta(jd-offset)
    return fake_epoch+delta

def julian_cycle(jdn,longwest):
    return round(jdn-2451545-0.0009-longwest/360.0)
def solar_noon(n,longwest):
    return 2451545+0.0009+longwest/360.0+n
def mean_anomaly(j):
    return (357.5291+0.98560028*(j-2451545))%360.0
def eq_center(M):
    return 1.9148*sin(M)+0.0200*sin(2*M)+0.0003*sin(3.0*M)

def ecliptic_longitude(M,C):
    return (M+102.9372+C+180.0)%360.0
def solar_transit(J,M,l):
    return J+(0.0053*sin(M))-(0.0069*sin(2*l))
def declination(l):
    return arcsin(sin(l)*sin(23.45))
def hour_angle(lat,d):
    arg=(sin(-0.83)-sin(lat)*sin(d))/(cos(lat)*cos(d))
    if (arg<-1 or arg>+1):
        return None
    return arccos(arg)
springautumn=set([3,9])
northernsummer=set([4,5,6,7,8])

def earliestsunset(dts,poss):
    candidates=[]
    for dt in dts:
        for pos in poss:
            lat,lon=pos
            up,down,what=sunriseset(dt,lat,lon)
            candidates.append((down,what))
    def key(x):
        down,what=x
        if what=='polar night':
            return (0,0)
        elif what=='polar twilight':
            return (1,0)
        elif what==None:
            return (2,down)
        else:
            assert what=='midnight sun'
            return (3,0)
    return min(candidates,key=key)
                

def sunriseset(dt,latitude,longitude):
    """
    Returns a tuple of three values:
    sunrise - Sunrise in UTC, or None if no sunrise this date.
    sunset - Sunset in UTC, or None if no sunrise this date.
    indicator - Four options:
        None - Normal case. Sunrise and sunset are not None in this case.
        "midnight sun" - Sun is up all day.
        "polar night" - Sun doesn't rise at all this day.
        "polar twilight" - The sun doesn't rise or set, but it skims along close to the horizon. This algorithm couldn't determine if it was just below or just above.
    """
    longitude_west=-longitude
    jdn=dt2julian_day(dt)
    n=julian_cycle(jdn,longitude_west)
    J=solar_noon(n,longitude_west)
    M=mean_anomaly(J)
    C=eq_center(M)
    l=ecliptic_longitude(M,C)
    transit=solar_transit(J,M,l)
    d=declination(l)
    ha=hour_angle(latitude,d)
    if ha==None:
        if latitude>0:
            if dt.month in springautumn:
                return None,None,'polar twilight'
            if dt.month in northernsummer:
                return None,None,'midnight sun'
            return None,None,'polar night'
        else:
            if dt.month in springautumn:
                return None,None,'polar twilight'
            if dt.month in northernsummer:
                return None,None,'polar night'
            return None,None,'midnight sun'
            
    down=2451545+0.0009+((ha+longitude_west)/360.0+n+0.0053*sin(M))-0.0069*sin(2.0*l)
    up=transit-(down-transit)
    
    return julian_day2dt(up),julian_day2dt(down),None
def sunrise_str(dt,latitude,longitude):
    up,down,what=sunriseset(dt,latitude,longitude)
    if what!=None:
        return "--:--"
    return up.strftime("%H:%MZ")
def sunset_str(dt,latitude,longitude):
    up,down,what=sunriseset(dt,latitude,longitude)
    if what!=None:
        return "--:--"
    return down.strftime("%H:%MZ")


#TODO: ALso calc sun position using
#http://pvcdrom.pveducation.org/SUNLIGHT/SUNPOS.HTM
#http://www.math.niu.edu/~rusin/uses-math/position.sun/


def equation_of_time(d):
    B=(360.0/365.0)*(d-81.0)
    return 9.87*sin(2*B)-7.53*cos(B)-1.5*sin(B)

class Vector(object):
    def __init__(self,*a):
        if len(a)==0:
            self.x=[0,0,0]
        else:
            self.x=[a[0],a[1],a[2]]
    def __str__(self):
        return "Vector("+",".join("%.3f"%(x,) for x in self.x)+")"
    def __mul__(self,v):
        if isinstance(v,Vector):
            assert len(self.x)==3
            assert len(v.x)==3
            return sum(x*y for x,y in zip(self.x,v.x))
        assert len(self.x)==3
        return Vector(*[v*a for a in self.x])
    def __rmul__(self,v):
        return self.__mul__(v)
    def __add__(self,v):
        return Vector(*[a+b for a,b in zip(self.x,v.x)])
    def __sub__(self,v):
        return Vector(*[a-b for a,b in zip(self.x,v.x)])
    def length(self):
        return math.sqrt(sum(a**2 for a in self.x))
    def normalized(self):
        l=self.length()
        if abs(l)<1e-8:
            return Vector(1,0,0)
        else:
            return (1.0/l)*self
    def cross(self,o):
        x=self.x
        return Vector(
            x[1]*o.x[2] - x[2]*o.x[1],
            x[2]*o.x[0] - x[0]*o.x[2],
            x[0]*o.x[1] - x[1]*o.x[0])
        
def time_correction_factor(longitude,eot):
    return 4.0*(longitude)+eot
def local_solar_time(local_time,time_correction):
    return local_time+time_correction/60.0
def hourangle2(lst):
    return 15.0*(lst-12.0)
def declination2(d):
    return 23.45*sin((360.0/365.0)*(d-81.0))

def frompolar(latitude,longitude):
    z=sin(latitude)  #z = 0 on equation
    a=cos(latitude)
    x=a*cos(longitude)  #x=1 on longitude meridian
    y=a*sin(longitude)  #y=1 on 90E
    return Vector(x,y,z)
def topolar(v):
    x,y,z=v.normalized().x
    azi=atan2(x,y)
    r=math.sqrt(x**2.0+y**2.0)
    ele=atan2(r,z)
    return ele,azi
    
def sun_position_in_sky(dt,latitude,longitude):
    UP=frompolar(latitude,0)
    #print "Calc sun-pos for %s at %f,%f"%(dt,latitude,longitude)
    dz=cos(latitude)
    dx=-sin(latitude)
    dy=0
    TN=Vector(dx,dy,dz)
    left=TN.cross(UP)
    
    #print "Reference system UP, TN, left:",UP,TN,left
    yearstart=dt.replace(month=1,day=1,hour=0,minute=0,second=0,microsecond=0)
    since=(dt-yearstart)
    d=since.days+since.seconds/86400.0
    localtime=dt.hour+dt.minute/60.0+dt.second/3600.0
    eot=equation_of_time(d)
    tc=time_correction_factor(longitude,eot)
    lst=local_solar_time(localtime,tc)
    ha=hourangle2(lst)
    decl=declination2(d)
    
    sunvec=frompolar(decl,ha)
    #print "Sunvec:",sunvec
    local=Vector(
            -(sunvec*TN),
            sunvec*left,
            sunvec*UP)
    #print "Local:",local
    ele,azi=topolar(local)
    azi+=180.0
    azi%=360.0
    #print "Calculated azi=%f, ele=%f"%(azi,ele)
    return ele,azi
            
    
    
if __name__=='__main__':
    for funcname in [
                          "frompolar",
                          "topolar",
                          "equation_of_time",
                          "time_correction_factor",
                          "local_solar_time",
                          "hourangle2",
                          "declination2"
                          ]:
        func=globals()[funcname]
        if funcname[0].isupper(): continue
        def makefun(func,funcname):
            def fun(*args):
                ret=func(*args) 
                print "%s(%s) -> %s"%(funcname,", ".join(str(x) for x in args),ret)
                return ret
            return fun
        globals()[funcname]=makefun(func,funcname)
    
    print "Calc sun pos now"
    task=(datetime(2011,1,31,15,00,0),59.3333,18.0+1.0/30)
    print "position:",sun_position_in_sky(*task)
    
    if 0:
        print "Calc sunrise/sunset today:"
        task=(datetime(2011,5,4,9,15),60.48,170.75)
        print "Rise:", sunrise_str(*task)
        print "Set:", sunset_str(*task)
        rise,fall,what=sunriseset(*task)
        if rise:
            print rise.strftime("%c")
        if fall:
            print fall.strftime("%c")
            
            
        
        