from elementtree.ElementTree import fromstring


def parse_gpx(gpxcontents):                
    xml=fromstring(gpxcontents)
    out=[]
    for track in xml.findall("*//{http://www.topografix.com/GPX/1/1}trkpt"):
        lat=float(track.attrib['lat'].strip())
        lon=float(track.attrib['lon'].strip())
        out.append((lat,lon))
    return out

