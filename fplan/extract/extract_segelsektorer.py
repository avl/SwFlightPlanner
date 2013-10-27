from fetchdata import getdata
import fplan.lib.mapper as mapper

def getareas(lines,date):
    name=None
    coords=[]
    ceiling=None
    floor=None
    vars=dict()
    def emit():
        if name==None:
            raise Exception("Area is missing name")
        if ceiling==None or floor==None:
            raise Exception("Area is missing floor or ceiling")
        cd=" - ".join(coords)
        
        ret=dict(
            floor=floor,
            ceiling=ceiling,
            freqs=[],
            type="segel",
            name=name+" glider sector",
            points=mapper.parse_coord_str(cd))
        return ret
    def haveany():
        return name!=None
    def parse_name(line):
        AN,name=line.split(" ",1)
        name=unicode(name,"iso-8859-15")
        assert AN=="AN"
        return name.strip()
    def parse_alt(line):
        A,alt=line.split(" ",1)
        assert A in ("AL","AH")
        alt=alt.strip()
        if alt=="":
            return "UNL"
        mapper.parse_elev(alt)
        return alt
    def parse_coord(line):
        C,coord=line.split(" ",1)
        assert C=="DP"
        coords.append(parse_rawcoord(coord))
    def parse_rawcoord(coord):        
        lat,N,lon,E=coord.strip().split(" ")
        lat=lat.replace(":","")
        lon=lon.replace(":","")
        return lat+N+" "+lon+E
    def parse_var(line):
        v,rest=line.split(" ",1)
        assert v=="V"
        if rest.startswith("X="):
            vars["center"]=parse_rawcoord(rest[2:])
            return
        raise Exception("Unknown variable")
    def parse_arc(line):
        db,rest=line.split(" ",1)
        assert db=="DB"
        c1,c2=rest.split(",")
        temp=[]
        temp.append(parse_rawcoord(c1))
        end=parse_rawcoord(c2)
        assert vars['center']
        
        bearing,radius=mapper.bearing_and_distance(mapper.parsecoord(vars['center']), mapper.parsecoord(end))
        temp.append("clockwise along an arc with radius %s NM centred on %s to the point %s"%((radius),vars['center'],end))
        #temp.append(end)
        coords.append(" ".join(temp))
    def parse_circle(line):
        c,rest=line.split(" ",1)
        assert c=='DC'
        radius=float(rest.strip())
        coords.append("A CIRCLE WITH RADIUS OF %sNM CENTERED ON %s"%(radius,vars['center']))
        
    lines=lines.replace("\r\n","\n")
    for line in lines.split("\n"):
        
        if line.startswith("*"):
            if haveany():
                yield emit()
                coords=[]
                floor=None
                ceiling=None
                name=None
            continue
        if line.startswith("AN"):
            name=parse_name(line)
        elif line.startswith("AL"):
            floor=parse_alt(line)
        elif line.startswith("AH"):
            ceiling=parse_alt(line)
        elif line.startswith("V"):
            parse_var(line)
        elif line.startswith("DP"):
            parse_coord(line)
        elif line.startswith("DB"):
            parse_arc(line)
        elif line.startswith("AC"): 
            continue  #ignore
        elif line.startswith("DC"):
            parse_circle(line)
        elif line.strip()=="":
            continue
        else:
            raise Exception("Unparsable line: "+line)
    if haveany():
        yield emit()
            
def extract_segel():
    segeldata,stamp=getdata("/ImageVaultFiles/id_21795/cf_78/Sektorer-2013-CU-rev1.TXT","segel")
    return list(getareas(segeldata,stamp))
    
    
if __name__=='__main__':
    for area in extract_segel():
        print area
    
    
