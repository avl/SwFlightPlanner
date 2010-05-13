#!/usr/bin/python
#encoding=utf8
import parse
import re
import fplan.lib.mapper as mapper


from elementtree import ElementTree

#def load_xml():
#    raw=open("ES_ENR_2_1_en.xml").read()
#    
#    
#    if 1:
#        raw=raw.replace("""<text top="296" left="57" width="268" height="7" font="1">     Part of GÖTEBORG TMA  584558N 0122951E - 584358N 0130950E - </text>""",                
#                        """<text top="296" left="57" width="268" height="7" font="1">     Part of GÖTEBORG TMA</text>
#                           <text top="296" left="168" width="268" height="7" font="1">584558N 0122951E - 584358N 0130950E - </text>""")
#       
#    xml=ElementTree.fromstring(raw)
#    return xml



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
    

def parse_page(parser,pagenr):
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
        if item.y1<25 and item.text in ["Lateral limits","Vertical limits","ATC unit"]:
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
        y1=cand.y1
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
            lines=page.get_lines(page.get_partially_in_rect(x1,y1,x2,y2,True,True))
            #print ("Parsed %s, %s: <%s>\n\n"%(cand.text,head.text,lines)).encode('utf8')
            d[head.text]=lines        
        d['name']=cand.text.strip()
        ret.append(d)  
    
    def parse_coord_str(s):
        for pstr in s.split("-"):
            print "Coord str: <%s>"%(pstr,)
            lat,lon=pstr.strip().split(" ")
            yield mapper.parse_coords(lat.strip(),lon.strip())
    
    out=[]
    for d in ret:
        pa=dict()
        arealines=[l for l in d['Lateral limits'] if l.strip()!=""]
        last_coord_idx=None
        print "D:<%s> (area:%s)"%(d,arealines)
        assert len(arealines)
        for idx in xrange(len(arealines)):
            if arealines[idx].lower().startswith("established"):
                last_coord_idx=idx
                pa['established']=" ".join(l for l in arealines[idx:])   
                break
        if last_coord_idx==None:
            last_coord_idx=len(arealines)-1
        assert not arealines[last_coord_idx].strip().endswith("-")
        for idx in xrange(last_coord_idx-1):
            assert arealines[idx].strip().endswith("-")
        
        vertlim=u" ".join(d['Vertical limits'])
        if vertlim.strip()=="":
            print "Object with no vertical limits: ",d['name']
            continue
        
        print "Vertlim: ",vertlim
        heightst=re.findall(r"(FL\s*\d{3})|(\d+\s*ft)",vertlim)
        heights=[]
        for fl,ht in heightst:
            if fl:
                heights.append("FL%s"%(fl,))
            if ht:
                heights.append("%sft"%(ht.strip(),))                
            
        print heights
        assert len(heights)==2
        ceiling=heights[0].strip()
        floor=heights[1].strip()
        
        pa['name']=d['name']
        pa['floor']=floor
        pa['ceiling']=ceiling
        pa['points']=list(parse_coord_str("".join(arealines[:last_coord_idx])))
        
        atc=d['ATC unit']
        #print "ATc: <%s>"%(atc,)
        freqs=[(y,float(x)) for x,y in re.findall(r"(\d{3}\.\d{3})\s*MHz\n(.*)","".join(atc))]
        print freqs
        pa['freqs']=freqs
        
        out.append(pa)
    return out

if __name__=='__main__':
    def fixgote(raw):
        #Fix illogical composition of Göteborg TMA description. 2010 04 02
        illo="""<text top="296" left="57" width="268" height="7" font="1">     Part of GÖTEBORG TMA  584558N 0122951E - 584358N 0130950E - </text>"""
        assert raw.count(illo)
        print "fix up gote"
        raw=raw.replace(illo,                
                        """<text top="296" left="5" width="138" height="7" font="1">     Part of GÖTEBORG TMA</text>
                           <text top="296" left="168" width="58" height="7" font="1">584558N 0122951E - 584358N 0130950E - </text>""")
        return raw
    p=parse.Parser("/AIP/ENR/ENR 2/ES_ENR_2_1_en.pdf",fixgote)
    
    for pagenr in xrange(5,p.get_num_pages()): 
        parsed=parse_page(p,pagenr)#pagenr)
        print "\n\n========================================================\n\n"
        print parsed
        #break



