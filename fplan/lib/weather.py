import fplan.extract.weather_chart_areas as weather_chart_areas
import fplan.extract.parse_llf_forecast as parse_llf_forecast
from pyshapemerge2d import Line2,Vertex,Polygon,vvector
import fplan.lib.mapper as mapper
import math

class Weather():
    def get_wind(self,elev):
        if type(elev)!=int:
            elev=elev.strip()
            if elev.startswith("FL"): elev=elev[2:].strip() #Gross simplification
            if elev.endswith("ft"): elev=elev[:-2].strip()
            assert elev.isdigit()
        ielev=int(elev)
        
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
            x=0.5*(ax*(1.0-f)+bx*f)
            y=0.5*(ay*(1.0-f)+by*f)
            direction=(180.0/math.pi)*math.atan2(y,x)
            if direction<0: direction+=360.0
            knots=math.sqrt(x**2+y**2)
            return dict(direction=direction,knots=knots)
        
        if elev<2000:
            return dict(knots=twothousand['knots'],direction=twothousand['direction'])
        elif elev<5000:
            return ipol(twothousand,fl50,(elev-2000.0)/(5000.0-2000.0))            
        elif elev<10000:
            return ipol(fl50,fl100,(elev-5000.0)/(10000.0-5000.0))
        return dict(knots=0,direction=0)            
        
    
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
    
    
    fc=parse_llf_forecast.run()
    
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
    
    