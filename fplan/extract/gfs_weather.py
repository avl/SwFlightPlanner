import threading
import pygrib

import math
import fetchdata
import os.path
from datetime import datetime,timedelta
import traceback
import numpy
import sys
import shutil

def get_std_press(alt):
    p0=101325
    L=0.0065
    T0=288.15
    g=9.80665
    M=0.0289644
    R=8.31447        
    alt_m=alt*0.3048
    press=p0*(1-(L*alt_m)/T0)**((g*M)/(R*L))
    press_mbar=press/100
    return press_mbar

def get_std_alt(press):
    p0=101325
    L=0.0065
    T0=288.15
    g=9.80665
    M=0.0289644
    R=8.31447        
    alt_m=-(T0*((100.0*press/p0)**(L*R/(g*M))-1))/L
    alt=alt_m/0.3048
    return alt

def get_press(qnh,surftemp,alt):
    p0=qnh*100.0
    L=0.0065
    T0=surftemp+273.15 #288.15
    g=9.80665
    M=0.0289644
    R=8.31447        
    alt_m=alt*0.3048
    press=p0*(1-(L*alt_m)/T0)**((g*M)/(R*L))
    press_mbar=press/100
    return press_mbar

def get_alt(qnh,surftemp,press):
    p0=qnh*100.0
    L=0.0065
    T0=surftemp+273.15 #288.15
    g=9.80665
    M=0.0289644
    R=8.31447        
    alt_m=-(T0*((100.0*press/p0)**(L*R/(g*M))-1))/L
    alt=alt_m/0.3048
    return alt

def fl2feet(fl,surftemp,qnh):
    stdfeet=fl*100
    press=get_std_press(stdfeet)
    return get_alt(qnh,surftemp,press)

    
    


def get_values(item,trg,convfun):
    lats,lons=item.latlons()
    level=item['level']
    us=item.values
    for y in xrange(us.shape[0]):
        for x in xrange(us.shape[1]):
            lat,lon=lats[y,x],lons[y,x]
            if lat<0:continue
            lat=int(lat)
            lon=int(lon)
            value=us[y,x]
            #print lat,lon,value
            trg[lat,lon]=convfun(value)
            #if lat==18 and lon==59:
            #    print "Stockholm",comp,"level",level,"wind:",value*3.6/1.852
    
class GfsForecast(object):
    def get_qnh(self,lat,lon):
        lat=int(lat)
        lon=int(lon)
        return self.qnh[lat,lon]/10.0

    def get_wind(self,lat,lon,altitude):        
        assert type(altitude) in [float,int]
        winds=self.get_winds(lat,lon)
        last_dir=None
        last_st=None
        last_alt=None
        #print "Fetching weather for",altitude
        for fl,dir,st,temp in sorted(winds):
            alt=fl*100
            #print "Comparing",altitude,alt
            if altitude<alt:                
                #print "Using alt",alt
                if last_dir==None or altitude<last_alt:
                    #print "Using first alt",alt
                    return dict(direction=dir,knots=st)
                ratio=(altitude-last_alt)/(alt-last_alt)
                #print "In between ",last_alt,"and",alt,"ratio:",ratio
                return dict(direction=(1-ratio)*last_dir+ratio*dir,knots=(1-ratio)*last_st+ratio*st)            
            last_alt=alt
            last_dir=dir
            last_st=st
        #print "Using last alt",alt
        return dict(direction=last_dir,knots=last_st)
    def get_winds(self,lat,lon):
        lat=int(lat)
        lon=int(lon)
        for (fl,xwind0),(fl2,ywind0),(fl3,temp0) in zip(self.xwinds,self.ywinds,self.temps):
            assert fl==fl2==fl3
            x=float(xwind0[lat,lon])
            y=float(ywind0[lat,lon])
            temp=float(temp0[lat,lon])
            st=(x*x+y*y)**0.5
            dir=(360+180+90-(180.0/math.pi)*math.atan2(y,x))%360.0
            #print "x,y -> dir",x,y,dir
            yield (fl,dir,st/100,temp/10.0)
    
    def __init__(self,xwinds,ywinds,temps,qnh):
        self.xwinds=xwinds
        self.ywinds=ywinds
        self.temps=temps
        self.qnh=qnh
            
    
def get_nominal_prognosis():
    now=datetime.utcnow()
    dt=now.replace(microsecond=0,second=0,minute=0,hour=now.hour-now.hour%6)
    ahead=now-dt
    if ahead<timedelta(0,3600):
        dt-=timedelta(0,3600*6)
    return dt


def create_gfs_cache():
    def dates():
        d=datetime.utcnow()
        for x in xrange(4):
            yield d
            d+=timedelta(0,3600*3)
    out=dict()
    for valid_for_dt in dates():
        for backoff in [0,6]:
            prog_date=get_nominal_prognosis()-timedelta(0,3600*backoff)
            offset=valid_for_dt-prog_date
            offset_hours=offset.seconds/3600.0
            offset_3hours=int(3*round(offset_hours/3.0))
            if offset_3hours<0:
                offset_3hours=0
            assert offset_3hours%3==0
            
            gfs=get_gfs(prog_date,offset_3hours)
            if gfs==None:
                continue
            out[(prog_date,offset_3hours)]=gfs
            break
    return out


def get_gfs(dt,future):    
    gfspath=None
    sdate=dt.strftime("%Y%m%d%H")
    shour=dt.strftime("%H")
    print "Trying download for",sdate
    url='http://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.%s/gfs.t%sz.pgrbf%02d.grib2'%(sdate,shour,future)
    try:
        gfspath=fetchdata.getdatafilename(
                    url,
                    country='raw',maxcacheage=86400*24)
    except:
        print traceback.format_exc()
        fetchdata.deletecache(url)
        return None
    if os.path.getsize(gfspath)<=100:
        fetchdata.deletecache(url)
        return None
    return get_gfs_impl(gfspath,future)

def get_gfs_impl(gfspath,future=0):
        
    gridf=pygrib.open(gfspath)
    
    grid=gridf.read()
    alts=[False for x in xrange(10)]
    
    xwind=[]
    ywind=[]
    temps=[]
    qnh=numpy.zeros((91,360),dtype=numpy.int16)
    
    pressure2alt=[None for x in xrange(1014)]
    first_mbar=None
    for alt in xrange(12500):
        press_mbar=get_std_press(alt)
        #print "pressure at alt",alt," is ",press_mbar
        if not first_mbar:
            pressure2alt[int(press_mbar)]=alt
            first_mbar=press_mbar
        else:
            if int(first_mbar)!=int(press_mbar):
                assert pressure2alt[int(press_mbar)+1]!=None 
                pressure2alt[int(press_mbar)]=alt
    #for press,alt in enumerate(pressure2alt):
    #    print "press,alt",press,alt
    
    msltemp=numpy.zeros((91,360),dtype=numpy.int16)
    
    
    h1000_km=get_std_alt(1000)*0.3048/1e3
    print "h1000 km",h1000_km
    h1000stdtemp=(273.15+15)-h1000_km*6.5
    print "h1000 std temp:",h1000stdtemp
    
    def tomsl_temp(temp):
        #print "1000 hpa temp:",temp," (std: ",h1000stdtemp,")"
        delta=temp-h1000stdtemp
        #print "delta",delta
        return 10*(15+delta)
    
    for item in grid:
        #print "\n".join(sorted(item.keys()))
        if item['name'].lower().count("pressure reduced to msl"):
            get_values(item,qnh,lambda value:value/10)
        if item['name'].lower().count("temperature"):
            if item['typeOfLevel']=="isobaricInhPa" and item['level']==1000:                
                get_values(item,msltemp,tomsl_temp)
            
    print "QNH:",10*qnh[59,18]/100.0,"hPa"
        
    print "Temp:",msltemp[59,18]/10.0,"C"
                
    

    for item in grid:        
        if item['typeOfLevel']!="isobaricInhPa":
            continue
        if pressure2alt[item['level']]==None:
            continue
        for comp in ['U','V']:
            #U blows to the east (from west to east)
            #V blows to the north (from south to north)
            if item['name']==comp+' component of wind':
                convfun=lambda value:value*100.0*3.6/1.852
                trg=numpy.zeros((91,360),dtype=numpy.int16)
                fl=pressure2alt[item['level']]/100.0
                print "Adding for FL",fl
                if comp=='U':
                    xwind.append((fl,trg))
                elif comp=='V':
                    ywind.append((fl,trg))
                get_values(item,trg,convfun)
                
        if item['name'].lower().count("temperature"):
            fl=pressure2alt[item['level']]/100.0
            temps.append((fl,numpy.zeros((91,360),dtype=numpy.int16)))
            get_values(item,temps[-1][1],lambda x:10*(x-273.15))
                    
    return GfsForecast(xwinds=xwind,ywinds=ywind,temps=temps,qnh=qnh)


import cPickle as pickle

gfswcache=dict()
gfswlock=threading.Lock()
gfswfiledate=None
lastcachecheck=None

def ensure_cache():
    global gfswcache
    global gfswfiledate
    try:
        ftime=os.path.getmtime("gfsweather.dat")
    except:
        print "No weather cache existing file"
        return
    if gfswfiledate==None or gfswfiledate!=ftime:
        try:                
            gfswcache=pickle.load(open("gfsweather.dat"))
            gfswfiledate=ftime
        except:
            print traceback.format_exc()
            return
                

def get_prognosis(when):
    global lastcachecheck
    gfswlock.acquire()        
    try:
        if lastcachecheck==None or datetime.utcnow()-lastcachecheck>timedelta(0,60):
            lastcachecheck=datetime.utcnow()
            print "Loading cache"
            ensure_cache()
        for backoff in [0,6]:
            prog_date=get_nominal_prognosis()-timedelta(0,3600*backoff)
            offset=when-prog_date
            offset_hours=offset.seconds/3600.0
            offset_3hours=int(3*round(offset_hours/3.0))
            if offset_3hours<0:
                offset_3hours=0
            assert offset_3hours%3==0
            key=(prog_date,offset_3hours)
            if key in gfswcache:
                return prog_date,prog_date+timedelta(0,3600*offset_3hours),gfswcache[key]
            continue
        return None,None,None             
    finally:
        gfswlock.release()
    return None,None,None
    
    

def dump_gfs_cache():
    fct=create_gfs_cache()
    #print "QNH:",fct.qnh[59,18]/10.0,"hPa"
    print "Wind:",
    f=open("gfsweather.dat.tmp","w")
    pickle.dump(fct,f,-1)
    f.close()
    shutil.move("gfsweather.dat.tmp","gfsweather.dat")
    

if __name__=='__main__':
    when,fct=get_prognosis(datetime.utcnow())
    print "For",when
    for fl,dir,st,temp in fct.get_winds(59,18):
        print "FL%d (%f feet): %03d deg, %.1fkt, %.1f C"%(int(fl),fl2feet(fl,15,fct.qnh[59,18]/10.0),int(dir),float(st),temp)
    for fl,dir,st,temp in fct.get_winds(59,19):
        print "FL%d (%f feet): %03d deg, %.1fkt, %.1f C"%(int(fl),fl2feet(fl,15,fct.qnh[59,18]/10.0),int(dir),float(st),temp)
        
