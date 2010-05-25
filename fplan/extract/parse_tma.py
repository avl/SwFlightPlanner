#!/usr/bin/python
#encoding=utf8
import parse
import re
import fplan.lib.mapper as mapper
import sys,os
import math
from parse import uprint



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

def parsecoord(seg):
    latlon=seg.strip().split(" ")
    if len(latlon)!=2:
        raise mapper.MapperBadFormat()
    lat,lon=latlon
    coord=mapper.parse_coords(lat.strip(),lon.strip())
    return coord
def parse_dist(s):
    uprint("In:%s"%s)
    val,nautical,meters=re.match(r"\s*([\d.]+)\s*(?:(NM)|(m))\b\s*",s).groups()
    dval=float(val)
    assert nautical!=None or meters!=None
    if meters:
        dval=dval/1852.0
    return dval

def minus(x,y):
    return tuple(a-b for a,b in zip(x,y))
def plus(x,y):
    return tuple(a+b for a,b in zip(x,y))
def scalarprod(x,y):
    return sum(a*b for a,b in zip(x,y))

def seg_angles(a1,a2,step):
    assert a2>a1
    dist=a2-a1
    nominal_cnt=math.ceil(dist/step)
    if nominal_cnt<=1:
        yield a1
        yield a2
        return
    delta=dist/float(nominal_cnt)
    a=a1
    for x in xrange(nominal_cnt):
        yield a
        a+=delta
    yield a2
     
    
def create_circle(center,dist_nm):
    zoom=14
    centermerc=mapper.latlon2merc(mapper.from_str(center),zoom)
    radius_pixels=mapper.approx_scale(centermerc,zoom,dist_nm)
    steps=dist_nm*math.pi*2/5.0
    if steps<16:
        steps=16
    out=[]
    angles=list(seg_angles(0,2.0*math.pi,math.pi*2.0/steps))
    for cnt,a in enumerate(angles):
        if cnt!=len(angles)-1:
            x=math.cos(a)*radius_pixels
            y=math.sin(a)*radius_pixels
            out.append(plus((x,y),centermerc))
    out2=[]
    for o in out:
        out2.append(mapper.to_str(mapper.merc2latlon(o,zoom)))
    return out2
    
def create_seg_sequence(prevpos,center,nextpos,dist_nm):
    zoom=14
    prevmerc=mapper.latlon2merc(mapper.from_str(prevpos),zoom)
    centermerc=mapper.latlon2merc(mapper.from_str(center),zoom)
    nextmerc=mapper.latlon2merc(mapper.from_str(nextpos),zoom)
    
    d1=minus(prevmerc,centermerc)
    d2=minus(nextmerc,centermerc)
    a1=math.atan2(d1[1],d1[0])
    a2=math.atan2(d2[1],d2[0])
    
    radius_pixels=mapper.approx_scale(centermerc,zoom,dist_nm)
    
    if a2<a1:
        a2+=math.pi*2
    if abs(a2-a1)<1e-6:
        return []
    steps=abs(a2-a1)/(math.pi*2.0)*dist_nm*math.pi*2/5.0
    if steps<16:
        steps=16
    out=[]
    angles=list(seg_angles(a1,a2,abs(a2-a1)/steps))
    for cnt,a in enumerate(angles):
        if cnt!=0 and cnt!=len(angles)-1:
            x=math.cos(a)*radius_pixels
            y=math.sin(a)*radius_pixels
            out.append(plus((x,y),centermerc))
    out2=[]
    for o in out:
        out2.append(mapper.to_str(mapper.merc2latlon(o,zoom)))
    return out2

def parse_area_segment(seg,prev,next):
    try:
        return [parsecoord(seg)]
    except mapper.MapperBadFormat:
        pass #continue processing
    border=re.match("Swedish/Danish border northward to (.*)",seg)
    if border:
        lat,lon=border.groups()[0].strip().split(" ")
        return [parsecoord(border.groups()[0])]
    arc=re.match(r"\s*clockwise along an arc cent[red]{1,5} on (.*) and with radius (.*)",seg)
    if arc:
        centerstr,radius=arc.groups()
        uprint("Parsing coord: %s"%centerstr)
        center=parsecoord(centerstr)
        dist_nm=parse_dist(radius)
        prevpos=parsecoord(prev)
        nextpos=parsecoord(next)
        uprint("Arc center: %s"%(center,))
        uprint("Seg params: %s %s %s %s"%(prevpos,center,dist_nm,nextpos))
        return create_seg_sequence(prevpos,center,nextpos,dist_nm)
    uprint("Matching against: %s"%(seg,))
    circ=re.match(r"\s*A circle with radius ([\d\.]+ (?:NM|m))\s+(?:\(.* km\))?\s*cent[red]{1,5}\s*on\s*(\d+N) (\d+E)\b.*",seg)
    if circ:
        radius,lat,lon=circ.groups()
        assert prev==None and next==None        
        uprint("Parsed circle:%s : %s"%(circ,circ.groups()))
        dist_nm=parse_dist(radius)
        zoom=14
        center=mapper.parse_coords(lat,lon)
        return create_circle(center,dist_nm)
    
    uprint("Unparsed area segment: %s"%(seg,))
    return []

def parse_coord_str(s):
    borderspecs=[
        "Swedish/Danish border northward to",
        "Swedish/Norwegian border northward to",
        ]
    uprint("Parsing area: %s"%(s,))
    items=s.split("-")
    out=[]
    for idx,pstr2 in enumerate(items):
        prev=None
        next=None
        if idx!=0:
            prev=items[idx-1]
        if idx!=len(items)-1:
            next=items[idx+1]
        pstr=pstr2
        #print "Coord str: <%s>"%(pstr,)
        
        for spec in borderspecs:
            if pstr2.count(spec):
                pstr=pstr2.replace(spec,"")
                break                
        if pstr.strip()=="": continue
        pd=parse_area_segment(pstr,prev,next)
        uprint("Parsed area segment <%s> into <%s>"%(pstr,pd))
        out.extend(pd)
        
    return out
def is_r_or_danger_area_name(name):
    uprint("Is danger/R: %s"%(name,))
    if re.match("ES\s+[DR]\d+[A-Za-z]?",name):
        uprint("Yes!")
        return True
    uprint("No!")
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
        if kind=="R" and not is_r_or_danger_area_name(item.text.strip()):
            continue
        if item.y1>avg_heading_y+1 and item.x1<10 and not item.text in ["Name",'None']:
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
        uprint("D:<%s> (area:%s)"%(d,arealines))
        assert len(arealines)
        for idx in xrange(len(arealines)):
            if arealines[idx].lower().startswith("established"):
                last_coord_idx=idx
                pa['established']=" ".join(l for l in arealines[idx:])   
                break
            if arealines[idx].lower().startswith("danger area"):
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
        
        #print "Vertlim: ",vertlim
        heightst=re.findall(r"(FL\s*\d{3})|(\d+\s*ft (?:\s*/\s*\d+\s*.\s*GND)?)|(GND)|(UNL)",vertlim)
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
        print "heights:",repr(heights)
        assert len(heights)==2
        ceiling=heights[0].strip()
        floor=heights[1].strip()
        
        pa['name']=d['name']
        pa['floor']=floor
        pa['ceiling']=ceiling
        pa['points']=list(parse_coord_str(" ".join(arealines[:last_coord_idx])))
        for p in pa['points']:
            assert p.count(",")==1 
        pa['type']=kind
        atc=d[thirdcol]
        #print "ATc: <%s>"%(repr(atc),)
        freqs=[(y,float(x)) for x,y in re.findall(r"(\d{3}\.\d{3})\s*MHz\n(.*)","\n".join(atc))]
        #print repr(freqs)
        pa['freqs']=freqs
        
        out.append(pa)
    return out
def pretty(pa):
    uprint("\n\nName: %s"%(pa['name'].encode('utf8'),))
    uprint("==============================================================================")
    uprint("Floor: %s, Ceiling: %s, freqs: %s"%(pa['floor'],pa['ceiling'],pa['freqs']))
    uprint("Points: %s"%(pa['points'],))

def parse_all_tma():
    def fixgote(raw):
        #Fix illogical composition of Göteborg TMA description. 2010 04 02
        illo="""<text top="295" left="57" width="268" height="7" font="1">     Part of GÖTEBORG TMA  584558N 0122951E """
        assert raw.count(illo)
        #print "fix up gote"
        raw=raw.replace(illo,                
                        """<text top="296" left="5" width="138" height="7" font="1">     Part of GÖTEBORG TMA</text>
                           <text top="296" left="168" width="58" height="7" font="1">584558N 0122951E """)
        return raw
    p=parse.Parser("/AIP/ENR/ENR 2/ES_ENR_2_1_en.pdf",fixgote)
	
    res=[]    
    for pagenr in xrange(5,p.get_num_pages()): 
        parsed=parse_page(p,pagenr,"TMA")#pagenr)
        res.extend(parsed)
    #for pa in res:
    #    pretty(pa)
    return res

def parse_r_areas():
    p=parse.Parser("/AIP/ENR/ENR 2/ES_ENR_5_1_en.pdf",lambda x: x)
	
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


