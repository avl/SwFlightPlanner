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

    
if __name__=='__main__':
    for funcname,func in list(globals().items()):
        def printer(*args):
            ret=func(*args)
            print "%s(%s) -> %s"%(funcname,", ".join(args),ret)
        globals()['funcname']=printer
    print "Calc sunrise/sunset today:"
    task=(datetime(2011,5,4,9,18),60.48,170.75)
    print "Rise:", sunrise_str(*task)
    print "Set:", sunset_str(*task)
    rise,fall,what=sunriseset(*task)
    if rise:
        print rise.strftime("%c")
    if fall:
        print fall.strftime("%c")
        