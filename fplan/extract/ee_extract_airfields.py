#encoding=utf8
import parse
from parse import Item
import re
import sys
import fplan.lib.mapper as mapper
from fplan.lib.mapper import uprint
import fplan.extract.rwy_constructor as rwy_constructor
from itertools import izip

def ee_parse_airfield(icao=None):
    spaces=[]
    ad=dict()
    ad['icao']=icao
    sigpoints=[]
    p=parse.Parser("/ee_%s.pdf"%(icao,),lambda x: x,country="ee")

    page=p.parse_page_to_items(0)
    print icao
    nameregex=ur".*%s\s*[-−]\s*([A-ZÅÄÖ\- ]{3,})"%(icao,)
    for item in page.get_by_regex(nameregex):
        print "fontsize:",item.fontsize        
        assert item.fontsize>=10
        ad['name']=re.match(nameregex,item.text).groups()[0].strip()
        break
    else:
        raise Exception("Found no airfield name!")
    
    for item in page.get_by_regex(ur".*Kõrgus merepinnast.*"):
        lines=page.get_lines(page.get_partially_in_rect(0,item.y1+0.1,100,item.y2-0.1))
        for line in lines:
            ft,=re.match(".*?([\d\.]+)\s*FT\.*",line).groups()
            assert not 'elev' in ad
            print "parsed ft:",ft
            ad['elev']=float(ft)
        

        
    for item in page.get_by_regex(ur"ARP koordinaadid"):
        lines=page.get_lines(page.get_partially_in_rect(item.x1,item.y1,100,item.y2))        
        for line in lines:
            print line
            for crd in mapper.parsecoords(line):
                assert not ('pos' in ad)
                ad['pos']=crd
                break
            else:
                raise Exception("No coords")
    ad['runways']=[]
    thrs=[]
    freqs=[]
    for pagenr in xrange(p.get_num_pages()):
        page=p.parse_page_to_items(pagenr)
        print "Parsing page",pagenr
        for item in page.get_by_regex("\s*RUNWAY\s*PHYSICAL\s*CHARACTERISTICS\s*"):
            print "Phys char"
            
            coords,=page.get_by_regex_in_rect("RWY end coordinates",0,item.y2,100,100) 

            design,=page.get_by_regex_in_rect("Designations",0,item.y2,100,100)
            
            lines=page.get_lines(page.get_partially_in_rect(0,design.y2,design.x2,100))
            print "Design",lines
            rwys=[]
            for line in lines:
                m=re.match("(\d{2})",line)
                if m:
                    print "rwynum",line
                    rwys.append((m.groups()[0],line.y1))
            rwys.append((None,100))
            for (rwy,y),(nextrwy,nexty) in izip(rwys,rwys[1:]):
                lines=page.get_lines(page.get_partially_in_rect(coords.x1,y,coords.x2,nexty-0.5))
                lines=[line for line in lines if line.strip()]
                print "Lines for rwy",lines
                thrlat,thrlon,endlat,endlon,undulation=lines[:5]
                assert undulation.count("GUND")
                
                thrs.append(dict(pos=mapper.parse_coords(thrlat,thrlon),thr=rwy))
            print thrs
            
    if 0:
            
            
        for item in page.get_by_regex("ATS AIRSPACE"):
            lines=iter(page.get_lines(page.get_partially_in_rect(0,item.y2+0.1,100,100)))
            spaces=[]
            while True:
                line=lines.next()
                #print "Read line:",line
                if line.count("Vertical limits"):
                    break                            
                m=re.match(ur".*?/\s+Designation and lateral limits\s*(.*\b(?:CTR|FIZ)\b.*?)\s*:?\s*$",line)
                if not m:
                    m=re.match(ur"\s*(.*\b(?:CTR|FIZ)\b.*?)\s*:",line)
                    #print "Second try:",m
                    
                spacename,=m.groups()
                #print "Got spacename:",spacename
                assert spacename.strip()!=""
                coords=[]
                while True:
                    line=lines.next()
                    #print "Further:",line
                    if line.count("Vertical limits"):
                        break                            
                    if not re.search(ur"[\d ]+N\s*[\d ]+E",line) and  \
                        not re.search(ur"circle|cent[red]{1,5}|pitkin|point",line):
                        break
                    coords.append(line)
                    
                areaspec="".join(coords)
                def fixup(m):
                    lat,lon=m.groups()
                    return lat.replace(" ","")+" "+lon.replace(" ","")
                areaspec=re.sub(ur"([\d ]+N)\s*([\d ]+E)",fixup,areaspec)
                #print "Fixed areaspec",areaspec
                #if icao=="EFKS":
                #    areaspec=areaspec.replace("6615 28N","661528N")
#Error! REstriction areas!
                spaces.append(dict(
                    name=spacename,
                    type="CTR",
                    points=mapper.parse_coord_str(areaspec)))
                if line.count("Vertical limits"):
                    #print "Breaking"
                    break                            
            while not line.count("Vertical limits"):
                line=lines.next()
            #print "Matching veritcal limits--------------------------------"
            oldspaces=spaces
            spaces=[]
            for space in oldspaces:
                if space['name'].count("/"):
                    a,b=space['name'].split("/")
                    spaces.append(dict(space,name=a.strip()))
                    spaces.append(dict(space,name=b.strip()))
                else:
                    spaces.append(space)
            missing=set([space['name'] for space in spaces])
            while True:
                for space in spaces:
                    #print "Matching ",space['name']," to ",line,"missing:",missing
                    for it in xrange(2):  
                        cand=space['name']
                        if it==1:
                            if cand.count("CTR"):
                                cand="CTR"
                            if cand.count("FIZ"):
                                cand="FIZ"
                        m=re.match(ur".*%s\s*:([^,:-]*)\s*-\s*([^,:-]*)"%(cand,),line)
                        if m: break
                    if len(spaces)==1 and not m:                        
                        m=re.match(ur".*Vertical limits\s*(.*)\s*-\s*(.*)",line)                        
                    if m:
                        for lim in m.groups():
                            assert lim.count(",")==0
                        space['floor'],space['ceiling']=m.groups()
                        missing.remove(space['name'])
                    #print "Missing:"
                    if len(missing)==0: break
                if len(missing)==0: break
                line=lines.next()
            
        print "Parse f o n page",pagenr      
        for item2 in page.get_by_regex(ur".*ATS\s*COMMUNICATION\s*FACILITIES.*"):
            lines=page.get_lines(page.get_partially_in_rect(0,item2.y2+0.1,100,100))
            for line in lines:
                if line.count("RADIO NAVIGATION AND LANDING AIDS"): break
                print "Comm line:",line
                twr=re.match(ur"TWR.*(\d{3}\.\d{3})\b.*",line)
                if twr:
                    freqs.append(('TWR',float(twr.groups()[0]))) 
                atis=re.match(ur"ATIS.*(\d{3}\.\d{3})",line)
                if atis:
                    freqs.append(('ATIS',float(atis.groups()[0])))
    for space in spaces:
        space['freqs']=freqs
    ad['runways'].extend(rwy_constructor.get_rwys(thrs))
    ad['freqs']=freqs
                             
    #print ad
    return ad,spaces,sigpoints
    

      
    
    
    
    
def ee_parse_airfields(onlyicao=None):
    icaolist=['EETN','EEKE','EEPU','EEKA']
                
    ads=[]
    adspaces=[]
    points=[]
    for icao in icaolist:
        if onlyicao!=None and icao!=onlyicao: continue
        ad,adspace,sigpoints=ee_parse_airfield(icao)
        ads.append(ad)
        points.append(sigpoints)
        adspaces.extend(adspace)
    return ads,adspaces,points
    
    
    
    
if __name__=='__main__':
    if len(sys.argv)==2:
        icaolimit=sys.argv[1]
    else:
        icaolimit=None
    ads,spaces,points=ee_parse_airfields(icaolimit)
    uprint("Spaces:")
    for p in points:
        uprint("Point: %s"%(p,))
    for sp in spaces:
        uprint( "Name:",sp['name'])
        uprint( "  Points:",sp['points'])
        uprint( "  Floor:",sp['floor'])
        uprint( "  Ceiling:",sp['ceiling'])
        uprint( "  Freqs:",sp['freqs'])
    for ad in ads:
        uprint( "Name: ",ad['name'])
        uprint( "  Other:",ad)
        
        
