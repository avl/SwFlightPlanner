#encoding=utf8
import parse
from parse import Item
import re
import fplan.lib.mapper as mapper
from itertools import izip,chain
from datetime import datetime
import fplan.extract.miner as miner
import sys
from ep_parse_tma import fixup
import lxml
import lxml.html
from fplan.extract.html_helper import alltext,alltexts
import fplan.extract.fetchdata as fetchdata

def extract_ft(alt):
    m=re.match(ur".*\((\d+ FT)\)\s*",alt,re.IGNORECASE)
    if m:
        return m.groups()[0]
    return alt
        
def pairwise(xs):
    it=iter(xs)
    while True:
        a=next(it)
        try:
            b=next(it)
        except StopIteration:
            raise Exception("Not an even number of elements, left with single: %s"%(a,))
        yield a,b

def ep_parse_airfield(icao):
    spaces=[]
    pages,date=miner.parse("/aip/openp.php?id=EP_AD_2_%s_en"%(icao,),
                           maxcacheage=86400*7,
                           country='ep',usecache=True)
    print "parsing ",icao,date
    points=None
    ctrname=None
    freqs=[]
    for nr,page in enumerate(pages):        
        if nr==0:
            def filter_tiny(its):
                for it in its:
                    print "Filtering:",repr(it)
                    print "size %f of <%s>."%(it.y2-it.y1,it.text)
                    textsize=it.y2-it.y1
                    if textsize>0.4:
                        yield it
            namehdg,=page.get_by_regex(ur".*AERODROME\s+LOCATION\s+INDICATOR\s+AND\s+NAME.*",re.DOTALL)
            subs=page.get_partially_in_rect(
                            0,namehdg.y1+0.5,100,namehdg.y2+2.5)
            allsubs=[]
            for sub in subs:
                print "Item:",repr(sub)
                print "sub",repr(sub.subs)
                allsubs.extend(sub.subs)
            print "allsubs",allsubs
            lineobjs=list(filter_tiny(allsubs))
            for lineobj in lineobjs:
                line=lineobj.text.strip()
                print "line:",line
                if line==icao: continue
                if re.match(ur".*AERODROME\s*LOCATION\s*INDICATOR.*",line): continue
                if re.match(ur".*WSKAŹNIK\s*LOKALIZACJI\s*LOTNISKA\s*I\s*NAZWA.*",line): continue                
                m=re.match(ur"%s\s*[-]\s*([\w\s/]+)"%(icao,),line,re.UNICODE|re.DOTALL)
                name,=m.groups()
                name=name.strip()
                break
            else:
                raise Exception("No name found!")
            print "Name:",name
            site,=page.get_by_regex(ur"ARP\s*-\s*WGS-84\s*coordinates\s*and\s*site\s*at\s*AD")
            print "site:",repr(site.text.strip())
            splat=site.text.strip().split("\n")
            print "splat:",splat
            print len(splat)
            poss=splat[1:]
            print "rawpos,",poss
            for line in poss:
                m=re.match(ur"(\d+)°(\d+)'(\d+)''(N)\s*(\d+)°(\d+)'(\d+)''(E).*",line)
                if m:
                    pos=mapper.parsecoord("".join(m.groups()))
                    break
            else:
                raise Exception("No pos found")
            
            elevi,=page.get_by_regex(ur"\s*Elevation/Reference\s*temperature\s*",re.DOTALL)
            elevft,=re.match(ur".*\d+\s+m\s*\((\d+)\s+ft\).*",elevi.text,re.DOTALL).groups()
            elev=float(elevft)
            
            
        
        for ats in page.get_by_regex(ur".*AIR\s*TRAFFIC\s*SERVICES\s*AIRSPACE.*",re.DOTALL):
            print "Searching for AD x.x on page %d, below y=%f"%(nr,ats.y2+1),icao
            enditems=page.get_by_regex_in_rect(ur".*AD\s*\d+\.\d+.*",
                        0,ats.y2+1,20,100,re.DOTALL)
            if len(enditems)>0:
                enditem_y1=enditems[0].y1
            else:
                if ats.y2>40:
                    enditem_y1=100
                else:
                    raise Exception("Missing enditem")
                    
            desighdr,=page.get_by_regex_in_rect(".*Airspace\s*designation\s*and\s*geographical\s*coordinates.*",
                            0,ats.y1,100,enditem_y1-1,re.DOTALL)
            verthdr,=page.get_by_regex_in_rect(".*Vertical\s*limits.*",
                            desighdr.x2,desighdr.y1,100,desighdr.y2,re.DOTALL)
            callsign,=page.get_by_regex_in_rect(".*call\s*sign.*",
                            verthdr.x2,desighdr.y1,100,desighdr.y2,re.DOTALL)
            
            coords=[]
            last=None
            seenreal=False
            ceiling=None
            floor=None
            for vlim in page.get_partially_in_rect(
                            verthdr.x1,verthdr.y2+0.5,verthdr.x2,enditem_y1-1):
                if vlim.text.strip()=='2': continue
                print "Vlimtext:",repr(vlim.text)
                ceilstr,floorstr=vlim.text.strip().split("\n")
                print "ceilstr",ceilstr
                print "floorstr",floorstr
                assert ceiling==None
                ceiling,=mapper.parse_all_alts(extract_ft(ceilstr))
                ceiling=mapper.altformat(*ceiling)
                assert floor==None
                floor,=mapper.parse_all_alts(extract_ft(floorstr))
                floor=mapper.altformat(*floor)
                break
            
            callsignlines=[]
            for x in page.get_lines2(page.get_partially_in_rect(
                            callsign.x1,callsign.y2+0.5,callsign.x2,enditem_y1-1)):
                t=x.strip()
                if t=="":continue
                if t=="4":continue
                if t=="Remarks": break
                callsignlines.append(t)
            for entity,lang in pairwise(callsignlines):
                print "entity,lang",repr((entity,lang))
                if lang=="PL": continue
                assert lang=="EN"
                servname,freq=re.match(ur"(.*?)\s*\((\d{3}\.\d{3})\s*MHz\)",entity).groups()
                if freq=="121.500":
                    continue
                freqs.append((servname,float(freq)))
                
                
            
            for desig in page.get_partially_in_rect(
                            0,desighdr.y2+0.5,desighdr.x2,enditem_y1-1):
                print "desig:",repr(desig.subs)
                
                for sub in desig.subs:
                    if last:
                        delta=sub.y1-last.y2
                        print "delta",delta
                        if delta>1:
                            break
                    text=sub.text.strip()
                    if not re.match(ur"\d+°\d+",sub.text):
                        print "Coord part:",text
                        if text.strip()=="1":
                            continue
                        if not seenreal and text.endswith("CTR"):
                            ctrname=text.split("/")[-1].strip()
                            continue
                        if not seenreal and re.match(ur".*The\s*line\s*joining.*",text):
                            continue
                        if not seenreal and text.endswith("following points:"):
                            continue
                        if not seenreal and text=="points:":
                            continue
                    if text.endswith("E"):
                        text=text+" - "
                    seenreal=True
                    coords.append(text)
                    last=sub
                pass
            assert points==None
            coordstr=fixup(" ".join(coords))
            print "Raw coords:",coordstr
            points=mapper.parse_coord_str(coordstr)
            assert ceiling
            assert floor
            assert ctrname
            spaces.append(
                dict(
                     name=ctrname,
                     points=points,
                     type="CTR",
                     ceiling=ceiling,
                     floor=floor,
                     freqs=freqs
                    ))
                        
                                       


            #not first page:
    assert points!=None
    return dict(
        name=name,
        pos=pos,
        icao=icao,
        elev=elev,
        ),spaces
            
def ep_parse_wikipedia_airports(url):
    parser=lxml.html.HTMLParser()
    data,date=fetchdata.getdata(url,country="wikipedia")
    parser.feed(data)
    tree=parser.close()
    res=[]
    for table in tree.xpath("//table"):
        for nr,row in enumerate(table.xpath(".//tr")):
            cols=list([alltext(x) for x in row.xpath(".//td")])
            print "#",nr,": ",cols
            if nr==0:                
                if len(cols)==0 or cols[0].strip()!="Airport":
                    break
                assert cols[3].strip()=="ICAO"
                assert cols[4].strip()=="Purpose"
                assert cols[5].strip().count("El")
                assert cols[9].strip()=="Coordinates"
            else:
                purpose=cols[4].strip()
                if purpose.count("Unused"):continue
                if purpose.count("Closed"):continue
                if purpose.count("Liquidated"): continue
                if purpose=="Military": continue #Just military
                icao=cols[3].strip()
                if icao=="": icao="ZZZZ"
                name=cols[0].strip()
                #print "lats:",row.xpath(".//span[@class='latitude']")
                lat,=alltexts(row.xpath(".//span[@class='latitude']"))
                lon,=alltexts(row.xpath(".//span[@class='longitude']"))
                coords=fixup(lat.strip()+" "+lon.strip())
                elevft=float(cols[5].strip())
                res.append(dict(
                                pos=mapper.parsecoord(coords),
                                name=name,
                                elev=elevft/0.3048,
                                icao=icao,
                                date=date,
                                url=url
                                ))
                
                
            
    return res
    
def ep_parse_airfields(filtericao=None):
    pages,date=miner.parse("/aip/openp.php?id=EP_AD_1_en",
                           maxcacheage=86400*7,
                           country='ep',usecache=True)
    icaos=[]
    print "Nr pages:",len(pages)
    for nr,page in enumerate(pages):
        for item in page.get_by_regex(ur".*\bICAO\s*CODE\b.*"):
            print "Icao",item
            for icaoitem in page.get_partially_in_rect(item.x1,item.y1+0.1,item.x2,100):
                for icao in re.findall(ur"\b(EP[A-Z]{2})\b",icaoitem.text):                        
                    assert len(icao)==4
                    icaos.append(icao)
        
    ads=[]
    tempads=[]
    tempads.extend(ep_parse_wikipedia_airports(
            "/wiki/Airports_in_Poland_with_unpaved_runways"))
    tempads.extend(ep_parse_wikipedia_airports(
            "/wiki/Airports_in_Poland_with_paved_runways"))
        
    seen=set()
    
    allspaces=[]
    for icao in icaos:
        assert len(icao)==4 and icao.isupper()
        if filtericao==None or filtericao==icao:
            ad,spaces=ep_parse_airfield(icao)
            ads.append(ad)
            seen.add(ad['icao'])
            allspaces.extend(spaces)
            
    for ad in tempads:
        if ad['icao']!='ZZZZ' and ad['icao'] in seen:
            continue
        seen.add(ad['icao'])
        ads.append(ad)
            
    return ads,allspaces

if __name__=='__main__':
    filter=None
    if len(sys.argv)>1:
        filter=sys.argv[1]
    ads,spaces=ep_parse_airfields(filter)
    for ad in ads:
        print "ad",ad
    for space in spaces:
        print "space",space
    for space in spaces:
        print space['name'],space['floor'],space['ceiling']