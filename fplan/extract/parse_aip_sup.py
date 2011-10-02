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
from area_parse_helper import find_areas
        

def extract_single_sup(full_url,sup,supname,opening_ours):
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
        for item in page.get_by_regex(".*HOURS OF OPERATION.*"):
            lines=page.get_lines(page.get_partially_in_rect(0,item.y1-2,100,item.y2+2))
            found=False
            for line in lines:
                if re.match(ur".*SUP\s*\d+/\d{4}\.?\s+HOURS OF OPERATION\s*$",line):
                    opening_ours.add(p.get_url())
                    print "Found hours:",opening_ours
            
            
        for areaname,coords,meta in find_areas(page):
            if areaname:
                name="%s (on page %d of %s)"%(areaname,pagenr+1,supname)
            else:
                name="Area on page %d of %s"%(pagenr+1,supname)
            print "Number of points",len(coords)
            areas.append(dict(
                url=full_url,
                pagenr=pagenr+1,
                sup=supname,
                name=name,
                type='aip_sup',
                points=coords))

        #hits=page.get_by_regex(r"[Ee]ntry.*[Ee]xit.*point")
        #items=sorted(page.get_partially_in_rect(holdingheading.x1+2.0,holdingheading.y2+0.1,holdingheading.x1+0.5,100),
        #    key=lambda x:x.y1)
        #    s=" ".join(page.get_lines(page.get_partially_in_rect(holdingheading.x1,y1+0.4,100,y2-0.1)))
    return areas

def parse_all_sups(limiter=None):
    raw=get_raw_aip_sup_page()
    print "Got raw sup page, %d bytes"%(len(raw),)
    areas=[]
    opening_ours=set()
    for base,sup in re.findall(r"(http://.*?)(/AIP/AIP.*Sup/SUP_\d+_\d+.pdf)",raw):
        #print "Parsing",base,sup
        if sup.count('33_10') or sup.count("14_11"):
            #No longer active
            continue
        
        #print "About to parse AIP SUP: <%s>"%(sup,)
        supname,=re.match(".*/(SUP_\d+_\d+.pdf)",sup).groups()
        if limiter!=None and limiter(supname)==False:
            continue
        areas.extend(extract_single_sup(base+sup,sup,supname,opening_ours))
    if "http://www.lfv.se/AIP/AIP%20Sup/SUP_52_10.pdf" in opening_ours:
        opening_ours.remove("http://www.lfv.se/AIP/AIP%20Sup/SUP_52_10.pdf")
    if not opening_ours:
        opening_ours=['unknown']
    
    return areas,list(opening_ours)[0]
    
if __name__=='__main__':
    def limiter(x):
        if len(sys.argv)<=1: return True
        if x.count(sys.argv[1]):
            return True
        return False
    if len(sys.argv)<=1:
        limiter=None
    areas,opening_hours=parse_all_sups(limiter)
    f=open("aipsup-out.txt","w")
    for area in sorted(areas,key=lambda x:x['name']):
        t="%s: coords: %s "%(area['name'],"-".join(mapper.format_lfv(*mapper.from_str(c)) for c in area['points']))
        print t
        f.write(repr(t)+"\n")
    print "Opening_hours url:",opening_hours
    f.write("Hours:"+opening_hours)
    f.close()
        
    
