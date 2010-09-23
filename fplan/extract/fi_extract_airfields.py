#encoding=utf8
import parse
from parse import Item
import re
import fplan.lib.mapper as mapper

def fi_parse_airfield(icao):
    spaces=[]
    ad=dict()
    ad['freqs']=[]
    p=parse.Parser("/fi/EF_AD_2_%s_EN.pdf"%(icao,),lambda x: x)
    page=p.parse_page_to_items(0)
    nameregex=ur"%s\s+-\s+([A-ZÅÄÖ ]{3,})"%(icao,)
    for item in page.get_by_regex(nameregex):
        print "fontsize:",item.fontsize
        assert item.fontsize>=14
        ad['name']=re.match(nameregex,item.text).groups()[0].strip()
        break
    for item in page.get_by_regex(ur"Mittapisteen.*sijainti"):
        lines=page.get_lines(page.get_partially_in_rect(item.x1,item.y1,100,item.y2))        
        for line in lines:
            for crd in mapper.parsecoords(line):
                assert not ('pos' in ad)
                ad['pos']=crd
    for pagenr in xrange(p.get_num_pages()):
        page=p.parse_page_to_items(pagenr)
        for item in page.get_by_regex("ATS AIRSPACE"):
            lines=page.get_lines(page.get_partially_in_rect(0,item.y2+0.1,100,100))                       
            line1=lines[0]
            spacename,=re.match(ur".*?/\s+Designation and lateral limits\s*(.* CTR):",line1).groups()
            rest=lines[1:]
            ctrlines=[]
            for line in rest:
                if line.count("Vertical limits"):
                    print line
                    floor,ceiling=re.match(ur".*?/\s+Vertical limits\s*(SFC)\s*-\s*(.*)",line).groups()
                    break
                ctrlines.append(line.strip())
            points=mapper.parse_coord_str("".join(ctrlines))
            freqs=[]      
            for item2 in page.get_by_regex("ATS COMMUNICATION FACILITIES"):
                lines=page.get_lines(page.get_partially_in_rect(0,item2.y2+0.1,100,100))
                for line in lines:
                    if line.count("RADIO NAVIGATION AND LANDING AIDS"): break
                    twr=re.match(ur"TWR.*(\d{3}\.\d{3})",line)
                    if twr:
                        freqs.append(('TWR',twr.groups()[0]))  
                    atis=re.match(ur"ATIS.*(\d{3}\.\d{3})",line)
                    if atis:
                        freqs.append(('ATIS',atis.groups()[0]))
            spaces.append(dict(
                name=spacename,points=points,
                floor=floor,ceiling=ceiling,freqs=freqs))
                             
    print ad
    return ad,spaces
    

      
    
    
    
    
def fi_parse_all_airfields():
    icaolist=["EFMA","EFTU"]
    ads=[]
    adspaces=[]
    for icao in icaolist:
        ad,adspace=fi_parse_airfield(icao)
        ads.append(ad)
        adspaces.extend(adspace)
    return ads,adspaces
    
    
    
    
if __name__=='__main__':
    ads,spaces=fi_parse_all_airfields()
    print "Spaces:"
    for sp in spaces:
        print "Name:",sp['name']
        print "  Points:",sp['points']
        print "  Floor:",sp['floor']
        print "  Ceiling:",sp['ceiling']
        print "  Freqs:",sp['freqs']
    for ad in ads:
        print "Name: ",ad['name']
        print "  Other:",ad
        
        
