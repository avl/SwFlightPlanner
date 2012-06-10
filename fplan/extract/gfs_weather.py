import pygrib
import math
import fetchdata
import os.path
from datetime import datetime,timedelta
import traceback
import numpy
import sys

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
    

def get_gfs():
    now=datetime.utcnow()
    gfspath=None
    for backoff in [0,6,12]:
        dt=now.replace(microsecond=0,second=0,minute=0,hour=now.hour-now.hour%6-backoff)
        sdate=dt.strftime("%Y%m%d%H")
        shour=dt.strftime("%H")
        print "Trying download for",sdate
        url='http://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.%s/gfs.t%sz.pgrbf00.grib2'%(sdate,shour)
        try:
            gfspath=fetchdata.getdatafilename(
                        url,
                        country='raw',maxcacheage=86400)
        except:
            print traceback.format_exc()
            gfspath=None
            fetchdata.deletecache(url)
            continue
        if os.path.getsize(gfspath)<=100:
            gfspath=None
            fetchdata.deletecache(url)
            continue
        break
    if gfspath==None:
        raise Exception("GFS download failed")
        
    gridf=pygrib.open(gfspath)
    
    grid=gridf.read()
    alts=[False for x in xrange(10)]
    
    xwind=[]
    ywind=[]
    qnh=numpy.zeros((91,360),dtype=numpy.int16)
    
    pressure2alt=[None for x in xrange(1014)]
    first_mbar=None
    for alt in xrange(9500):
        p0=101325
        L=0.0065
        T0=288.15
        g=9.80665
        M=0.0289644
        R=8.31447        
        alt_m=alt*0.3048
        press=p0*(1-(L*alt_m)/T0)**((g*M)/(R*L))
        press_mbar=int(press/100)
        #print "pressure at alt",alt," is ",press_mbar
        if not first_mbar:
            pressure2alt[press_mbar]=alt
            first_mbar=press_mbar
        else:
            if first_mbar!=press_mbar:
                assert pressure2alt[press_mbar+1]!=None 
                pressure2alt[press_mbar]=alt
    #for press,alt in enumerate(pressure2alt):
    #    print "press,alt",press,alt
    
    for item in grid:
        #print "\n".join(sorted(item.keys()))
        if item['name'].lower().count("pressure reduced to msl"):
            get_values(item,qnh,lambda value:value/10)
    print "QNH:",10*qnh[59,18]/100.0,"hPa"
                
    

    for item in grid:        
        for comp in ['U','V']:
            #U blows to the east (from west to east)
            #V blows to the north (from south to north)
            if item['typeOfLevel']!="isobaricInhPa":
                continue
            if item['name']==comp+' component of wind':
                convfun=lambda value:value*100.0*3.6/1.852
                if pressure2alt[item['level']]==None:
                    continue
                trg=numpy.zeros((91,360),dtype=numpy.int16)
                fl=pressure2alt[item['level']]/100.0
                print "Adding for FL",fl
                if comp=='U':
                    xwind.append((fl,trg))
                elif comp=='V':
                    ywind.append((fl,trg))
                get_values(item,trg,convfun)
    def get_wind(lat,lon):
        for (fl,xwind0),(fl2,ywind0) in zip(xwind,ywind):
            assert fl==fl2
            x=float(xwind0[lat,lon])
            y=float(ywind0[lat,lon])
            st=(x*x+y*y)**0.5
            dir=(360+90-(180.0/math.pi)*math.atan2(y,x))%360.0
            #print "x,y -> dir",x,y,dir
            yield (fl,dir,st/100)
    print "QNH:",10*qnh[59,18]/100.0,"hPa"
    print "Wind:",
    for fl,dir,st in get_wind(59,18):
        print "FL%d: %03d deg, %.1fkt"%(int(fl),int(dir),float(st))
        
if __name__=='__main__':
    get_gfs()
        