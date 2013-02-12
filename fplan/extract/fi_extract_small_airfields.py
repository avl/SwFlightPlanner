#encoding=utf8
import parse
from parse import Item
import re
import sys
import fplan.lib.mapper as mapper
from fplan.lib.mapper import uprint
import fplan.extract.rwy_constructor as rwy_constructor

def fi_parse_small_airfields(only=None):
    p=parse.Parser("/ais/vfr/pdf/aerodromes.pdf",lambda x: x,country="fi")
    ads=dict()
    for pagenr in xrange(p.get_num_pages()):
        page=p.parse_page_to_items(pagenr)
        if not page: continue
        lines=page.get_lines(page.get_partially_in_rect(0,0,100,15))
        heading=lines[0].strip()
        if pagenr<4 and not heading[-4:-2]=="EF": continue #this is one of the first pages, with general info, not an airport sheet
        #print heading
        name,icao=re.match(ur"(.*),\s*Finland\s*(EF[A-Z]{2})",heading).groups()
        name=name.strip()
        ad=ads.setdefault(icao,dict())
        ad['name']=name
        ad['icao']=icao
        #print "Name: <%s> <%s>"%(icao,name)
        if only!=None and only!=icao: continue
        for item in page.get_by_regex(ur"1.*ARP.*sijainti.*location"):
            posline=page.get_lines(page.get_partially_in_rect(0,item.y2+0.05,100,item.y2+5))[0]
            print "Posline:",posline
            lat,lon=re.match(ur"(\d{6}N) (\d{7}E).*",posline).groups()
            ad['pos']=mapper.parse_coords(lat.replace(" ",""),lon.replace(" ",""))

        for item in page.get_by_regex(ur"FREQ MHZ"):
            freqline=page.get_lines(page.get_partially_in_rect(item.x1,item.y2+0.05,item.x2+20,item.y2+5))[0]
            print "Freqline:",freqline
            freq,=re.match(ur"(\d{3}\.\d{3}).*",freqline).groups()
            ad['freq']=float(freq)
        for item in page.get_by_regex(ur"ELEV FT \(M\)"):
            elevline=page.get_lines(page.get_partially_in_rect(item.x1,item.y2+0.05,item.x2+20,item.y2+5))[0]
            print "elevline:",elevline
            elev,=re.match(ur"(\d+)\s*\(\d+\)",elevline).groups()
            ad['elev']=int(elev)


    for icao,ad in ads.items():
        assert ad['icao']==icao
        assert 'pos' in ad

    return ads.values()
    
if __name__=='__main__':
    if len(sys.argv)==2:
        icaolimit=sys.argv[1]
    else:
        icaolimit=None
    ads=fi_parse_small_airfields(icaolimit)
    for ad in ads:
        uprint( "Name: ",ad['name'])
        uprint( "  Other:",ad)
        
        
