#!/usr/bin/python
#encoding=utf8
import parse
from parse import Item
import re
import fplan.lib.mapper as mapper
import sys,os
import math
from fplan.lib.mapper import parse_coord_str,uprint
from pyshapemerge2d import Polygon,Vertex,vvector
import fplan.extract.border_follower

def parse_page(parser,pagenr):   
    page=parser.parse_page_to_items(pagenr)
    items=page.items
    minx=min([item.x1 for item in items])
    headings=[]
    majorre=ur"\s*([A-ZÅÄÖ ][A-ZÅÄÖ]{3,})\s+(?:TMA\s*\d*|MIL CTA)\s*(?:-.*)?$"
    minorre=ur"\s*(?:TMA|MIL CTA [SN]?)\s*[A-ZÅÄÖ ]*\s*"
    for item in page.get_by_regex(majorre):
        m,=re.match(majorre,item.text).groups()
        assert m!=None
        assert m.strip()!=""
        headings.append(('major',item.text.strip(),m,item))
    for item in page.get_by_regex(minorre):
        m=re.match(minorre,item.text).group()
        assert m!=None
        assert m.strip()!=""
        #print "Heading %d: %s"%(item.y1,m)
        headings.append(('minor',item.text.strip(),m,item))
    #print headings
    headings.sort(key=lambda x:x[3].y1)
    def findheadingfor(y,meta=None):
        minor=None
        major=None
        for (kind,full,name,item) in reversed(headings):
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
            return major+" "+minor
        return fullname
    cury=0
    coordstrs=page.get_by_regex(ur".*\d{6}N \d{7}E.*")
    out=[]
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
        name=findheadingfor(item.y1,headmeta)
        areaspec=[]
        #print "Rect: ",0,cury,minx+35,100
        y1=cury
        lines=page.get_lines(page.get_partially_in_rect(0,cury,minx+25,100))
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
            for freqcand in page.get_by_regex(ur".*\d{3}\.\d{1,3}.*"):
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
                freq,=re.match(ur".*(\d{3}\.\d{3}).*",freqcand.text).groups()
                if freq=="121.500": continue
                lines=page.get_lines(page.get_partially_in_rect(x-10,y-1,x-0.5,y+1.5))
                fname=None
                for line in reversed(lines):
                    g=re.match(ur".*\b(\w{3,}\s+(?:Approach|Tower)).*",line)
                    if g:                        
                        #print "freqname Matched:",line
                        fname,=g.groups()
                        fname=fname.strip()
                        break
                if not fname: raise Exception("Found no frequency name for freq: "+freq)
                freqs.append((fname,float(freq)))
            if len(freqs): break
        
        (ceiling,ceilingy),(floor,floory)=verts
        assert ceilingy<floory
        assert floory-ceilingy<5.0
        uprint("Analyzing area for %s"%(name,))
        assert "".join(areaspec).strip()!=""
        area=mapper.parse_coord_str("".join(areaspec),context='estonia')
        uprint("Done analyzing %s"%(name,))
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
    

    return out
def pretty(pa):
    uprint("\n\nName: %s"%(pa['name'].encode('utf8'),))
    uprint("==============================================================================")
    uprint("Floor: %s, Ceiling: %s, freqs: %s"%(pa['floor'],pa['ceiling'],pa['freqs']))
    uprint("Points: %s"%(pa['points'],))

def ee_parse_tma():
    def fixgote(raw):
        return raw
    p=parse.Parser(r"/index.aw?section=9129&action=genpdf&file=9129.pdf",fixgote,country='ee')
	
    res=[]    
    for pagenr in xrange(1,p.get_num_pages()): 
        parsed=parse_page(p,pagenr)#pagenr)
        res.extend(parsed)
    for pa in res:
        pretty(pa)
    return res


    
if __name__=='__main__':
    ee_parse_tma()
    #parse_r_areas()


