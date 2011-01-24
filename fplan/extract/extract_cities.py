


def get_cities():
    points=[]
    for line in open("fplan/extract/cities.csv"):
        line=unicode(line,'utf8')
        lon,lat,kind,name=line.strip().split(",")
        assert kind in ['city','town']   
        points.append(dict(
            name=name,
            kind=kind,
            pos="%f,%f"%(float(lat),float(lon))))                
    return points

if __name__=='__main__':
    get_cities()
    