#encoding=utf8
import parse
from parse import Item
import re
import fplan.lib.mapper as mapper
from itertools import izip

def fi_parse_sigpoints():
    points=[]
    p=parse.Parser("/fi/EF_ENR_4_4_EN.pdf",lambda x: x)
    for pagenr in xrange(p.get_num_pages()):        
        page=p.parse_page_to_items(pagenr)
        for item in page.get_by_regex(ur"\d{6}N\s*\d{7}E"):        
            lines=page.get_lines(page.get_partially_in_rect(0,item.y1,100,item.y2))
            assert len(lines)==1
            print "parse:",lines[0]
            name,lat,lon=re.match(ur"\s*([A-Z]{5})\s*(?:\(\s*FLYOVER\s*\))?\s*X?\s*(\d{6}N)\s*(\d{7}E)\s*.*",lines[0]).groups()
            points.append(dict(
                name=name,
                kind='sig. point',
                pos=mapper.parse_coords(lat,lon)))                
            
    return points
        
    
if __name__=='__main__':
    pts=fi_parse_sigpoints()
    print "Sig points:"
    for sp in pts:
        print "Name:",sp['name']
        print "  Pos:",sp['pos']
        
