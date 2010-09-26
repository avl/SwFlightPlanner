#encoding=utf8
import parse
from parse import Item
import re
import fplan.lib.mapper as mapper
from itertools import izip

def fi_parse_restrictions():
    spaces=[]
    p=parse.Parser("/fi/EF_ENR_5_1_EN.pdf",lambda x: x)
    for pagenr in xrange(p.get_num_pages()):        
        page=p.parse_page_to_items(pagenr)
        raws=list(sorted(page.get_by_regex(ur"(?:EF [PRD]\d+[A-Z]{0,2} .*)|(?:.*Tunnus, nimi ja sivurajat.*)"),key=lambda x:x.y1))+[None]
        for cur,next in izip(raws[:-1],raws[1:]):
            if cur.text.count("Tunnus, nimi ja sivurajat"): continue #not a real airspace
            space=dict()
            if next==None:
                y2=100
            else:
                y2=next.y1-1.75
            name=cur.text.strip()
            space['name']=name
            if name.startswith("EF R28"):
                continue #This airspace is special, and not supported now (it's the no-mans-land-zone on border to russia!)
        
            areaspecprim=page.get_lines(page.get_partially_in_rect(cur.x1+0.01,cur.y2+0.05,cur.x1+50,y2))
            areaspec=[]
            for area in areaspecprim:
                if len(areaspec) and area.strip()=="": break
                areaspec.append(area)
            print "Y-interval:",cur.y1,y2,"next:",next
            print "Name:",space['name']
            print "areaspec:",areaspec
            space['points']=mapper.parse_coord_str("".join(areaspec))
            vertitems=page.get_partially_in_rect(cur.x1+55,cur.y1+0.05,cur.x1+70,y2+1.5)
            vertspec=page.get_lines(vertitems)
            print vertitems
            assert len(vertspec)==2
            ceiling,floor=vertspec
            space['ceiling']=ceiling
            space['floor']=floor
            space['type']='R'
            space['freqs']=[]
            spaces.append(space)
            

    return spaces
    

      
    
    
    
if __name__=='__main__':
    spaces=fi_parse_restrictions()
    print "Spaces:"
    for sp in spaces:
        print "Name:",sp['name']
        print "  Points:",sp['points']
        print "  Floor:",sp['floor']
        print "  Ceil:",sp['ceiling']
        
