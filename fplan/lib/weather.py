import fplan.extract.weather_chart_areas as weather_chart_areas
import fplan.extract.parse_llf_forecast as parse_llf_forecast
from pyshapemerge2d import Line,Vertex,Polygon,vvector
import fplan.lib.mapper as mapper
import math
from datetime import datetime,timedelta


class Weather():
    def get_wind(self,elev):
        if type(elev)!=int:
            elev=mapper.parse_elev(elev)
        ielev=int(elev)
        print "Ielev: ",ielev
        twothousand,fl50,fl100=self.winds['2000'],self.winds['FL50'],self.winds['FL100']
        def dcos(x):
            return math.cos(x/(180.0/math.pi))
        def dsin(x):
            return math.sin(x/(180.0/math.pi))
        def ipol(a,b,f):
            ax=dcos(a['direction'])*a['knots']
            ay=dsin(a['direction'])*a['knots']
            bx=dcos(b['direction'])*b['knots']
            by=dsin(b['direction'])*b['knots']
            x=(ax*(1.0-f)+bx*f)
            y=(ay*(1.0-f)+by*f)
            direction=(180.0/math.pi)*math.atan2(y,x)
            if direction<0: direction+=360.0
            knots=math.sqrt(x**2+y**2)
            res=dict(direction=direction,knots=knots)
            print "\nInterpolated %s and %s with f=%s into %s\n"%(a,b,f,res)
            return res
        
        if ielev<2000:
            return dict(knots=twothousand['knots'],direction=twothousand['direction'])
        elif ielev<5000:
            return ipol(twothousand,fl50,(ielev-2000.0)/(5000.0-2000.0))
        elif ielev<10000:
            return ipol(fl50,fl100,(ielev-5000.0)/(10000.0-5000.0))
        elif ielev>=10000:
            return dict(knots=fl100['knots'],direction=fl100['direction'])
        return dict(knots=0,direction=0)


parsed_weather_cache=None
def get_parsed_weather():
    global parsed_weather_cache
    if parsed_weather_cache:
        cache,when=parsed_weather_cache
        if datetime.utcnow()-when<timedelta(minutes=15):
            return cache
    fc=parse_llf_forecast.run('A')
    fc.update(parse_llf_forecast.run('B'))
    fc.update(parse_llf_forecast.run('C'))
    parsed_weather_cache=(fc,datetime.utcnow())
    return fc

def get_weather(lat,lon):
    zoomlevel=13
    px,py=mapper.latlon2merc((lat,lon),zoomlevel)
    w=Weather()
    areas=weather_chart_areas.get_areas()
    insides=[]
    dists=[]
    
    for name,area in areas.items():
        poly_coords=[]
        centerx=0.0
        centery=0.0
        for coord in area:
            x,y=mapper.latlon2merc(coord,zoomlevel)
            centerx+=x+0.0
            centery+=y+0.0
            poly_coords.append(Vertex(int(x),int(y)))
        if len(poly_coords)<3:
            print "Weather area %s has few points: %s "%(name,area)
            continue
        centerx/=len(poly_coords)
        centery/=len(poly_coords)
        cdist=(centerx-px)**2+(centery-py)**2
        poly=Polygon(vvector(poly_coords))
        if poly.is_inside(Vertex(int(px),int(py))):
            cdist*=1e-3
        insides.append((cdist,name,area))
    #print "insides:",insides
    insides.sort()
    dist,name,area=insides[0]
    if dist>20000**2:        
        return None        
    w.weather_area=name
    
    mainarea,rest=name.split("_")
    part=rest[:-2]
    seg=rest[-2:]
    
    try:
        fc=get_parsed_weather()
    except Exception,cause:
        print "Couldn't fetch weather: ",cause #there's no weather service at certain times.
        return None
    
    print "Reading weather from %s, %s"%(mainarea,part)
    w.winds=fc[(mainarea,part)]['winds']
    #print "Winds at position:",w.winds
    #llf=parse_llf_forecast.run()
    #print "\n\nLLF:",llf
    #print "Areas:",areas
    #w.areas=areas
    #w.llf=llf
    return w
def get_wind_at(lat,lon,alt):
    return get_weather(lat,lon).get_wind(alt)

if __name__=='__main__':
    w=get_weather(59,18.5)
    print "Weather, winds:",w.winds
    print "Get winds at @1000:",w.get_wind(1000)
    print "Get winds at @3000:",w.get_wind(3000)
    print "Get winds at @5000:",w.get_wind(5000)
    print "Get winds at @7000:",w.get_wind(7000)
    
    
