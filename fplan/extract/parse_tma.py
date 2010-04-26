#!/usr/bin/python
#encoding=utf8
import parse


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
    
def normalize_items(items):
    minx=min(x.x1 for x in items)
    miny=min(x.y1 for x in items)
    maxx=max(x.x2 for x in items)
    maxy=max(x.y2 for x in items)
    xfactor=maxx-minx
    yfactor=maxy-miny
    for item in items:
        yield Item(
            text=item.text,
            x1=100.0*(item.x1-minx)/xfactor,
            y1=100.0*(item.y1-miny)/yfactor,
            x2=100.0*(item.x2-minx)/xfactor,
            y2=100.0*(item.y2-miny)/yfactor
            )    

    
def parse_page(parser,pagenr):
    pitems=parser.parse_page_to_items(pagenr)
    items=list(parser.normalize_items(pitems))
    items.sort(key=lambda item:item.y1)
    print "Possible Areas:"
    zone_candidates=[]
    headings=[]
    for item in items:        
        if item.text==None: continue
        item.text=item.text.strip()
        if item.text=="": continue
        if item.text=="Name": continue
        if item.text in ["Lateral limits","Vertical limits","ATC unit","Freq MHz","Callsign"]:
               headings.append(item)  
        
        if item.x1<10 and not item.text in ["Name",'None']:
            zone_candidates.append(item)
    print "found candidates:",zone_candidates
    if len(headings)==0:
        return []
    merged=[]
    for item in zone_candidates:
        if len(merged)==0:
            merged.append(item)
            continue
        last=merged[-1]
        if item.y1-last.y2<1.5:
            merged[-1]=Item(
                text=" ".join([last.text,item.text]),
                x1=min(last.x1,item.x1),
                x2=max(last.x2,item.x2),
                y1=min(last.y1,item.y1),
                y2=max(last.y2,item.y2))
        else:
            merged.append(item)
    for cand,nextcand in zip(merged[:-1],merged[1:]):
        cand.next_y1=nextcand.y1
    if len(merged):
        merged[-1].next_y1=100.0 #end of page
    
    for cand in merged:
        print "\n\nCandidate: %s\n----------------------------------------\n"%(cand.text.encode('utf8'))
        d=dict() 
        for item in items:            
            if item.y1>=cand.y1-0.05 and item.y2<cand.next_y1-0.05:
                def closeness(h):
                    return abs(h.x1-item.x1)
                print "Headings:",headings
                closest_heading=min(headings,
                        key=closeness)
                d.setdefault(closest_heading.text.strip(),[]).append(item.text)
        print d                   
        pass
    return merged

if __name__=='__main__':
    def fixgote(raw):
        #Fix illogical composition of Göteborg TMA description. 2010 04 02
        illo="""<text top="296" left="57" width="268" height="7" font="1">     Part of GÖTEBORG TMA  584558N 0122951E - 584358N 0130950E - </text>"""
        assert raw.count(illo)
        raw=raw.replace(illo,                
                        """<text top="296" left="57" width="268" height="7" font="1">     Part of GÖTEBORG TMA</text>
                           <text top="296" left="168" width="268" height="7" font="1">584558N 0122951E - 584358N 0130950E - </text>""")
        return raw
    p=parse.Parser("/AIP/ENR/ENR 2/ES_ENR_2_1_en.pdf")
    
    for pagenr in xrange(p.get_num_pages()): 
        parse_page(p,pagenr)



