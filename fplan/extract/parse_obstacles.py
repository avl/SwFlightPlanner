#!/usr/bin/python
#encoding=utf8
import parse
import re
import fplan.lib.mapper as mapper
import sys,os
import math
from parse import uprint
obsttypes=[
"Wind turbine",
"Mast",
"Cathedral",
"Pylon",
"Building",
"Platform",
"Chimney",
"Mine hoist",
"Bridge pylon",
"Crane",
"W Tower",
"Church",
"Silo",
"City Hall",
"Gasometer",
"Tower",
"Bridge pylon, 60 per minute"]


def get_pixel_radius(o,zoomlevel):
    merc=mapper.latlon2merc(mapper.from_str(o['pos']),zoomlevel)
    draw_radius_nm=(int(o['height'])*2.0*0.16e-3)
    draw_radius_pixels=mapper.approx_scale(merc,zoomlevel,draw_radius_nm)
    radius=draw_radius_pixels
    if radius<4:
        radius=4
    return radius

def parse_obstacles():
    p=parse.Parser("/AIP/ENR/ENR 5/ES_ENR_5_4_en.pdf",lambda x: x)
    
    res=[]    
    for pagenr in xrange(0,p.get_num_pages()):
        page=p.parse_page_to_items(pagenr)
        
        items=page.get_by_regex(r"\bDesignation\b")
        print items
        assert len(items)==1
        ay1=items[0].y1
        ay2=100        
        in_rect=page.get_fully_in_rect(0,ay1,100,100)
        lines=page.get_lines(in_rect,order_fudge=20)
        for line in lines:
            line=line.strip()
            if line=="within radius 300 m.":
                continue
            if line=="": continue
            if line.startswith("AMDT"):
                continue
            if line.startswith("AIRAC AMDT"):
                continue
            if re.match("^Area\s*No\s*Designation.*",line):
                continue
            if re.match("^ft\s*ft\s*Character.*",line):
                continue
            if line.strip()=="The LFV Group":
                continue
            if line.startswith("The"): continue
            if line.startswith("LFV"): continue
            if line.startswith("Group"): continue
            if line.strip()=="": continue
            uprint("Matching line: <%s>"%(line,))
            if line.strip()=="Reverse side intentionally blank":
                continue
            m=re.match(r"\s*(?:\d{2}N \d{2}E)?\s*\d+\s*(.*?)(\d{6}\.?\d*N)\s*(\d{7}\.?\d*E)\s*(?:\(\*\))?\s*(\d+)\s*(\d+)\s*(.*)$",
                        line)
            if m:
                name,lat,lon,height,elev,more=m.groups()                
                uprint("Found match: %s"%(m.groups(),))
                light_and_type=re.match(r"(.*?)\s*("+"|".join(obsttypes)+")",more)
                if not light_and_type:
                    raise Exception(u"Unknown obstacle type:%s"%(more,))
                light,kind=light_and_type.groups()

                
                res.append(
                    dict(
                        name=name,
                        pos=mapper.parse_coords(lat,lon),
                        height=height,
                        elev=elev,
                        lighting=light,
                        kind=kind
                         ))
            else:
                raise Exception("Unparsed obstacle line: %s"%(line,))                
    return res

if __name__=='__main__':
    for obst in parse_obstacles():
        print obst
 
