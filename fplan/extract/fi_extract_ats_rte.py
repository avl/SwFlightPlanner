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
("L24","0679ab4cea290636ac02b4ec4d3035d8") : ( 10,"FL 65","FL 95","""VIBEP
602733N 0241439E
R MAROM
602652N 0240237E
R LAKUT
602617N 0235235E
R AMEDU
602849N 0233644E
R SITMU
602942N 0230554E
R RUSOX
603055N 0221523E
"""),
("L80","3705096c45c33f6b85df0f1fc063e445") : ( 10,"FL 65","FL 95","""
    PIVOR
612436N 0233440E
R GIMIS
612558N 0225520E
18.9
FL 285
PERM
H24
FL 65
16.2
R PEKUS
612659N 0222145E
16.3
R ERKES
612753N 0214745E
    """),

("N198","866aaf523c7d17679852ead9dc4fb7d0") : ( 10,"FL 65","FL 95","""
UXETI
600828N 0195452E
R DELAP
601449N 0203250E
R GIMUL
602256N 0212320E
R RUSOX
603055N 0221523E
R ALIBA
604623N 0223740E
R INKIS
605615N 0225207E
R TURUX
610917N 0231128E
PERM
H24
20.0
R PIVOR
612436N 0233440E

    """),

("N609","7ea769e12b5acfef69e91eb746075a16") : ( 10,"FL 65","FL 95","""
ERKES
612753N 0214745E
R TUSKU
610729N 0215751E
FL 95
48.7
FL 100
19.2
21.0
C
FL 285
FL 65
21.7
R NIRPU
604627N 0220801E
16.0
R RUSOX
603055N 0221523E

    """),

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
("P739","e592bf8dbca98fa5849590baf42b375c") : ( 10,"FL 65","FL 95","""
DOBAN FIR BDRY
594758N 0242709E
FL 285
PERM
H24
ATS-reitin jatko, ks. Viron AIP.
For continuation, see AIP Estonia.
FL 65
45.3
10
FL 70
C
R ELPIR
601740N 0253519E

    """),

("P854","38e067efd6355944dd8db788f440ef64") : ( 10,"FL 65","FL 95","""
PIVOR
612436N 0233440E
R VELUN
610656N 0235800E
R PEMOS
605501N 0241327E
R PIVAK
604402N 0242729E
PERM
H24
11.2
R ODEXA
602016N 0245713E

    """),

("Q1","5a497170c51cdd6015a4c99cf8c5df5e") : ( 10,"FL 65","FL 95","""
ODEXA
602016N 0245713E
26.5
R ARTUR
602048N 0240350E
FL 65
29.5
R MEDOT
602626N 0230532E
FL 285
FL 70
25.2
R RUSOX
603055N 0221523E

    """),
("T89","e969eeda855120842ec4280ce05a7df9") : ( 10,"FL 65","FL 95","""
OGVOR
645554N 0252133E
R AKOVU
643912N 0244811E
R NOSLO
641625N 0240405E
R OKAMO
640032N 0233419E
R KURAX
634730N 0231026E
R VEXAT
632915N 0223527E
R OMELU
631750N 0221403E
R VAVOS
630229N 0214554E

    """),
("T91","cfe3289634704900c2313d961c09e4ae") : ( 10,"FL 65","FL 95","""
ERKES
612753N 0214745E
R NIPAN
610902N 0220727E
R ATRIV
605700N 0221948E
R TURSU
604838N 0225330E
R GUPSA
603739N 0233624E
R INKOL
602956N 0240546E
>FL 95: C
FL 95 - FL 65: D
5.0
R VIBEP
602733N 0241439E

    """),
("T95","e68c77af136c319ba00c57616e2ee4e6") : ( 10,"FL 65","FL 95","""
PIVOR
612436N 0233440E
R VALOX
610651N 0233520E
R ENOKI
604936N 0233558E
R GUPSA
603739N 0233624E
FL 95 - FL 65: D
R AMEDU
602849N 0233644E

    """),
("Y86","326d8c40c74912fca21f0e5866277d07") : ( 10,"FL 65","FL 95","""
PIVOR
612436N 0233440E
17.8
FL 285
R VALOX
610651N 0233520E
FL 65
17.3
THIS PAGE INTENTIONALLY LEFT BLANK
10
FL 70
R ENOKI
604936N 0233558E
12.0
R GUPSA
603739N 0233624E
>FL 95: C
FL 95 - FL 65: D
8.9
R AMEDU
602849N 0233644E
    """),
("Z210","dea085535cbeb1c68a6809cbb34bf414") : ( 10,"FL 65","FL 95","""
TINOS FIR BDRY
694730N 0261340E
FL 285
PERM
H24
FL 65
53.6
R VADLA FIR BDRY
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
                if (routename,sig) in predef:
                    #pobj=None
                    #for sroutename,ssig in predef:
                    #    if routename==sroutename:
                    pobj=(routename,sig)
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
        

