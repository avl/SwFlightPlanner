#encoding=utf8
import parse
from parse import Item
import re
import fplan.lib.mapper as mapper
from itertools import izip,chain
from datetime import datetime

def ee_parse_restrictions():
    spaces=[]
    p=parse.Parser("/ee_restricted_and_danger.pdf",lambda x: x,country='ee')
    for pagenr in xrange(p.get_num_pages()):        
        page=p.parse_page_to_items(pagenr)
        raws=list(sorted(page.get_by_regex(ur"EE[RD]\d+\s+.*"),key=lambda x:x.y1))+[None]
        if len(raws)>1:
            elevs=page.get_by_regex(ur"\d+\s*FT\s*MSL|FL\s*\d+")
            assert elevs
            elevcol=min(elev.x1 for elev in elevs)
            assert elevcol!=100
            for cur,next in izip(raws[:-1],raws[1:]):
                #if cur.text.count("Tunnus, nimi ja sivurajat"): continue #not a real airspace
                space=dict()
                if next==None:
                    y2=100
                else:
                    y2=next.y1-1.75
                name=cur.text.strip()
                space['name']=name
                

            
                areaspecprim=page.get_lines(page.get_partially_in_rect(cur.x1+0.01,cur.y2+0.05,elevcol-2,y2),
                                            fudge=.25)
                #print "areaspecprim:\n","\n".join(areaspecprim)
                areaspec=[]
                for area in areaspecprim:
                    print "area in ",area
                    area=area.replace(u"–","-")
                    if len(areaspec) and area.strip()=="": break
                    area=re.sub(ur"\w-$","",area)
                    areaspec.append(area)
                #print "Y-interval:",cur.y1,y2,"next:",next
                #print "Name:",space['name']
                #print "areaspec:",areaspec
                inp=" ".join(areaspec)
                #print inp
                #raw_input()
                
                tpoints=mapper.parse_coord_str(inp,context='estonia')
                if name.startswith("EER1"): 
                    tseaborder="592842N 0280054E - 593814N 0273721E - 593953N 0265728E - 594513N 0264327E"
                    seapoints=mapper.parse_coord_str(tseaborder)
                    cont=None      
                    points=[]
                    def close(a,b):
                        bearing,dist=mapper.bearing_and_distance(
                                    mapper.from_str(a),mapper.from_str(b))
                        #print (a,b),dist
                        return dist<1.0
                    for idx,point in enumerate(tpoints):
                        points.append(point)    
                        if close(point,seapoints[0]):
                            print "WAS CLOSE",point,seapoints[0]
                            points.extend(seapoints[1:-1])
                            for idx2,point in enumerate(tpoints[idx+1:]):
                                if close(point,seapoints[-1]):
                                    points.extend(tpoints[idx+1+idx2:])
                                    break
                            else:
                                raise Exception("Couldn't find seaborder end")
                            break                    
                    else:
                        raise Exception("Couldn't find seaborder")
                else:
                    points=tpoints
                space['points']=points
                vertitems=page.get_partially_in_rect(elevcol,cur.y1+0.05,elevcol+8,y2+1.5)
                vertspec=[]
                for v in page.get_lines(vertitems):
                    if v.strip()=="": continue
                    if v.strip().count("Lennuliiklusteeninduse AS"): 
                        continue
                    vertspec.append(v.strip())
                
                print "vertspec:",vertspec
                assert len(vertspec)==2
                ceiling,floor=vertspec
                
                if mapper.parse_elev(floor)>=9500 and mapper.parse_elev(ceiling)>=9500:
                    continue
                
                space['ceiling']=ceiling
                space['floor']=floor
                space['type']='R'
                space['freqs']=[]
                spaces.append(space)
                


    spaces.append(dict(
        name="EE TSA 1",
        ceiling="UNL",
        floor="5000 FT GND",
        points=mapper.parse_coord_str(u""" 
            594500N 0255000E – 594500N 0261800E – 
            592100N 0265800E – 591200N 0261200E – 
            591600N 0255400E – 594500N 0255000E"""),
        type="TSA",
        date=datetime(2011,03,25),
        freqs=[]))

    return spaces
    

      
    
    
    
if __name__=='__main__':
    spaces=ee_parse_restrictions()
    print "Spaces:"
    for sp in spaces:
        print "Name:",sp['name']
        print "  Points:",sp['points']
        print "  Floor:",sp['floor']
        print "  Ceil:",sp['ceiling']
        
