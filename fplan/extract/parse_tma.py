#!/usr/bin/python
#encoding=utf8
import parse
import re
import fplan.lib.mapper as mapper
import sys,os
import math

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
        #print "heights for ",d['name'],":",repr(heights)
        assert len(heights)==2
        ceiling=heights[0].strip()
        floor=heights[1].strip()
        
        pa['name']=d['name']
        pa['floor']=floor
        pa['ceiling']=ceiling
        print "Arealines:\n================\n%s\n============\n"%(arealines[:last_coord_idx])
        print pa
        pa['points']=list(parse_coord_str(" ".join(arealines[:last_coord_idx])))
        vs=[]
        for p in pa['points']:
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
        did_replace=[0]
        def replacer(args):
            print args.groups()
            y,x,w,h,font=args.groups()            
            assert int(w)>=260 and int(w)<280
            assert int(h)>=6 and int(h)<=10
            x1=x
            y1=y
            w1=80
            h1=h

            x2=168
            y2=y
            w2=150
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
    for pagenr in xrange(5,p.get_num_pages()): 
        parsed=parse_page(p,pagenr,"TMA")#pagenr)
        res.extend(parsed)
    #for pa in res:
    #    pretty(pa)
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


