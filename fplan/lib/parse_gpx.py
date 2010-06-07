from elementtree.ElementTree import fromstring
import re
from datetime import datetime
class Track():pass
def parse_gpx(gpxcontents,startstr,endstr):
    start=None
    end=None
    try:
        start=datetime.strptime(startstr,"%Y-%m-%d %H:%M:%S")
        end=datetime.strptime(endstr,"%Y-%m-%d %H:%M:%S")
    except Exception,cause:
        print "Problem parsing gpx daterange: ",cause
        end=None
        start=None
        
    print "GPX Range: ",start,end
    xml=fromstring(gpxcontents)
    out=[]
    lastlat=None
    lastlon=None
    threshold=0.25*1.0/60.0
    minlat=1e30
    minlon=1e30
    maxlat=-1e30
    maxlon=-1e30
    out=Track()
    out.points=[]
    for track in xml.findall("*//{http://www.topografix.com/GPX/1/1}trkpt"):
        lat=float(track.attrib['lat'].strip())
        lon=float(track.attrib['lon'].strip())
        tim=track.find("{http://www.topografix.com/GPX/1/1}time").text.strip()
        ele=float(track.find("{http://www.topografix.com/GPX/1/1}ele").text.strip())
        Y,M,D,h,m,s=re.match("(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):([\.\d]+)Z",tim.strip()).groups()
        micros=int((1e6)*(float(s)%1.0))
        s=int(float(s))
        dtim=datetime(int(Y),int(M),int(D),int(h),int(m),int(s),int(micros))
        print "Parsed %s as %s"%(tim,dtim)
        
        if start and end and (dtim<start or dtim>end): continue

        if lastlat!=None and lastlon!=None:            
            d=(lastlat-lat)**2+(lastlon-lon)**2
        else:
            d=2*threshold
        if d>threshold**2:            
            out.points.append(((lat,lon),int(ele)))
            lastlon=lon
            lastlat=lat
            if lat<minlat: minlat=lat
            if lon<minlon: minlon=lon
            if lat>maxlat: maxlat=lat
            if lon>maxlon: maxlon=lon
    out.bb1=(maxlat,minlon)
    out.bb2=(minlat,maxlon)
    return out

