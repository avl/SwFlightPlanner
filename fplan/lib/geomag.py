from datetime import datetime,timedelta
from fplanquick.fplanquick import geomag_calc

def decimal_year(dt):
    start=datetime(dt.year,1,1,0,0,0)
    end=datetime(dt.year+1,1,1,0,0,0)
    totdays=(end-start).days        
    delta=dt-start
    nowdays=delta.days+delta.seconds/86400.0+delta.microseconds/(86400*1e6)
    return float(dt.year)+float(nowdays)/float(totdays)

def calc_declination(pos,when,altitude_feet):
    """
    pos = (lat,lon)
    when = datetime in UTC
    altitude_feet = altitude. Set to 0 for surface.
    """
    altitude_km=altitude_feet*0.3048/1000.0
    
    decyear=decimal_year(when)
    
    lat,lon=pos
    
    return geomag_calc(lat,lon,decyear,altitude_km)
    

    
    