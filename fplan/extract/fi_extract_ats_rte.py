#encoding=utf8
import parse
from parse import Item
import re
import sys
import fplan.lib.mapper as mapper
from fplan.lib.mapper import uprint
import md5
import math

predef={
#('L24','c3d07b60f586fb24ad054ac98050225e') : 
#    ( 10, 'FL 65','FL 95','602733N 0241439E 602652N 0240237E 602617N 0235235E 602849N 0233644E 602942N 0230554E 603055N 0221523E'),
#TODO: Update L24, it has in fact changed

("L24","0679ab4cea290636ac02b4ec4d3035d8") : ( 10,"FL 65","FL 95","602733N 0241439E 602652N 0240237E 602617N 0235235E 602849N 0233644E 602942N 0230554E 603055N 0221523E"),

('L80',"3705096c45c33f6b85df0f1fc063e445") :
    ( 10, 'FL 65','FL 95','612436N 0233440E 612558N 0225520E 612659N 0222145E 612753N 0214745E'),
('N198','866aaf523c7d17679852ead9dc4fb7d0') :
    ( 10,'FL 65','FL 95',"""MARIE
    VOR/DME (MAR)
    600828N 0195452E
    DELAP
    601449N 0203250E
    GIMUL
    602256N 0212320E
    RUSKO
    VOR/DME (RUS)
    603055N 0221523E
    ALIBA
    604623N 0223740E
    INKIS
    605615N 0225207E
    TURUX
    610917N 0231128E
    PIRKKA
    VOR/DME (PIR)
    612436N 0233440E"""),

('N609','7c3cc8a33caec8d434f1e4b3987cabeb') :
    ( 10, 'FL 65','FL 95',"""
    PREVIK
    VOR/DME (PRI)
    612753N 0214745E
    TUSKU
    610729N 0215751E
    NIRPU
    604627N 0220801E
    RUSKO
    VOR/DME (RUS)
    603055N 0221523E"""),
("P854","de13b5724612b6ae4e72fd94c17b5e4c") : ( 10,"FL 65","FL 95","""
    612436N 0233440E
    VELUN
    610656N 0235800E
    PEMOS
    605501N 0241327E
    PIVAK
    604402N 0242729E
    HELSINKI
    VOR/DME (HEL)
    602016N 0245713E
    """),
 ("P739","6575745343ce3e57abd06f483102ec85") : ( 10,"FL 65","FL 95","""
    594758N 0242709E
    601740N 0253519E
    """),
("Q1","235a20cfc4f969979fb9298d1b7a153d") : ( 10,"FL 65","FL 95","""
    602016N 0245713E
    ARTUR
    602048N 0240350E
    MEDOT
    602626N 0230532E
    RUSKO
    VOR/DME (RUS)
    603055N 0221523E    
    """),
("T89","2a9d2c3353fa9b4bdb037eec099d860e") : ( 10,"FL 65","FL 95","""
    645554N 0252133E
    AKOVU
    643912N 0244811E
    NOSLO
    641625N 0240405E
    OKAMO
    640032N 0233419E
    KRUUNU
    L
    (KRU)
    634730N 0231026E
    VEXAT
    632915N 0223527E
    OMELU
    631750N 0221403E
    VAASA
    VOR/DME
    (VAS)
    630229N 0214554E
    """),
("T91","6a478222e0d15c5631afd4e9087a4c70") : ( 10,"FL 65","FL 95","""
    612753N 0214745E
NIPAN
610902N 0220727E
ATRIV
605700N 0221948E
TURSU
604838N 0225330E
>FL 95: C
FL 95 - FL 65: D
GUPSA
603739N 0233624E
INKOL
602956N 0240546E
602733N 0241439E
    """),
("T95","5969a77bba6e4b5e98171657cc265be5") : ( 10,"FL 65","FL 95","""
        PIRKKA
    VOR/DME
    (PIR)
    612436N 0233440E
    VALOX
    610651N 0233520E
    ENOKI
    604936N 0233558E
    GUPSA
    603739N 0233624E
    AMEDU
    602849N 0233644E

    """),
("Y86","de353fd0368eb7e9385fb63b4a0e98f6") : ( 10,"FL 65","FL 95","""
    PIRKKA
    VOR/DME (PIR)
    612436N 0233440E
    VALOX
    610651N 0233520E
    ENOKI
    604936N 0233558E
    GUPSA
    603739N 0233624E
    AMEDU
    602849N 0233644E    
    """),
("Z210","fbcefbeef58e41802adbd08c9aabac1c") : ( 10,"FL 65","FL 95","""
    TINOS FIR BDRY
    694730N 0261340E
    VADLA FIR BDRY
    694506N 0284743E
    """),    
}


def rotL(p):
    x,y=p
    return (-y,x)
def rotR(p):
    x,y=p
    return (y,-x)
def add(a,b):
    return (a[0]+b[0],a[1]+b[1])    
def sub(a,b):
    return (a[0]-b[0],a[1]-b[1])    
def scalar(a,b):
    return a[0]*b[0]+a[1]*b[1]
def mul(k,a):
    return (k*a[0],k*a[1])
def norm(a):
    return math.sqrt(a[0]**2+a[1]**2)    
def normalize(a):
    dlen=norm(a)
    if abs(dlen)<1e-6: raise Exception("Attempt to normalize zero-vector")
    return mul(1.0/dlen,a)


def get_outline(coords,width):
    left=[]
    right=[]
    uprint("Coords:\n<%s>\n, width: <%s>"%(coords,width))
    for idx in xrange(len(coords)):
        here=coords[idx]
        mid=True
        if idx==0:
            prev=coords[idx]
            mid=False
        else:
            prev=coords[idx-1]
        if idx==len(coords)-1:
            next=coords[idx]
            mid=False
        else:
            next=coords[idx+1]
        d=(float(next[0]-prev[0]),float(next[1]-prev[1]))
        enwiden=1.0
        if mid:
            d1=normalize(sub(here,prev))
            d2=normalize(sub(next,here))
            s=scalar(d1,d2)
            if s<=-1.0: s=-1.0
            if s>=1.0: s=1.0
            a=math.acos(s)
            if abs(a)>60.0/(180.0/math.pi): 
                raise Exception("ATS route turns too sharply, at index: %d"%(idx,))
            enwiden=1.0/math.cos(a)
        width*=enwiden
        d=normalize(d)
        left.append(add(here,mul(0.5*width,rotL(d))))
        right.append(add(here,mul(0.5*width,rotR(d))))
    return right+list(reversed(left))
        
def fi_parse_ats_rte():
    p=parse.Parser("/ais/eaip/pdf/enr/EF_ENR_3_3_EN.pdf",lambda x: x,country='fi')
    out=[]
    for pagenr in xrange(p.get_num_pages()):        
        page=p.parse_page_to_items(pagenr)
        
        def isol_routes():
            cur=None
            accum=[]
            for line in page.get_lines(page.get_all_items()):
                uprint("Looking at ",line)
                m=re.match(ur"(^[A-Z]{1,2}\d+)\s+\(.*",line)
                if m and line.x1<25:
                    if cur:
                        uprint("Yielding %s: %s because of found name:%s"%(cur,accum,m.groups()))
                        yield cur,accum
                        accum=[]
                    cur,=m.groups()
                    continue
                m=re.match(ur"(\d{6}N)\s*(\d{7}E).*",line)
                if m:
                    accum.append((line.y1,line.y2," ".join(m.groups())))
            if cur:
                uprint("Yielding %s: %s because of end of page"%(cur,accum))
                yield cur,accum
                accum=[]
        def getsig(coords,altspecs):
            poss=[]
            #print "Coords: <%s>"%(coords,)
            for y1,y2,pos in coords:
                poss.append(pos)
            uprint("poss: <%s>"%(poss,))
            s="-".join(poss)
            s2="-".join(altspecs)
            return md5.md5(s.encode('utf8')+s2.encode('utf8')).hexdigest()
        def low_routes(routes):
            for routename,coords in routes:
                uprint("Found route: %s, with %s cords"%(routename,coords))
                assert len(coords)>=2
                y1=coords[0][0]
                y2=coords[-1][1]
                foundlow=False
                altspec=[]
                for item in page.get_partially_in_rect(0,y1,100,y2):
                    uprint("Looking for alt for %s in :"%(routename,),item.text)
                    m=re.match(ur".*FL\s+(\d{2,3})\b(?:\s.*|$)",item.text)
                    if m:
                        fl,=m.groups()
                        uprint("Matched alt:",m.groups())
                        fli=int(fl,10)
                        if fli<95:
                            uprint("Foundlow for route %s: %d"%(routename,fli))
                            foundlow=True
                    altspec.append(item.text)
                if foundlow: 
                    yield routename,coords,altspec

        
        def get_airspaces(routes):
            for routename,coords,altspec in routes:
                sig=getsig(coords,altspec)
                if 1 or (routename,sig) in predef:
                    pobj=None
                    for sroutename,ssig in predef:
                        if routename==sroutename:
                            pobj=(sroutename,ssig)
                    width_nm,floor,ceiling,coordstr=predef[pobj]
                    rawcoords=re.findall(ur"(\d{6}N)\s*(\d{7}E)",coordstr)
                    coords=[mapper.latlon2merc(mapper.from_str(mapper.parse_coords(lats,lons)),13) for lats,lons in rawcoords]
                    width=float(mapper.approx_scale(coords[0],13,1.25*width_nm))
                    try:
                        outline=get_outline(coords,width)
                    except:
                        uprint(u"Trouble parsing %s"%(routename,))
                        raise
                    yield dict(name=routename,
                        floor=floor,
                        ceiling=ceiling,
                        freqs=[],
                        type="RNAV",
                        points=[mapper.to_str(mapper.merc2latlon(x,13)) for x in outline])
                else:
                    uprint("Need to have predefine for route %s, with md5: %s"%(routename,sig))
                    uprint("Altitude, and points")
                    raise Exception('Missing predef for route. Use: ("%s","%s") : ( 10,"FL 65","FL 95","""\n\n    """),'%(routename,sig))
        i1=isol_routes()
        low1=low_routes(i1)
        out.extend(list(get_airspaces(low1)))
    return out
                    


if __name__=='__main__':
    for space in fi_parse_ats_rte():
        uprint(space)
        

