#encoding=utf8
import parse
from parse import Item
import re
import fplan.lib.mapper as mapper
from itertools import izip

def ee_parse_sigpoints():
    points=[]
    p=parse.Parser("/index.aw?section=9142&action=genpdf&file=9142.pdf",lambda x: x,country='ee')
    for pagenr in xrange(p.get_num_pages()):        
        page=p.parse_page_to_items(pagenr)
        for item in page.get_by_regex(ur"\d{6}N\s*\d{7}E"):                    
            lines=page.get_lines(page.get_partially_in_rect(0,item.y1+0.01,100,item.y2-0.01))
            print "Sigpoint lines:%s"%(repr(lines,))
            
            lines=[line for line in lines if re.match(ur"\s*\w{4,6}.*\d{6}N\s*\d{7}E.*",line,re.UNICODE)]
            print lines
            assert len(lines)==1
            print "parse:",lines[0]
            name,lat,lon=re.match(ur"\s*(\w{4,6})\s*(\d{6}N)\s*(\d{7}E).*",lines[0],re.UNICODE).groups()
            points.append(dict(
                name=name,
                kind='sig. point',
                pos=mapper.parse_coords(lat,lon)))                
            
    return points
        
    
if __name__=='__main__':
    pts=ee_parse_sigpoints()
    print "Sig points:"
    for sp in pts:
        print "Name:",sp['name']
        print "  Pos:",sp['pos']
        
