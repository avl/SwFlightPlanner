#!/usr/bin/python
#encoding=utf8
import parse
import re
import fplan.lib.mapper as mapper
from fplan.lib.poly_cleaner import clean_up_polygon
import sys,os
import math
from datetime import datetime

from fplan.lib.mapper import parse_coord_str,uprint
from pyshapemerge2d import Polygon,Vertex,vvector

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

def parse_page(parser,pagenr,kind="TMA"):   
    if kind=="TMA":
        thirdcol="ATC unit"
    elif kind=="R":
        thirdcol="Remarks (nature of hazard,"
    else:
        raise Exception("Bad kind")
    page=parser.parse_page_to_items(pagenr)
    items=page.items
    #print "Items:",pitems    

    #print "Possible Areas:"
    headings=[]
    for item in items:        
        if item.text==None: continue
        item.text=item.text.strip()
        if item.text=="": continue
        if item.text=="Name": continue
        if item.y1<25 and item.text in ["Lateral limits","Vertical limits",thirdcol]:
               headings.append(item)  
    
    headings.sort(key=lambda x:x.x1)    
    #print "found candidates:",zone_candidates    
    if len(headings)==0:
        return []
    avg_heading_y=sum(h.y1 for h in headings)/float(len(headings))
    #print "Found headings:",headings
    zone_candidates=[]
    for item in items:        
        if item.text==None or item.text.strip()=="": continue
        if item.text.strip().startswith("AMDT"): continue
        if item.text.strip().startswith("The LFV Group"): continue
        if re.match(ur"\s*LFV\s*AIRAC\s*AMDT\s*\d+/\d+\s*",item.text): continue
        if item.text.strip()=="LFV": continue
        if item.text.strip().startswith("AIRAC"): continue        
        if kind=="R" and not is_r_or_danger_area_name(item.text.strip()):
            continue
        if item.y1>avg_heading_y+1 and item.x1<12 and not item.text in ["Name",'None',"LFV"]:
            zone_candidates.append(item)
    
    zone_candidates.sort(key=lambda x:x.y1)
    
    for zone in zone_candidates:
        assert not zone.text.count("AOR")
        assert not zone.text.count("FIR")
            
    assert len(headings)==3
    
    
    
    ret=[]
    for i in xrange(len(zone_candidates)):
        d=dict()
        cand=zone_candidates[i]
        if i<len(zone_candidates)-1:
            nextcand=zone_candidates[i+1]
        else:
            nextcand=None
        y1=cand.y1-0.25
        y2=100
        if nextcand: y2=nextcand.y1-0.75
        for j in xrange(len(headings)):
            head=headings[j]
            if j<len(headings)-1:
                nexthead=headings[j+1]
            else:
                nexthead=None
            x1=head.x1
            x2=head.x2
            if j==len(headings)-1:                
                x1=headings[j-1].x2+3
                x2=100
            lines=page.get_lines(page.get_partially_in_rect(x1,y1,x2,y2,xsort=True,ysort=True))
            #print ("Parsed %s y,%d-%d, %s: <%s>\n\n"%(cand.text,y1,y2,head.text,lines)).encode('utf8')
            d[head.text]=lines        
        if kind=="R":
            d['name']=" ".join(x.strip() for x in filter_head_foot(page.get_lines(page.get_partially_in_rect(0,y1,10,y2,xsort=True,ysort=True))))
        else:
            d['name']=cand.text.strip()
        ret.append(d)  


    
    out=[]
    for d in ret:
        pa=dict()
        arealines=[l for l in d['Lateral limits'] if l.strip()!=""]
        last_coord_idx=None
        #uprint("D:<%s> (area:%s)"%(d,arealines))
        assert len(arealines)
        if arealines[0].strip()=="Danger area EK D395 and D396 are":
            arealines=arealines[1:]
        if arealines[0].strip()=="situated within TMA":
            arealines=arealines[1:]

        for idx in xrange(len(arealines)):
            if arealines[idx].lower().startswith("established"):
                last_coord_idx=idx
                pa['established']=" ".join(l for l in arealines[idx:])   
                break
            if arealines[idx].lower().startswith("danger area"):
                last_coord_idx=idx
                break
            if arealines[idx].strip()=="LFV":
                last_coord_idx=idx
                break
        if last_coord_idx==None:
            last_coord_idx=len(arealines)
        #print "ARealines:",arealines
        assert not arealines[last_coord_idx-1].strip().endswith("-")
        #for idx in xrange(last_coord_idx-1):
        #    print "arealine: <%s>"%(arealines[idx].strip(),)
        #    assert arealines[idx].strip().endswith("-") or arealines[idx].strip().endswith("to")
        
        vertlim=u" ".join(d['Vertical limits'])
        if vertlim.strip()=="":
            #print "Object with no vertical limits: %s"%(repr(d['name']),)
            continue
        
        print "Vertlim: ",vertlim
        heightst=re.findall(r"(FL\s*\d{3})|(\d+\s*ft\s*(?:\s*/\s*\d+\s*.\s*GND)?)|(GND)|(UNL)",vertlim)
        heights=[]
        for fl,ht,gnd,unl in heightst:
            if fl:
                heights.append(fl)
            if ht:
                heights.append(ht.strip())
            if gnd:
                heights.append(gnd.strip())
            if unl:
                heights.append(unl.strip())
        print "heights for ",d['name'],":",repr(heights)
        assert len(heights)==2
        ceiling=heights[0].strip()
        floor=heights[1].strip()
        
        pa['name']=d['name']
        pa['floor']=floor
        pa['ceiling']=ceiling
        print "Arealines:\n================\n%s\n============\n"%(arealines[:last_coord_idx])
        print pa
        areacoords=" ".join(arealines[:last_coord_idx])
        pa['points']=parse_coord_str(areacoords)
        
        
        vs=[]
        for p in pa['points']:
            print "from_str:",repr(p)
            x,y=mapper.latlon2merc(mapper.from_str(p),13)
            vs.append(Vertex(int(x),int(y)))

        p=Polygon(vvector(vs))
        if p.calc_area()<=30*30:
            print pa
            print "Area:",p.calc_area()
        assert p.calc_area()>30*30
        print "Area: %f"%(p.calc_area(),)
        print "Point-counts:",len(pa['points'])
        for p in pa['points']:
            assert p.count(",")==1 
        pa['type']=kind
        atc=d[thirdcol]
        #print "ATc: <%s>"%(repr(atc),)
        freqs=[(y,float(x)) for x,y in re.findall(r"(\d{3}\.\d{3})\s*MHz\n(.*)","\n".join(atc))]
        #print repr(freqs)
        pa['freqs']=freqs
        
        for cleaned in clean_up_polygon(list(pa['points'])):
            d=dict(pa)
            #print "cleaned",cleaned
            for tup in cleaned:
                assert type(tup)==str
                latlon=mapper.from_str(tup)
                lat,lon=latlon
                assert lat>=-85 and lat<=85
            d['points']=cleaned
            #print cleaned
            print "name:",d['name']
            print "cleaned points:",d['points']
            print "from:",areacoords
            #raise Exception()
            out.append(d)
        #if pa['name'].lower().count("esrange"):
        #    print "Exit esrange"
        #    sys.exit(1)
                    
    return out
def pretty(pa):
    uprint("\n\nName: %s"%(pa['name'].encode('utf8'),))
    uprint("==============================================================================")
    uprint("Floor: %s, Ceiling: %s, freqs: %s"%(pa['floor'],pa['ceiling'],pa['freqs']))
    uprint("Points: %s"%(pa['points'],))

def parse_all_tma():
    def fixgote(raw):
        #Fix illogical composition of Göteborg TMA description. 2010 04 02
        did_replace=[0]
        def replacer(args):
            print args.groups()
            y,x,w,h,font=args.groups()
            print w,h            
            assert int(w)>=260 and int(w)<420
            assert int(h)>=6 and int(h)<=15
            f=float(w)/270.0
            x1=x
            y1=y
            w1=80
            h1=h

            x2=168*f
            y2=y
            w2=150*f
            h2=h
            did_replace[0]+=1
            repl="""<text top="%s" left="%s" width="%s" height="%s" font="%s">Part of GÖTEBORG TMA</text>
                           <text top="%s" left="%s" width="%s" height="%s" font="%s">584558N 0122951E - 584358N 0130950E - </text>"""%(
                           y1,x1,w1,h1,font,y2,x2,w2,h2,font)
            print "\n======================================\nReplacement:\n",repl
            return repl
        raw=re.sub(r"""<text top="(\d+)" left="(\d+)" width="(\d+)" height="(\d+)" font="(\d+)">\s*Part of GÖTEBORG TMA  584558N 0122951E - 584358N 0130950E - </text>""",replacer,raw)
        assert did_replace[0]==1
        return raw
    p=parse.Parser("/AIP/ENR/ENR 2/ES_ENR_2_1_en.pdf",fixgote)
	
    res=[]    
    found=False
    for pagenr in xrange(0,p.get_num_pages()):
        page=p.parse_page_to_items(pagenr)
        if found or page.get_by_regex(r"Terminal Control Areas"):
            found=True
        else:
            continue        
        parsed=parse_page(p,pagenr,"TMA")
        res.extend(parsed)
        
    res.append(dict(
        name="SWEDEN FIR",
        icao="ESAA",
        floor='GND',
        ceiling='-',
        freqs=[],
        type='FIR',
        date=datetime(2011,4,9),
        points=mapper.parse_coord_str("""
690336N 0203255E - 
Along the common X/Y state boundary to 653148N 0240824E -
644100N 0225500E - 633700N 0213000E -
632830N 0204000E - 631000N 0201000E -
614000N 0193000E - 610000N 0191905E -
601803N 0190756E - 601130N 0190512E -
593346N 0195859E - 591524N 0203239E -
590000N 0210000E - 573410N 0200900E -
570000N 0195000E - 555100N 0173300E -
545500N 0155200E - 545500N 0150807E -
clockwise along an arc centred on 550404N 0144448E and with radius 16.2 NM -
545500N 0142127E - 545500N 0125100E -
552012N 0123827E - Along the common X/Y state boundary to 561253N 0122205E -
583000N 0103000E - 584540N 0103532E -
585332N 0103820E - Along the common X/Y state boundary to 690336N 0203255E
                                        
""",context="sweden")))
        
    for pa in res:
        pretty(pa)
    return res

def parse_r_areas():
    p=parse.Parser("/AIP/ENR/ENR 5/ES_ENR_5_1_en.pdf",lambda x: x)
	
    res=[]    
    for pagenr in xrange(2,p.get_num_pages()): 
        parsed=parse_page(p,pagenr,"R")
        res.extend(parsed)
    for pa in res:
        pretty(pa)
    return res

    
if __name__=='__main__':
    parse_all_tma()
    parse_r_areas()


