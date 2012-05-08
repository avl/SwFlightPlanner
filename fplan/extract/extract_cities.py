

from fplan.lib.maptilereader import latlon_limits,latlon_limits_hd
        

def get_cities():
    points=[]
    
    for line in open("fplan/extract/cities.csv"):
        line=unicode(line,'utf8')
        #print repr(line)
        lon,lat,kind,name=line.strip().split(",",3)
        name=name.replace('"',"")
        lon=float(lon)
        lat=float(lat)
        lat1,lon1,lat2,lon2=latlon_limits()
        if kind!='city':
            if lat<lat1 or lat>lat2 or lon<lon1 or lon>lon2:
                continue #only take cities from outside the high-def area        
        assert kind in ['city','town']   
        points.append(dict(
            name=name,
            kind=kind,
            pos="%f,%f"%(float(lat),float(lon))))                
    return points

if __name__=='__main__':
    cs=get_cities()
    print "Got %d cities and towns"%(len(cs),)
    
