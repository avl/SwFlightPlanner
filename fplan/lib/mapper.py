import re
from itertools import count
import popen2
import math
import cStringIO

def sec(x):
        return 1.0/math.cos(x)

def merc(lat):
        lat/=(180.0/3.14159)
        return math.log(math.tan(lat)+sec(lat))
def unmerc(y):
        return (180.0/3.14159)*math.atan(math.sinh(y))
        
def latlon2merc(pos,zoomlevel):
	lat,lon=pos
	factor=(2.0**(zoomlevel))
	return (factor*256.0*(lon+180.0)/360.0,128*factor-128*factor*merc(lat)/merc(85.05113))
def merc2latlon(p,zoomlevel):
	x,y=p
	factor=(2.0**(zoomlevel))
	return (unmerc((128*factor-y)/128.0/factor*merc(85.05113)),x*360.0/(256.0*factor)-180.0)
def max_merc_y(zoomlevel):
    return 256*(2**zoomlevel)
def max_merc_x(zoomlevel):
    return 256*(2**zoomlevel)

	
def _from_decimal(x):
	"""From decimal lat/lon tuple to to format: N47-13'30" E12-49'37" """
	if x<0: return "-"+from_decimal(-x)
	tot_micros=int(1000000.0*60.0*60.0*x+0.5)
	factors=[
		(180,1000000*60*60),
		(60,1000000*60),
		(60,1000000),
		(1000000,1)
	]
	deg,minute,second,ms=\
		[(tot_micros/factor)%mod for mod,factor in factors]
	assert sum(x*factor for (x,(mod,factor)) in zip([deg,minute,second,ms],factors))==tot_micros
	c="%dd%d'%02d.%06d\""%(deg,minute,second,ms)
	return c

def from_str(pos):
	lat,lon=pos.split(",")
	lat=float(lat)
	lon=float(lon)
	return lat,lon
def to_str(pos):
	return "%.10f,%.10f"%pos
	
def from_aviation_format(pos):	
    lat_deg,lat_min,ns,lon_deg,lon_min,ew=re.match("(\d\d)([\d\.]*)([NS])(\d\d\d)([\d\.]*)([EW])",pos).groups()
    lat=float(lat_deg)+float(lat_min)/60.0
    lon=float(lon_deg)+float(lon_min)/60.0
    if (ns=='S'): lat=-lat
    if (ew=='W'): lon=-lon
    return lat,lon
   
def _to_deg_min(x):
	x*=60*10000
	x=int(math.floor(x)+0.5)
	deg=x/(60*10000)
	min=(x%(60*10000))/10000.0
	return deg,min

   
def to_aviation_format(latlon):
	lat,lon=latlon
	ns='N'
	if lat<0:
		ns='S'
		lat=-lat
	lat_deg,lat_min=_to_deg_min(lat)		
	ew='E'
	if lon<0:
		ew='W'
		lon=-lon
	lon_deg,lon_min=_to_deg_min(lon)		

	return "%02d%07.4f%s%03d%07.4f%s"%(
		lat_deg,lat_min,ns,
		lon_deg,lon_min,ew)
		      
    

def bearing_and_distance(start,end): #pos are tuples, (north-south,east-west)
	pos1=start
	pos2=end
	if pos1==pos2: return 0,0
	#print "Distance between called: <%s>, <%s>"%(pos1,pos2)
	a=[_from_decimal(float(pos)) for pos in pos1.split(",")]
	b=[_from_decimal(float(pos)) for pos in pos2.split(",")]	
	#x="""geod +ellps=WGS84 <<EOF -I +units=km
	#42d15' -71d07' 45d31' -123d41'
	#EOF
	#"""	
	#Coord order is: North/south, east/west, north/south2, east/west2
	x="""geod -p -f %%.6f -F %%.6f  +ellps=WGS84 <<EOF -I +units=km
%s %s %s %s
EOF"""%(a[0],a[1],b[0],b[1])
	#print "ARGS:",x
	#print "Popen:",x
	res=popen2.popen2(x)[0].read()
	#print "popen res: ",repr(res)
	splat=res.split('\t')
	dist=splat[2].split('\n')[0]
	if dist=="nan": return 0,0 #this seems to happen when distance is too short for geod program
	dist=float(dist)
	bearing=splat[0].strip()
	assert bearing!="nan"
	bearing=float(bearing)
	return bearing,dist
	
		

