#encoding=utf8
import parse
from parse import Item
import re
import fplan.lib.mapper as mapper
from itertools import izip,chain
from datetime import datetime

def ep_parse_tra():
    p=parse.Parser("/_EP_ENR_2_2_2_EN.pdf",lambda x: x,country='pl')
    spaces=[]
    for pagenr in xrange(p.get_num_pages()):
        page=p.parse_page_to_items(pagenr)
        headings=list(page.get_by_regex(ur"EP (?:TSA|TRA|TFR) [\d\w]+$"))+[None]        
        for tra,next in izip(headings,headings[1:]):
            print "TRA: <%s>"%(tra.text,)
            y1=tra.y1+0.1
            if next:
                y2=next.y1-0.1
            else:
                y2=97
                

            
            for hdgcand in \
                sorted(page.get_by_regex_in_rect(ur"3",tra.x2+0.1,0,tra.x2+50,tra.y1+0.1),
                       key=lambda x:-x.y1):
                alt_x1=hdgcand.x1-3
                alt_x2=hdgcand.x1+3
                alt_y1=hdgcand.y2+0.1
                break
            else:
                raise Exception("Couldn't find heading for %s"%(tra.text,))
                
            if tra.text.count("EP TRA 01") or \
                tra.text.count("EP TRA 02"):
                y1=alt_y1
                
            o=[]
            for line in page.get_lines(page.get_partially_in_rect(
                                            tra.x2+0.1,y1,tra.x2+10,y2)):
                line=line.strip()
                if line.count("Vistula"): continue
                if line.count("River"): continue       
                if line.count(u"granicy"): continue         
                if line.count(u"EPWW"): continue         
                print "Stripped line:",line
                if line.count("AIRAC"):
                    break
                if line=="":break
                o.append(line)
            print "output:",o
            if len(o)==0: continue
            altcand=[]
            for alt in page.get_lines(page.get_partially_in_rect(
                                            alt_x1,y1,alt_x2,y2)):
                if alt=="": break
                altcand.append(alt)
            print altcand
            h1,h2=altcand
            def fixupalt(x):
                print "Fixing",x
                fl,alt,gnd,unl=re.match(ur"(?:(FL\d+)|\d+\s*m\s*\((\d+)\s*ft\)|(GND)|(UNL))",x).groups()
                if fl: return fl
                if alt: return alt+"FT MSL"
                if gnd: return "GND"
                if unl: return "UNL"
            ceiling,floor=[fixupalt(h) for h in [h1,h2]]
            if mapper.parse_elev(floor)>=9500:
                continue
            kind,name=re.match("EP (TSA|TRA|TFR) ([\d\w]+)",tra.text).groups()            
            def fix_coords(s):
                
                def fixer(m):
                    a,b,c,d, e,f,g,h=m.groups()
                    return "%02d%02d%02d%s %03d%02d%02d%s - "%(int(a),int(b),int(c),d,
                                                               int(e),int(f),int(g),h)
                return re.sub(ur"(\d{2,3})°(\d{2})'(\d{2})''([NS])\s*(\d{2,3})°(\d{2})'(\d{2})''([EW])",fixer,s)
            coordstr2=fix_coords("".join(o)).rstrip().rstrip("-")
            print "COordstr:",coordstr2
            spaces.append(dict(
                name="EF %s %s"%(kind,name),
                points=mapper.parse_coord_str(coordstr2,context="poland"),
                ceiling=ceiling,
                floor=floor,
                type="TSA",
                freqs=[]
                    ))
    return spaces
if __name__=='__main__':
    for space in ep_parse_tra():
        print "space",space
        
    