#encoding=utf8
import parse
from parse import Item
import re
import fplan.lib.mapper as mapper
from itertools import izip

def fi_parse_obstacles():
    obsts=[]
    p=parse.Parser("/fi/EF_ENR_5_4_EN.pdf",lambda x: x)
    for pagenr in xrange(p.get_num_pages()):        
        page=p.parse_page_to_items(pagenr)
        item=min(page.get_by_regex(ur"(?:AIP SUOMI.*)|(?:ENR 5.4.*)"),key=lambda x:x.x1)
        assert item.x1<20
        lx=item.x1
        for item in page.get_by_regex(ur"\d{6}N\s*\d{7}E"):
            lines=page.get_lines(page.get_partially_in_rect(lx-1,item.y1-0.25,lx+5,item.y2+0.25))
            print "obj",lines
            assert len(lines)==1
            objid,=re.match("(EFINOB \d+)",lines[0]).groups()

            lines=page.get_lines(page.get_partially_in_rect(lx+15,item.y1-0.25,lx+25,item.y2+0.25))
            obsttypes=[ 
                        ("Savupiippu",'Chimney'),
                        ('Masto','Mast'),
                        ('Rakennus','Building'),
                        ('Tuulivoimala','Wind turbine'),
                        ('Torni','Tower'),
                        ('Nosturi','Crane')
                        ]
            
            lines=page.get_partially_in_rect(lx+15,item.y1-0.25,100,item.y2+0.25)
            lines.sort(key=lambda x:x.x1+0.05*x.y1) #sort mostly on x1, and slightly on y1
            nameandtype=" ".join(l.text.strip() for l in lines)
            name,kind=None,None
            for obst_fi,obst_en in obsttypes:
                regex=ur"(.{3,})\s+%s\s*/\s*(%s)\s*(\d{6}N)\s*(\d{7}E)\s+(\d+)\s+(\d+)(.*)"%(obst_fi,obst_en)
                m=re.match(regex,nameandtype)
                print "Matched <%s> against <%s>, result: %s"%(regex,nameandtype,m)
                if m:
                    name,kind,lat,lon,height,elev,lighting=m.groups()
                    break
            assert name and kind
            
            #lines=page.get_lines(page.get_partially_in_rect(lx+52,item.y1-0.25,100,item.y2+0.25))
            #print lines
            #assert len(lines)==1
            #lat,lon,height,elev,lighting=re.match(ur"",lines[0]).groups()
            obsts.append(
                dict(
                    name=name,
                    pos=mapper.parse_coords(lat,lon),
                    height=height,
                    elev=elev,
                    lighting=lighting,
                    kind=kind,
                    objid=objid
                     ))

    return obsts
    

      
    
    
    
if __name__=='__main__':
    obsts=fi_parse_obstacles()
    print "Obstacles:"
    for sp in obsts:
        print "Name:",sp['name']
        print "  Pos:",sp['pos']
        print "  Elev:",sp['elev']
        print "  Height:",sp['height']
        
