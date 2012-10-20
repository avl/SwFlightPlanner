#encoding=utf8
from pyproj import Proj,transform
import shapefile
from copy import copy
from fplan.lib import mapper
def no_obstacles(*fnames):
    out=[]
    for fname in fnames:
        r=shapefile.Reader(fname)
        utm = Proj(proj='utm',zone=33,ellps='WGS84')
        wgs84 = Proj(init='epsg:4326')
    
        untrans=set()
        osts={unicode('Vindm\xef\xbf\xbdlle','utf8'):'Wind turbine',
              u'T\ufffdrn':'Tower',
              u'Mast TELE':'Mast',
              u'Annet':'Antenna',    
            u'Heisekran':'Crane',
            u'Tank':'Tank',
            u'Fyr':'Lighthouse',
            u'Bru':'Bridge',
            u'Mast EL':'Mast',
            u'Pipe':'Chimney',
            u'Oljeinstallasjon':'Oil Platform',
            u'Mast/stolpe veilys':'Mast',
            u'Bygning':'Building',
            u'Hoppbakke':'Ski-jump',
            u'Silo':'Silo',
            u'Skiheis':'Ski lift',
            u'Kraftlinespenn':'Power lines', 
           u'LuftledningLH':'Power lines', 
           u'Gondolheis':'Ski lift', 
           u'Taubane':'Aerial tramway', 
           u'L\ufffdypestreng':'Power lines'
            }
        """
    "Wind turbine",
    "Mast",
    "Cathedral",
    "Pylon",
    "Building",
    "Platform",
    "Chimney",
    "Mine hoist",
    "Bridge pylon",
    "Crane",
    "W Tower",
    "Church",
    "Silo",
    "City Hall",
    "Gasometer",
    "Tower",
    "Bridge pylon, 60 per minute"]
    """
        columns=[x[0] for x in r.fields]

        for rec in r.shapeRecords():
            #print "col:",columns
            #print "rec:",rec.record
            d=dict(zip(columns[1:],rec.record))
            def fixname(n):
                n=n.strip()
                if n=="":
                    n="Unknown"
                return n
            nortype=unicode(d['hindertype'],'utf8')
            engtype=osts.get(nortype,nortype)
            if not nortype in osts:
                untrans.add(nortype)
            base=dict(
                      name=fixname(unicode(d['lfh_navn'],'utf8')),
                      height=d['hoeydeover'],
                      elev=d['totalhoeyd'],
                      lighting=unicode(d['lyssetting'],'utf8'),
                      kind=engtype)
            if base['height']<400*0.3048:
                continue
            for point in rec.shape.points:
                x,y=point
                lat,lon=transform(utm,wgs84,x,y)
                #print "Input: ",d,x,y,"output:",lat,lon
                cur=copy(base)
                cur['pos']=mapper.to_str((lat,lon))
                out.append(cur)
            #break
        print "missing translations",untrans
    return out
if __name__=='__main__':
    for x in no_obstacles(
        "/home/anders/saker/avl_fplan_world/norway_obst/20120903pkt.shp",
        "/home/anders/saker/avl_fplan_world/norway_obst/20120903linpkt.shp",
        "/home/anders/saker/avl_fplan_world/norway_obst/20120903lin.shp",
        ):
        print x
        