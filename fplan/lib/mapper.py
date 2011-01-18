#encoding=utf8
import re
from itertools import count
import popen2
import math
import cStringIO
import math

def sec(x):
        return 1.0/math.cos(x)

def merc(lat):
        lat/=(180.0/3.14159)
        return math.log(math.tan(lat)+sec(lat))
def unmerc(y):
        return (180.0/3.14159)*math.atan(math.sinh(y))
        
def latlon2merc(pos,zoomlevel):
    lat,lon=pos
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

def approx_scale_lat(lat,zoomlevel,length_in_nautical_miles):
    """Return the number of mercator proj 'pixels'
    which correspond most closely to the distance given in nautical miles.
    This scale is only valid at the latitude of the given mercator coords. 
    """  
    factor=(2.0**(zoomlevel))
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

def approx_bearing_vec(vec_a,vec_b):
    dx=vec_b.get_x()-vec_a.get_x()
    dy=vec_b.get_y()-vec_a.get_y()
    tt=90.0-(math.atan2(-dy,dx)*180.0/math.pi)
    if tt<0: tt+=360.0
    return tt
    
def approx_dist_vec(vec_a,vec_b,zoomlevel):
    onenm=approx_scale((vec_a.get_x(),vec_b.get_x()),zoomlevel,1.0)
    dx=vec_b.get_x()-vec_a.get_x()
    dy=vec_b.get_y()-vec_a.get_y()
    mercd=math.sqrt(dx**2+dy**2)
    return mercd/onenm
    
    
    
class MapperBadFormat(Exception):pass    

compre=re.compile(ur"(\d{2,7})([\.,]\d+)?([NSEWnsew])")
def parse_coord_component(comp):
    m=compre.match(comp)
    if not m:
        raise MapperBadFormat(u"Bad format: %s"%(comp,))
    w,dec,what=m.groups()
    if dec!=None and dec.startswith(","):
        dec="."+dec[1:]
    decf=0.0
    what=what.upper()
    if len(w) in [2,3]:
        #Degree only
        wf=float(w)
        if dec:
            decf+=float("0"+dec)
    elif len(w) in [4,5]:
        #Degrees and minutes
        deg,minutes=w[:-2:],w[-2:]
        if dec:
            decf+=float("0"+dec)/60.0
        wf=float(deg)+float(minutes)/60.0        
    elif len(w) in [6,7]:
        #Degrees and minutes and seconds
        deg,minutes,seconds=w[:-4],w[-4:-2],w[-2:]
        if dec:
            decf+=float("0"+dec)/3600.0
        wf=float(deg)+float(minutes)/60.0+float(seconds)/3600.0
    else:
        raise MapperBadFormat(u"Bad format(2): %s"%(comp,))       
    return wf+decf,what


def parse_lfv_format(lat,lon):    
    latdec,what=parse_coord_component(lat)
    if what=='W':
        latdec=-latdec
    if not what in 'NS': raise MapperBadFormat("Bad format(3): %s,%s"%(lat,lon))
    londec,what=parse_coord_component(lon)
    if what=='W':
        londec=-londec
    if not what in 'EW': raise MapperBadFormat("Bad format(4): %s,%s"%(lat,lon))
    londec=(londec+180)%360-180
    if latdec<-85 or latdec>85:
        raise MapperBadFormat(u"Latitude out of range: %s %s : lat = %s"%(lat,lon,latdec))
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
        
def parse_lfv_area(area,allow_decimal_format=True):
    found=False
    for lat,lon in re.findall(r"(\d{4,6}(?:[,\.]\d+)?[NS])\s*(\d{5,7}(?:[,\.]\d+)?[EW])",area):
        yield parse_lfv_format(lat.strip(),lon.strip())
        found=True
    if not found and allow_decimal_format:
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
    """bearing in degrees, distance in km"""
    pos1=start
    pos2=end
    if pos1==pos2: return 0,0
    if type(pos1)==tuple and type(pos2)==tuple:
        a=pos1
        b=pos2
    else:
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
    return bearing,dist/1.852
    
        


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

def parsecoords(seg):
    coords=[]
    for lat,lon in re.findall(r"(\d+[\.,]?\d*[NS])\s*(\d+[\.,]?\d*[EW]\b)",seg):
        coord=parse_coords(lat.strip(),lon.strip())
        coords.append(coord)
    return coords


def seg_angles(pa1,pa2,step,direction):    
    a1=pa1
    a2=pa2
    if direction=="cw":
        if a2<a1:
            a2+=2*math.pi
        dist=a2-a1
    else:
        if a1<a2:
            a2-=2*math.pi
        dist=a1-a2
    #uprint("Dist:",dist)
    nominal_cnt=math.ceil(dist/step)
    if nominal_cnt<=1:
        yield pa1
        yield pa2
        return
    delta=dist/float(nominal_cnt)
    a=a1
    for x in xrange(int(nominal_cnt)):
        yield a
        if direction=="cw":
            a+=delta
        else:
            a-=delta
        if a>math.pi: a-=2.0*math.pi
        if a<-math.pi: a+=2.0*math.pi
    yield pa2
     
    
def create_circle(center,dist_nm):
    zoom=14
    centermerc=latlon2merc(from_str(center),zoom)
    radius_pixels=approx_scale(centermerc,zoom,dist_nm)
    steps=dist_nm*math.pi*2/5.0
    if steps<16:
        steps=16
    out=[]
    angles=list(seg_angles(0,2.0*math.pi,math.pi*2.0/steps,"cw"))
    for cnt,a in enumerate(angles):
        if cnt!=len(angles)-1:
            x=math.cos(a)*radius_pixels
            y=math.sin(a)*radius_pixels
            out.append(plus((x,y),centermerc))
    out2=[]
    for o in out:
        out2.append(to_str(merc2latlon(o,zoom)))
    return out2
    
def create_seg_sequence(prevpos,center,nextpos,dist_nm,direction):
    zoom=14
    prevmerc=latlon2merc(from_str(prevpos),zoom)
    centermerc=latlon2merc(from_str(center),zoom)
    nextmerc=latlon2merc(from_str(nextpos),zoom)
    
    d1=minus(prevmerc,centermerc)
    d2=minus(nextmerc,centermerc)
    a1=math.atan2(d1[1],d1[0])
    a2=math.atan2(d2[1],d2[0])
    
    radius_pixels=approx_scale(centermerc,zoom,dist_nm)
    
    #if a2<a1:
    #    a2+=math.pi*2
    if abs(a2-a1)<1e-6:
        return []
    steps=abs(a2-a1)/(math.pi*2.0)*dist_nm*math.pi*2/5.0
    if steps<16:
        steps=16
    out=[]
    angles=list(seg_angles(a1,a2,abs(a2-a1)/steps,direction=direction))
    for cnt,a in enumerate(angles):
        if cnt!=0 and cnt!=len(angles)-1:
            x=math.cos(a)*radius_pixels
            y=math.sin(a)*radius_pixels
            out.append(plus((x,y),centermerc))
    out2=[]
    for o in out:
        out2.append(to_str(merc2latlon(o,zoom)))
    return out2
def uprint(*ss):
    out=[]
    for s in ss:
        if type(s)==unicode:
            out.append(s.encode('utf8'))
        elif type(s)==str:
            out.append(s)
        else:
            out.append(repr(s))
    print " ".join(out)
def parse_dist(s):
    #uprint("In:%s"%s)
    val,nautical,meters=re.match(r"\s*([\d.]+)\s*(?:(NM)|(m))\b\s*",s).groups()
    dval=float(val)
    assert nautical!=None or meters!=None
    if meters:
        dval=dval/1852.0
    return dval


def parse_area_segment(seg,prev,next):
    #uprint("Parsing <%s>"%(seg,))
    for borderspec in [
        "Swedish/Danish border northward to (.*)",
        "Swedish/Norwegian border northward to (.*)"
        ]:
        border=re.match(borderspec,seg)
        if border:
            
            if prev.strip()=="671311N 0162302E":
                return [parsecoord(x) for x in "671627N 0161903E - 673139N 0161704E - 673201N 0162439E - 673900N 0163343E".split(" - ")]            
            okprev=set(["560158N 0123925E","682121N 0195516E"])
            if not prev.strip() in okprev:
                uprint(prev)
                raise Exception("Border spec not supported fully yet: %s"%(borderspec,))            
            lat,lon=border.groups()[0].strip().split(" ")
            return [parsecoord(border.groups()[0])]
    arc=re.match(r"\s*clockwise along an arc cent[red]{1,5} on (.*) and with radius (.*)",seg)
    if arc:
        centerstr,radius=arc.groups()
        prevposraw=None
        nextposraw=None
        direction="cw"
    if not arc:
        arc=re.match(ur"\s*(\d+N\s*\d+E)?.*?(\bcounterclockwise|\bclockwise) along an? (?:circle|arc)\s*.?\s*(?:with)?\s*(?:säde)?\s*/?\s*radius\s*(\d+\.?\d*? NM)\s*,?\s*(?:keskipiste /)?\s*cent[red]{1,5}\s*on\s*(\d+N\s*\d+E)(?:[^\d]*|(?:.*to the point\s*(\d+N\s*\d+E)))$",seg)
        #arc=re.match(ur".*?((?:counter)?clockwise) along.*?(circle|arc).*?radius\s*(\d+\.?\d*? NM).*?cent.*?on\s*(\d+N \d+E).*(to the point\s*\d+N \d+E)?.*",seg)
        #if arc:
        #    print "midArc:",arc,arc.groups()
        #else:
        #    print "Noarc"
        if arc:
            #print "match: <%s>"%(arc.group(),)
            #directionraw,circarc,
            prevposraw,directionraw,radius,centerstr,nextposraw=arc.groups()
            #if nextposraw:
            #    nextposraw=re.match(ur"to the point\s*(\d+N\s*\d+E).*",nextposraw)
                
            #print "rad,cent", radius,centerstr
            if directionraw=="clockwise":
                direction="cw"
            elif directionraw=="counterclockwise":
                direction="ccw"
            else:
                raise Exception("Unknown direction")
            
    if arc:
        #uprint("Parsing coord: %s"%centerstr)
        #uprint("Direction: %s"%(direction,))
        center=parsecoord(centerstr)
        dist_nm=parse_dist(radius)
        #uprint("prev: <%s>, next: <%s>"%(prev,next))
        if prevposraw==None:
            prevposlatlon=re.match(ur".*?(\d+N)\s*(\d+E)\s*",prev).groups()        
            prevpos=parse_coords(*prevposlatlon)
            prevposraw=prev
        else:
            prevposlatlon=prevposraw.split(" ")
            prevpos=parsecoord(prevposraw)
        if nextposraw==None:
            nextposlatlon=re.match(ur"\s*(\d+N)\s*(\d+E).*",next).groups()
            nextpos=parse_coords(*nextposlatlon)
            nextposraw=next
        else:
            nextposlatlon=nextposraw.split(" ")
            nextpos=parsecoord(nextposraw)
        #uprint(u"Emitting arc from <%s> to <%s> with center <%s> and radius <%s> direction <%s>"%(
        #    prevposlatlon,nextposlatlon,centerstr,radius,direction))
        #uprint("Arc center: %s"%(center,))
        #uprint("Seg params: %s %s %s %s"%(prevpos,center,dist_nm,nextpos))
        segseq=create_seg_sequence(prevpos,center,nextpos,dist_nm,direction=direction)
        return segseq
    circ=re.match( ur".*A circle,?\s*(?:with)? radius ([\d\.]+\s*(?:NM|m))\s*(?:\(.*[kK]?[mM]\))?\s*,?\s*cent[red]{1,5}\s*on\s*(\d+N)\s*(\d+E).*",seg)
    if circ:
        radius,lat,lon=circ.groups()
        assert prev==None and next==None        
        #uprint("Parsed circle:%s : %s"%(circ,circ.groups()))
        dist_nm=parse_dist(radius)
        zoom=14
        center=parse_coords(lat,lon)
        return create_circle(center,dist_nm)

    try:
        assert seg.count(" ")%2==1
        segs=seg.split(" ")
        assert len(segs)%2==0
        c=[]
        for i in xrange(len(segs)/2):
            p=" ".join(segs[2*i:2*i+2])
            #print "P:",p
            c.append(parsecoord(p))
        #c=parsecoord(seg)
        return c
    except MapperBadFormat:
        uprint("Couldn't parse <%s> as a plain coord"%(seg,))
        #raise
        pass #continue processing

    uprint("Unparsed area segment: %s"%(seg,))
    return []

def parse_coord_str(s):
    #borderspecs=[
    #    ]
    #uprint("Pre?")
    #uprint("Parsing area: %s"%(s,))
    #uprint("Twice?")
    s=s.replace(u"–","-")
    s=s.replace(u"counter-clock","counterclock")
    s=s.replace(u"clock-wise","clockwise")
    itemstemp=s.strip().split("-")
    items=[]
    for item in itemstemp:
        if re.match(ur"-?pisteeseen\s*/\s*to the point",item.strip()): continue
        #item=item.replace(u"-pisteeseen /  to the point","-")
        items.append(item)
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
        
        #for spec in borderspecs:
        #    if pstr.count(spec):
        #        pstr=pstr.replace(spec,"")
        #        break                
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
    if elev.lower().endswith("ft msl"): elev=elev[:-6].strip()
    if elev.lower().endswith("ft amsl"): elev=elev[:-6].strip()
    if elev.lower().endswith("ft gnd"): elev=elev[:-6].strip()
    if elev.lower().endswith("ft sfc"): elev=elev[:-6].strip()
    if elev.lower()=="unl": return 99999
    if elev.lower()=="sfc": return 0 #TODO: Lookup using elevation map
    if elev.lower()=="gnd": return 0 #TODO:We should lookup GND height using an elevation map!!
    elev=elev.replace(" ","")
    if not elev.isdigit():
        raise NotAnAltitude(repr(elev))    
    return int(elev)
    
