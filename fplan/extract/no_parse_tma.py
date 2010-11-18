#!/usr/bin/python
#encoding=utf8
import parse
from parse import Item
import re
import fplan.lib.mapper as mapper
import sys,os
import math
from area_parse_helper import find_areas
from fplan.lib.mapper import parse_coord_str,uprint
from pyshapemerge2d import Polygon,Vertex,vvector

"""
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
        if st.endswith("Avinor"): continue            
        if st.startswith("ENR 2.1 - 2"): continue            
        if st.startswith("NORSK"): continue            
        out.append(x)
    return out

def parse_page(parser,pagenr):   
    page=parser.parse_page_to_items(pagenr)
    out=[]
    for areaname,coords,meta in find_areas(page):
        print "Found area:",areaname
        if areaname.count("CTA") or areaname.count("FIR") or areaname.count("REF:ENR 2.2-3") or areaname.count("OCA"): continue
        
        assert areaname.count("TMA")
        lines=[x for x in page.get_lines(page.get_partially_in_rect(0,meta['y2']+0.5,100,meta['y2']+10)) if x.strip()]
        alts=[]
        for line in lines[:15]:
            print "Alt-parsing:",line
            m=re.match(ur"(FL \d+).*",line)
            if m:
               alts.append(m.groups()[0])
            m=re.match(ur"(\d+ FT AMSL).*",line)
            if m:
                alts.append(m.groups()[0])
            if len(alts)==2: break
        ceiling,floor=alts 
        identh,=page.get_by_regex(ur"IDENT")
        freqh,=page.get_by_regex(ur"FREQ")
        
        callsign= " ".join(page.get_lines(page.get_partially_in_rect(identh.x1,meta['y1']+0.25,freqh.x1-2.0,meta['y2'])))
        freqlines=" ".join(page.get_lines(page.get_partially_in_rect(freqh.x1,meta['y1'],freqh.x2,meta['y2'])))
        def wanted_freq(x):
            if abs(x-121.5)<1e-6: return False
            if x>150.0: return False
            return True
        freqs=[(callsign,float(x)) for x in re.findall(ur"\d{3}\.\d{3}",freqlines) if wanted_freq(float(x))]
                
        
        out.append(dict(
            floor=floor,
            ceiling=ceiling,
            freqs=freqs,
            type="TMA",
            name=areaname,
            points=coords))

    return out
def pretty(pa):
    uprint("\n\nName: %s"%(pa['name'].encode('utf8'),))
    uprint("==============================================================================")
    uprint("Floor: %s, Ceiling: %s, freqs: %s"%(pa['floor'],pa['ceiling'],pa['freqs']))
    uprint("Points: %s"%(pa['points'],))

def no_parse_tma():
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
        
    p=parse.Parser(r"/norway_aip/current/AIP/EN_ENR_2_1_en.pdf",fixgote,country='no')
	
    res=[]    
    for pagenr in xrange(4,p.get_num_pages()): 
        parsed=parse_page(p,pagenr)#pagenr)
        res.extend(parsed)
        #break
    for pa in res:
        pretty(pa)
    return res

def no_parse_r_areas():
    p=parse.Parser("/norway_aip/current/AIP/EN_ENR_5_1_en.pdf",lambda x: x,country='no')
	
    res=[]    
    for pagenr in xrange(2,p.get_num_pages()): 
        parsed=parse_page(p,pagenr,"R")
        res.extend(parsed)
    #for pa in res:
    #    pretty(pa)
    return res

    
if __name__=='__main__':
    no_parse_tma()
    #parse_r_areas()


