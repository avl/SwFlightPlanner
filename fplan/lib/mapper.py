#encoding=utf8
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
    #print "lat,lon:",lat,lon
    assert lat>=-85 and lat<=85
    assert lon>=-180 and lon<=180
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

def approx_scale(merc_coords,zoomlevel,length_in_nautical_miles):
    """Return the number of mercator proj 'pixels'
    which correspond most closely to the distance given in nautical miles.
    This scale is only valid at the latitude of the given mercator coords. 
    """  
    x,y=merc_coords
    factor=(2.0**(zoomlevel))
    lat=unmerc((128*factor-y)/128.0/factor*merc(85.05113))
    latrad=lat/(180.0/math.pi)
    scale_diff=math.cos(latrad)
    return 256*factor*(float(length_in_nautical_miles)/(360*60.0))/scale_diff
    
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
    
class MapperBadFormat(Exception):pass    
def parse_lfv_format(lat,lon):    
    """Throws MapperBadFormat if format can not be parsed"""
    if not lat[0:4].isdigit():
        raise MapperBadFormat("%s,%s"%(lat,lon))    
    latdeg=float(lat[0:2])
    latmin=float(lat[2:4])
    if len(lat)>5:
        if not lat[4:6].isdigit():
            raise MapperBadFormat("%s,%s"%(lat,lon))    
        latsec=float(lat[4:6])
    else:
        latsec=0
    if not lon[0:5].isdigit():
        raise MapperBadFormat("%s,%s"%(lat,lon))    
    londeg=float(lon[0:3])
    lonmin=float(lon[3:5])
    if len(lon)>6:
        if not lon[5:7].isdigit():
            raise MapperBadFormat("%s,%s"%(lat,lon))    
        lonsec=float(lon[5:7])
    else:
        lonsec=0
    latdec=latdeg+latmin/60.0+latsec/(60.0*60.0)
    londec=londeg+lonmin/60.0+lonsec/(60.0*60.0)
    if lat[-1]=='S':
        latdec=-latdec
    elif lat[-1]!='N':
        raise MapperBadFormat("%s,%s"%(lat,lon))    
    if lon[-1]=='W':
        londec=-londec
    elif lon[-1]!='E':
        raise MapperBadFormat("%s,%s"%(lat,lon))    
    return '%.10f,%.10f'%(latdec,londec)

parse_coords=parse_lfv_format
def format_lfv(lat,lon):
    out=[]   
    for c,(pos,neg) in [(lat,('N','S')),(lon,('E','W'))]:
        if c<0:
            sign=-1
            H=neg
            c=-c
            assert c>=0
        else:
            H=pos
            sign=1
        totseconds=int(round(c*60.0*60.0))
        degrees=totseconds//3600
        totseconds-=3600*degrees
        minutes=totseconds//60
        totseconds-=60*minutes
        seconds=totseconds
        if pos=='N': #latitude            
            out.append("%02d%02d%02d%s"%(degrees,minutes,seconds,H))
        else:
            out.append("%03d%02d%02d%s"%(degrees,minutes,seconds,H))
    return " ".join(out)

def format_lfv_ats(lat,lon):
    out=[]   
    for c,(pos,neg) in [(lat,('N','S')),(lon,('E','W'))]:
        if c<0:
            sign=-1
            H=neg
            c=-c
            assert c>=0
        else:
            H=pos
            sign=1
        totseconds=int(round(c*60.0*60.0))
        degrees=totseconds//3600
        totseconds-=3600*degrees
        minutes=totseconds//60
        if pos=='N': #latitude            
            out.append("%02d%02d%s"%(degrees,minutes,H))
        else:
            out.append("%03d%02d%s"%(degrees,minutes,H))
    return "".join(out)
        
def parse_lfv_area(area):
    found=False
    for lat,lon in re.findall(r"(\d{4,6}(?:,\d+)?[NS])\s*(\d{5,7}(?:,\d+)?[EW])",area):
        yield parse_lfv_format(lat.strip(),lon.strip())
        found=True
    if not found:
        for lat,lon in re.findall(r"([-+]?\d{1,3}\.?\d*)\s*,\s*([-+]?\d{1,3}\.?\d*)",area):
            yield "%.10f,%.10f"%(float(lat),float(lon))
        
                
   
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
    """bearing in degrees, distnace in km"""
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
    
        


def minus(x,y):
    return tuple(a-b for a,b in zip(x,y))
def plus(x,y):
    return tuple(a+b for a,b in zip(x,y))
def scalarprod(x,y):
    return sum(a*b for a,b in zip(x,y))
def parsecoord(seg):
    latlon=seg.strip().split(" ")
    if len(latlon)!=2:
        raise MapperBadFormat()
    lat,lon=latlon
    coord=parse_coords(lat.strip(),lon.strip())
    return coord

def seg_angles(a1,a2,step):
    assert a2>a1
    dist=a2-a1
    nominal_cnt=math.ceil(dist/step)
    if nominal_cnt<=1:
        yield a1
        yield a2
        return
    delta=dist/float(nominal_cnt)
    a=a1
    for x in xrange(int(nominal_cnt)):
        yield a
        a+=delta
    yield a2
     
    
def create_circle(center,dist_nm):
    zoom=14
    centermerc=latlon2merc(from_str(center),zoom)
    radius_pixels=approx_scale(centermerc,zoom,dist_nm)
    steps=dist_nm*math.pi*2/5.0
    if steps<16:
        steps=16
    out=[]
    angles=list(seg_angles(0,2.0*math.pi,math.pi*2.0/steps))
    for cnt,a in enumerate(angles):
        if cnt!=len(angles)-1:
            x=math.cos(a)*radius_pixels
            y=math.sin(a)*radius_pixels
            out.append(plus((x,y),centermerc))
    out2=[]
    for o in out:
        out2.append(to_str(merc2latlon(o,zoom)))
    return out2
    
def create_seg_sequence(prevpos,center,nextpos,dist_nm):
    zoom=14
    prevmerc=latlon2merc(from_str(prevpos),zoom)
    centermerc=latlon2merc(from_str(center),zoom)
    nextmerc=latlon2merc(from_str(nextpos),zoom)
    
    d1=minus(prevmerc,centermerc)
    d2=minus(nextmerc,centermerc)
    a1=math.atan2(d1[1],d1[0])
    a2=math.atan2(d2[1],d2[0])
    
    radius_pixels=approx_scale(centermerc,zoom,dist_nm)
    
    if a2<a1:
        a2+=math.pi*2
    if abs(a2-a1)<1e-6:
        return []
    steps=abs(a2-a1)/(math.pi*2.0)*dist_nm*math.pi*2/5.0
    if steps<16:
        steps=16
    out=[]
    angles=list(seg_angles(a1,a2,abs(a2-a1)/steps))
    for cnt,a in enumerate(angles):
        if cnt!=0 and cnt!=len(angles)-1:
            x=math.cos(a)*radius_pixels
            y=math.sin(a)*radius_pixels
            out.append(plus((x,y),centermerc))
    out2=[]
    for o in out:
        out2.append(to_str(merc2latlon(o,zoom)))
    return out2
def uprint(s):
    if type(s)==unicode:
        print s.encode('utf8')
    else:
        print s
def parse_dist(s):
    #uprint("In:%s"%s)
    val,nautical,meters=re.match(r"\s*([\d.]+)\s*(?:(NM)|(m))\b\s*",s).groups()
    dval=float(val)
    assert nautical!=None or meters!=None
    if meters:
        dval=dval/1852.0
    return dval


def parse_area_segment(seg,prev,next):
    try:
        c=[parsecoord(seg)]
        #print "Parsed as regualr coord: ",c
        return c
    except MapperBadFormat:
        pass #continue processing
    border=re.match("Swedish/Danish border northward to (.*)",seg)
    if border:
        lat,lon=border.groups()[0].strip().split(" ")
        return [parsecoord(border.groups()[0])]
    arc=re.match(r"\s*clockwise along an arc cent[red]{1,5} on (.*) and with radius (.*)",seg)
    if arc:
        centerstr,radius=arc.groups()
        #uprint("Parsing coord: %s"%centerstr)
        center=parsecoord(centerstr)
        dist_nm=parse_dist(radius)
        prevpos=parsecoord(prev)
        nextpos=parsecoord(next)
        #uprint("Arc center: %s"%(center,))
        #uprint("Seg params: %s %s %s %s"%(prevpos,center,dist_nm,nextpos))
        return create_seg_sequence(prevpos,center,nextpos,dist_nm)
    #uprint("Matching against: %s"%(seg,))
    circ=re.match(r"\s*A circle with radius ([\d\.]+ (?:NM|m))\s+(?:\(.* k?m\))?\s*cent[red]{1,5}\s*on\s*(\d+N) (\d+E)\b.*",seg)
    if circ:
        radius,lat,lon=circ.groups()
        assert prev==None and next==None        
        #uprint("Parsed circle:%s : %s"%(circ,circ.groups()))
        dist_nm=parse_dist(radius)
        zoom=14
        center=parse_coords(lat,lon)
        return create_circle(center,dist_nm)
    
    #uprint("Unparsed area segment: %s"%(seg,))
    return []

def parse_coord_str(s):
    borderspecs=[
        "Swedish/Danish border northward to",
        "Swedish/Norwegian border northward to",
        ]
    #uprint("Parsing area: %s"%(s,))
    
    items=s.replace(u"–","-").strip().split("-")
    out=[]
    for idx,pstr2 in enumerate(items):
        prev=None
        next=None
        if idx!=0:
            prev=items[idx-1]
        if idx!=len(items)-1:
            next=items[idx+1]
        pstr=pstr2.strip()
        #print "Coord str: <%s>"%(pstr,)
        
        for spec in borderspecs:
            if pstr.count(spec):
                pstr=pstr.replace(spec,"")
                break                
        if pstr.strip()=="": continue
        pd=parse_area_segment(pstr,prev,next)
        #uprint("Parsed area segment <%s> into <%s>"%(pstr,pd))
        out.extend(pd)
    if len(out)<3:
        raise Exception("Too few items in coord-str: <%s>"%(s,))
    return out
    
class NotAnAltitude(Exception):pass
def parse_elev(elev):    
    if type(elev)==int: return float(elev)
    if type(elev)==float: return elev
    if not isinstance(elev,basestring):
        raise NotAnAltitude(repr(elev))
    elev=elev.strip()
    if elev.upper().startswith("FL"): elev=elev[2:].strip().lstrip("0")+"00" #Gross simplification
    if elev.lower().endswith("ft"): elev=elev[:-2].strip()
    if not elev.isdigit():
        raise NotAnAltitude(repr(elev))
    return int(elev)
    
