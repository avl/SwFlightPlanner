#encoding=utf8
import parse
from parse import Item
import re
import fplan.lib.mapper as mapper
from itertools import izip

def ey_parse_sigpoints():
    points=[]
    p=parse.Parser("/EY_ENR_4_4_en_2011-03-10.pdf",lambda x: x,country='ee')
    for pagenr in xrange(p.get_num_pages()):        
        page=p.parse_page_to_items(pagenr)
        for item in page.get_by_regex(ur"[\d\s]+N\s*[\d\s]+E"):                    
            lines=page.get_lines(page.get_partially_in_rect(0,item.y1+0.01,100,item.y2-0.01))
            print "Sigpoint lines:%s"%(repr(lines,))
            
            lines=[line for line in lines if re.match(ur"\s*\w{4,6}.*[\d\s]+N\s*[\d\s]+E.*",line,re.UNICODE)]
            print lines
            assert len(lines)==1
            print "parse:",lines[0]
            name,lat,lon=re.match(ur"\s*(\w{4,6})\s*([\d\s]+N)\s*([\d\s]+E).*",lines[0],re.UNICODE).groups()
            points.append(dict(
                name=name,
                kind='sig. point',
                pos=mapper.parse_coords(lat.replace(" ",""),lon.replace(" ",""))))                
            
    return points
        
    
if __name__=='__main__':
    pts=ey_parse_sigpoints()
    print "Sig points:"
    for sp in pts:
        print "Name:",sp['name']
        print "  Pos:",sp['pos']
        
