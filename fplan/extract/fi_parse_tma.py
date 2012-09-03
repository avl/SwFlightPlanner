#!/usr/bin/python
#encoding=utf8
import parse
from parse import Item
import re
import fplan.lib.mapper as mapper
import sys,os
import math
from datetime import datetime
from fplan.lib.mapper import parse_coord_str,uprint
from pyshapemerge2d import Polygon,Vertex,vvector
import ats_routes
import pyshapemerge2d as shapemerge2d
import fplan.lib.makepoly as makepoly
"""i
class Item(object):
    def __init__(self,text,x1,y1,x2,y2):
        self.text=text
        self.x1=x1
        self.y1=y1
        self.x2=x2
        self.y2=y2
    def __repr__(self):
        return "Item(%.1f,%.1f - %.1f,%.1f : %s)"%(self.x1,self.y1,self.x2,self.y2,repr(self.text))

    
def parse_page_to_items(parser,page):
    items=[Item(text=unicode(item.text),
          x1=float(item.attrib['left']),
          x2=float(item.attrib['left'])+float(item.attrib['width']),
          y1=float(item.attrib['top']),
          y2=float(item.attrib['top'])+float(item.attrib['height'])
          ) for item in page.findall("text")]
    return items
"""

def is_r_or_danger_area_name(name):
    #uprint("Is danger/R: %s"%(name,))
    if re.match("ES\s+[DR]\d+[A-Za-z]?",name):
        #uprint("Yes!")
        return True
    #uprint("No!")
    return False

def filter_head_foot(xs):
    out=[]
    for x in xs:
        st=x.strip()
        if st.startswith("AMDT"):continue
        if st.startswith("The LFV Group"): continue            
        out.append(x)
    return out


def parse_page(parser,pagenr):   
    page=parser.parse_page_to_items(pagenr)
    items=page.items
    minx=min([item.x1 for item in items])
    headings=[]
    majorre=ur"\s*([A-ZÅÄÖ ][A-ZÅÄÖ]{3,})\s+(?:TMA|MIL CTA)\s*(?:-.*)?$"
    minorre=ur"\s*(?:TMA|MIL CTA [SN]?)\s*[A-ZÅÄÖ ]*\s*"
    airwayre=ur"(AWY\s+EF\s+[-A-Z]+)"
    delegre=ur".*(Delegation\s+of\s+responsibility).*"
    for item in page.get_by_regex(majorre):
        m,=re.match(majorre,item.text).groups()
        assert m!=None
        assert m.strip()!=""
        headings.append(('major',item.text.strip(),m,item))
    for item in page.get_by_regex(airwayre):
        m,=re.match(airwayre,item.text).groups()
        assert m!=None
        assert m.strip()!=""
        headings.append(('airway',item.text.strip(),m,item))
    for item in page.get_by_regex(minorre):
        m=re.match(minorre,item.text).group()
        assert m!=None
        assert m.strip()!=""
        #print "Heading %d: %s"%(item.y1,m)
        headings.append(('minor',item.text.strip(),m,item))
    for item in page.get_by_regex(delegre):
        m,=re.match(delegre,item.text).groups()
        assert m!=None
        assert m.strip()!=""
        headings.append(('deleg',item.text.strip(),m,item))
    #print headings
    headings.sort(key=lambda x:x[3].y1)
    def findheadingfor(y,meta=None):
        minor=None
        major=None
        #print "HEadings:",headings
        for (kind,full,name,item) in reversed(headings):
            #print "Checking %s,%s (state: minor %s / major %s)"%(kind,item.y1,minor,major)
            if kind=='airway' and item.y1<y:
                return name,"airway"
            if kind=='deleg' and item.y1<y:
                return name,"deleg"
            if minor==None and kind=="minor" and item.y1<y:
                minor=name.strip()
                if meta!=None: meta['minor_y']=item.y1
            if major==None and kind=="major" and item.y1<y:
                major=name.strip()
                fullname=full
                if meta!=None: meta['major_y']=item.y1
                break
        assert major!=None and major.strip()!=""
        if minor!=None:
            return major+" "+minor,"area"
        return fullname,"area"
    cury=0
    coordstrs=page.get_by_regex(ur".*\d{6}N \d{7}E.*")

    airway_width=None
    airway_vlim=None
    for item in page.get_partially_in_rect(0,0,100,15):
        if item.text.upper().count("WID NM"):
            airway_width=(item.x1,item.x2)
        if item.text.lower().count("vertical limits"):
            airway_vlim=(item.x1,item.x2) 
    
    out=[]
    atsout=[]
    while True:
        found=False
        #print "Looking for coords, y= %d"%(cury,)
        for titem in coordstrs:
            #print "Considering coordstr: ",titem.y1
            if titem.y1<=cury: continue
            if titem.x1<40: 
                item=titem
                found=True
                break
        if not found: break
        cury=item.y1
        headmeta=dict()
        name,hkind=findheadingfor(item.y1,headmeta)
        
        if hkind=='airway':
            assert airway_width and airway_vlim
            
            lines=page.get_lines(page.get_partially_in_rect(0,cury,minx+35,100),order_fudge=6)
            y1=cury
            y2=100
            coordlines=[]
            for idx,line in enumerate(lines):
                if line.count("AWY") and line.count("EF"): 
                    y2=line.y1
                    break            
                coordlines.append(line.strip())
            coordstr=" ".join(coordlines)
            inpoints=[mapper.parse_coords(lat,lon) for lat,lon in re.findall(r"(\d+N) (\d+E)",coordstr)]
                        
            for wcand in page.get_partially_in_rect(airway_width[0],y1+0.05,airway_width[1],y2-0.05):
                width_nm=float(re.match(r"(\d+\.?\d*)",wcand.text).groups()[0])
                
            elevs=[]
            for vcand in page.get_partially_in_rect(airway_vlim[0],y1+0.05,airway_vlim[1],y2-0.05):                
                elevs.append(re.match(r"(FL\s*\d+)",vcand.text).groups()[0])
            elevs.sort(key=lambda x:mapper.parse_elev(x))
            floor,ceiling=elevs
                
            atsout.append(dict(
                floor=floor,
                ceiling=ceiling,
                freqs=[],
                type="RNAV",
                name=name,
                points=ats_routes.get_latlon_outline(inpoints, width_nm)))
                                    
            cury=y2          
            continue            
        elif hkind=='deleg':
                        
            y2=cury+1
            continue            
        else:
            areaspec=[]
            #print "Rect: ",0,cury,minx+35,100
            y1=cury
            lines=page.get_lines(page.get_partially_in_rect(0,cury,minx+35,100),order_fudge=10)
            for idx,line in enumerate(lines):
                if re.search(ur"FL \d+",line) or line.count("FT MSL"): 
                    vertidx=idx
                    break            
                #print "Line:",line.encode('utf8')
                if line.strip()=="":
                    vertidx=idx
                    break
                cury=max(cury,line.y2+0.5)                
                line=line.replace(u"–","-")
                if not (line.endswith("-") or line.endswith(" ")):
                    line+=" "                
                areaspec.append(line)
            verts=[]
            
            for idx in xrange(vertidx,len(lines)):
                #print "Looking for alt:",lines[idx],"y2:",lines[idx].y2
                m=re.search(ur"(FL\s+\d+)",lines[idx].strip())
                if m:
                    verts.append((m.groups()[0],lines[idx].y1))
                m=re.search(ur"(\d+ FT (?:MSL|GND|SFC))",lines[idx].strip())
                if m:
                    verts.append((m.groups()[0],lines[idx].y1))
                if len(verts)>=2: break
            y2=verts[-1][1]
            
        
        freqs=[]
        for attempt in xrange(2):
            for freqcand in page.get_by_regex(ur".*\d{3}\.\d{3}.*"):
                #print "headmeta:",headmeta
                #print "attempt:",attempt
                #print "freqy1:",freqcand.y1
                if freqcand.x1<30: continue
                if attempt==0:
                    if freqcand.y1<y1: continue
                else:
                    if 'major_y' in headmeta:                    
                        if freqcand.y1<headmeta['major_y']: continue
                    else:
                        if freqcand.y1<y1: continue
                                
                    
                if freqcand.y1>y2: continue
                x,y=freqcand.x1,freqcand.y1
                lines=page.get_lines(page.get_partially_in_rect(x+0.1,y-10,x+5,y-0.1))

                freq,=re.match(ur".*(\d{3}\.\d{3}).*",freqcand.text).groups()
                fname=None
                for line in reversed(lines):
                    if re.match(ur"[A-ZÅÄÖ ]{3,}",line):                        
                        #print "freqname Matched:",line
                        fname=line.strip()
                        break
                if not fname: raise Exception("Found no frequency name for freq: "+freq)
                freqs.append((fname,float(freq)))
            if len(freqs): break
        
        (ceiling,ceilingy),(floor,floory)=verts
        assert ceilingy<floory
        assert floory-ceilingy<5.0
        #uprint("Analyzing area for %s"%(name,))
        assert "".join(areaspec).strip()!=""
        print areaspec
        area=mapper.parse_coord_str("".join(areaspec))
        #uprint("Done analyzing %s"%(name,))
        #print area
        if name.count("CTA") and name.count("TMA")==0:
            type_="CTA"
        else:
            type_="TMA"
        
        out.append(dict(
            floor=floor,
            ceiling=ceiling,
            freqs=freqs,
            type=type_,
            name=name,
            points=area))
    
    return out,atsout
def pretty(pa):
    uprint("\n\nName: %s"%(pa['name'].encode('utf8'),))
    uprint("==============================================================================")
    uprint("Floor: %s, Ceiling: %s, freqs: %s"%(pa['floor'],pa['ceiling'],pa['freqs']))
    uprint("Points: %s"%(pa['points'],))

def fi_parse_tma():
    def fixgote(raw):
        #Fix illogical compositions...
        if 0:
            illo="""<text top="295" left="57" width="268" height="7" font="1">     Part of GÖTEBORG TMA  584558N 0122951E """
            assert raw.count(illo)
            #print "fix up gote"
            raw=raw.replace(illo,                
                            """<text top="296" left="5" width="138" height="7" font="1">     Part of GÖTEBORG TMA</text>
                               <text top="296" left="168" width="58" height="7" font="1">584558N 0122951E """)
        return raw
    p=parse.Parser(r"/ais/eaip/pdf/enr/EF_ENR_2_1_EN.pdf",fixgote,country='fi')
	
    res=[]    
    atsres=[]
    for pagenr in xrange(4,p.get_num_pages()): 
        parsed,atsparsed=parse_page(p,pagenr)#pagenr)
        res.extend(parsed)
        atsres.extend(atsparsed)        
        #break
        
    
    print "Len ouf out ",len(res)    
    for space in atsres:
        print "bef cut:",space['points']
        mypoly=makepoly.poly(space['points'])
        
        for tmaitem in res:
            if tmaitem['type']!='TMA': continue
            tmapoly=makepoly.poly(tmaitem['points'])
            #print mypoly
            #print tmapoly
            shape=mypoly.subtract(tmapoly)
            mypolys=shape.get_polys()

            #print "Length is:", len(mypolys)
            mypoly=shapemerge2d.Polygon(mypolys[0])
            #print "Cutting"
            #print "Cut to:",mypoly
        t=[]
        for mx,my in [(v.get_x(),v.get_y()) for v in  mypoly.get_vertices()]:
            t.append(mapper.to_str(mapper.merc2latlon((mx,my),13)))
        print "Aft cut:",t
        space['points']=t
        
    res.extend(atsres)
        
    res.append(dict(
        name="FINLAND FIR",
        icao="EFIN",
        floor='GND',
        ceiling='-',
        freqs=[],
        type='FIR',
        date=datetime(2011,4,9),
        points=mapper.parse_coord_str("""                                   
    601130N 0190512E - 601803N 0190756E -
610000N 0191905E - 614000N 0193000E -
631000N 0201000E - 632830N 0204000E -
633700N 0213000E - 644100N 0225500E -
653148N 0240824E -
Along the common X/Y state boundary to 690336N 0203255E -
Along the common X/Y state boundary to 690307N 0285545E -
Along the common X/Y state boundary to 601201N 0271735E - 
600800N 0263300E -
595830N 0260642E - 595300N 0255200E -
595430N 0252000E - 595300N 0245100E -
590000N 0210000E - 591524N 0203239E -
593346N 0195859E - 601130N 0190512E
""",context="finland")))
        
        
        
    #for pa in res:
    #    pretty(pa)
        
        
    return res

def fi_parse_r_areas():
    p=parse.Parser("/ais/eaip/pdf/enr/EF_ENR_5_1_en.pdf",lambda x: x,country='fi')
	
    res=[]    
    for pagenr in xrange(2,p.get_num_pages()): 
        parsed=parse_page(p,pagenr,"R")
        res.extend(parsed)

    #for pa in res:
    #    pretty(pa)
    return res

    
if __name__=='__main__':
    fi_parse_tma()
    #parse_r_areas()


