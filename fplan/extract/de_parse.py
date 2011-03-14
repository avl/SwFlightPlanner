import re
import fplan.lib.mapper as mapper


def parse_airspace():
    lines=[unicode(x,'latin1') for x in list(open("fplan/extract/denmark.airspace")) if 
           not x.startswith("#") and
           not x.startswith("FIR boundary")           
           ]
    return parse_space(lines)

def parse_space(lines):    
    idx=[0]
    out=[]
    translate=dict(
        ATS='TMA',
        TIA='TMA',
        TIZ='CTR',
        TMA='TMA',
        CTR='CTR'
        )
    try:
        def getline():
            if idx[0]==len(lines):
                raise StopIteration()
            r=lines[idx[0]]
            idx[0]+=1
            return r
        def peek():
            if idx[0]==len(lines):
                raise StopIteration()
            r=lines[idx[0]]
            return r
        def get(what):
            splat=getline().split("=")
            if len(splat)!=2:
                raise Exception("Expected <%s=?>, got <%s>"%(what,splat))
            key,val=splat
            if key!=what:
                raise Exception("Expected <%s>, got <%s>"%(what,splat))
            assert key==what
            return val.strip()
        def isnext(what):
            line=peek()
            if line.startswith(what):
                return True
            return False
        while True:
            TYPE=get("TYPE")
            SUBTYPE=get("SUBTYPE")
            CLASS=get("CLASS")
            RADIO=get("RADIO")
            notes=[]
            while isnext("NOTES"):
                notes.append(get("NOTES"))
            TITLE=get("TITLE")
            BASE=get("BASE")
            TOPS=get("TOPS")            
            freqs=[]
            for radio in [RADIO]+notes:
                name,freq=re.match("(.*?)\s*(\d{3}\.\d{3}\s*(?:and)?)+",radio).groups()
                fr=re.findall(ur"\d{3}\.\d{3}",freq)
                for f in fr:
                    if float(f)<200.0:
                        freqs.append((name,float(f)))
            print freqs
            points=[]
            area=[]
            while True:
                if isnext("POINT"):
                    p=get("POINT")
                    area.append(p)
                    continue
                if isnext('CLOCKWISE'):
                    radius,center,dest=re.match(ur"CLOCKWISE RADIUS=(\d+\.?\d*) CENTRE=(\d+N \d+E) TO=(\d+N \d+E)",getline()).groups()
                    area.append(ur"clockwise) along an arc with radius %s centred on %s to the point %s"%(radius,center,dest))
                    continue
                if isnext('CIRCLE'):
                    l=getline()
                    radius,center=re.match(ur"CIRCLE RADIUS=(\d+\.?\d*) CENTRE=(\d+\.?\d*N \d+\.?\d*E)",l).groups()
                    area.append("A circle with radius %s NM centred on %s"%(radius,center))
                break
            points=mapper.parse_coord_str(" - ".join(area))
            
            type_=translate[SUBTYPE]
            def elev(x):
                if x=="SFC": return "GND"
                if x.lower().startswith("fl"):
                    assert x[2:].isdigit()
                    return "FL%03d"%(int(x[2:]))
                assert x.isdigit()
                return "%d ft MSL"%(int(x),)
            out.append(
                dict(
                     name=" ".join([TITLE.strip(),SUBTYPE])+" [2010]",
                     floor=elev(BASE),
                     ceiling=elev(TOPS),
                     freqs=freqs,
                     points=points,
                     type=type_
                     ))            
    except StopIteration:
        pass
    else:
        raise Exception("Unexpected erorr")
    return out

def parse_airfields():
    return []
def parse_denmark():
    
    airspace=parse_airspace()
    airfields=parse_airfields()
    print "Spaces:"
    for sp in airspace:
        print "Name:",sp['name']
        print "  Points:",sp['points']
        print "  Floor:",sp['floor']
        print "  Ceil:",sp['ceiling']
        print "  Freqs:",sp['freqs']
        
    
    return dict(
        airspace=airspace,
        airfields=airfields)
if __name__=='__main__':
    parse_denmark()
    