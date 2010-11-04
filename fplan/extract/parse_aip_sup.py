from fetchdata import getxml,get_raw_aip_sup_page
from parse import Parser
import re
import sys
from fplan.lib.mapper import parse_coord_str
import extra_airfields
import fplan.lib.mapper as mapper
from pyshapemerge2d import Vertex,Polygon,vvector
from fplan.lib.mapper import parse_coords,uprint
import csv
from fplan.lib.get_terrain_elev import get_terrain_elev
import math
    
def extract_single_sup(full_url,sup,supname):
    #print getxml("/AIP/AD/AD 1/ES_AD_1_1_en.pdf")
    ads=[]
    try:
        p=Parser(sup)
    except:
        print "Could't parse",sup
        #Some AIP SUP's contain invalid XML after conversion from PDF.
        #skip these for now
        return []
    areas=[]
    startpage=None
    for pagenr in xrange(p.get_num_pages()):            
        page=p.parse_page_to_items(pagenr)
        #print page.get_all_items()
        areastarts=sorted(page.get_by_regex(r".*?\d{4,6}[NS]\s*\d{5,7}[EW].*"),key=lambda x:(x.y1,x.x1))
        if len(areastarts)==0: continue
        #print "Found %d area-lines on page"%(len(areastarts),)
        #print areastarts
        idx=0
        cury=None
        while True:
            firstdiff=None
            process=[]
            while True:
                if idx>=len(areastarts): break
                process.append(areastarts[idx])            
                cury=areastarts[idx].y1
                #print "Diff:",diff,"firstdiff:",firstdiff,"delta:",diff-firstdiff if diff!=None and firstdiff!=None else ''
                idx+=1
                if idx<len(areastarts):
                    diff=areastarts[idx].y1-cury
                    assert diff>0.0
                    if firstdiff==None: firstdiff=diff
                    #print "Diff:",diff
                    if diff>6.0: 
                        #print "Diff too big"
                        break
                    if diff>1.35*firstdiff: 
                        #print "bad spacing",diff,1.5*firstdiff
                        break
            #print "Determined that these belong to one area:",process
            if len(process):
                alltext="\n".join(page.get_lines(process))
                print "<%s>"%(alltext,)
                anyarea=re.findall(r"((?:\d{4,6}[NS]\s+\d{5,7}[EW][^0-9]{0,3})+)",alltext,re.DOTALL|re.MULTILINE)
                print "Matching:"
                print anyarea
                if not len(anyarea): continue
                if len(re.findall(r"\d{4,6}[NS]\s+\d{5,7}[EW][^0-9]{0,3}",anyarea[0]))>=3:
                    coords=parse_coord_str(anyarea[0].strip())
                    #print "AREA:"
                    #print coords
                    #print "===================================="
                    coordfontsize=process[0].fontsize
                    areaname=None
                    for item in reversed(sorted(page.get_partially_in_rect(0,0,100,process[0].y1),key=lambda x:(x.y1,x.x1))):
                        if item.text.strip()=="": continue
                        #print "fontsize",item.fontsize,item.text,"y1:",item.y1
                        if item.font!=process[0].font:
                            prevx1=item.x1
                            revname=[]
                            for nameitem in reversed(sorted(page.get_partially_in_rect(0,item.y1+0.01,item.x2,item.y2-0.01),key=lambda x:(x.x1))):
                                if prevx1-nameitem.x2>3.0:
                                    break
                                revname.append(nameitem.text.strip())                                
                            areaname=" ".join(reversed(revname))
                            break
                    if areaname:
                        name="%s (on page %d of %s)"%(areaname,pagenr+1,supname)
                    else:
                        name="Area on page %d of %s"%(pagenr+1,supname)
                    areas.append(dict(
                        url=full_url,
                        pagenr=pagenr+1,
                        sup=supname,
                        name=name,
                        type='aip_sup',
                        points=coords))
            if idx>=len(areastarts): break            

        #hits=page.get_by_regex(r"[Ee]ntry.*[Ee]xit.*point")
        #items=sorted(page.get_partially_in_rect(holdingheading.x1+2.0,holdingheading.y2+0.1,holdingheading.x1+0.5,100),
        #    key=lambda x:x.y1)
        #    s=" ".join(page.get_lines(page.get_partially_in_rect(holdingheading.x1,y1+0.4,100,y2-0.1)))
    return areas

def parse_all_sups():
    raw=get_raw_aip_sup_page()
    print "Got raw sup page, %d bytes"%(len(raw),)
    areas=[]
    for base,sup in re.findall(r"(http://.*?)(/AIP/AIP.*Sup/SUP_\d+_\d+.pdf)",raw):
        print "Parsing",base,sup
        if sup.count('33_10'):
            #No longer active
            continue
        print "About to parse AIP SUP: <%s>"%(sup,)
        supname,=re.match(".*/(SUP_\d+_\d+.pdf)",sup).groups()
        areas.extend(extract_single_sup(base+sup,sup,supname))
    return areas
    
if __name__=='__main__':
    areas=parse_all_sups()
    for area in areas:
        print area['name'],'coords:',"-".join(mapper.format_lfv(*mapper.from_str(c)) for c in area['points'])
        
    
