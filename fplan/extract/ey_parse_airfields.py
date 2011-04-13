#encoding=utf8
import parse
from parse import Item,Parser
import re
import fplan.lib.mapper as mapper
from itertools import izip,chain
from datetime import datetime
import fplan.extract.miner as miner
import sys

def fixup(s):
    def fixfunc(m):
        return "".join(m.groups())
    return re.sub(ur"(\d{2,3})\s*(\d{2})\s*(\d{2})\s*([NSEW])",
                                                 fixfunc,
                                                 s)

def ey_parse_airfield(icao):
    spaces=[]                           
    p=Parser("/EY_AD_2_%s_en.pdf"%(icao,),lambda x:x)
    freqs=[]
    for nr in xrange(0,p.get_num_pages()): 
        page=p.parse_page_to_items(nr)
        if nr==0:
            #[–-]
            nameregex=ur"\s*%s\s*[–-]\s*(.*?)\s*$"%(icao,)
            print "Nameregex",nameregex            
            nameitem=page.get_by_regex(nameregex,re.UNICODE)[0]            
            name,=re.match(nameregex,nameitem.text,re.UNICODE).groups()
            name=name.replace("Tarptautinis","International")
            #print repr(name)
            #sys.exit(1)
            coordhdg,=page.get_by_regex(ur".*ARP\s*koordinat.s.*",re.DOTALL)
            coord=page.get_partially_in_rect(
                            coordhdg.x2+4,coordhdg.y1+0.1,100,coordhdg.y2-0.1)[0]
            pos,=mapper.parsecoords(fixup(coord.text.replace(" ","")))
            
            elevhdg,=page.get_by_regex(ur".*Vietos\s*aukštis.*",re.DOTALL)
            elevitem,=page.get_partially_in_rect(
                            elevhdg.x2+1,elevhdg.y1+0.1,100,elevhdg.y2-0.1)
            elev,=re.match(ur"(\d+)\s*FT.*",elevitem.text).groups()
            elev=int(elev)
                        
    
        for comm in page.get_by_regex(ur".*ATS\s*COMMUNICATION\s*FACILITIES.*",re.DOTALL):
            ends=page.get_by_regex_in_rect(
                        ur".*RADIO\s*NAVIGATION.*",
                        0,comm.y2,100,100)
            if ends:
                end=ends[0].y1-0.1
            else:
                end=100
            freqitems=page.get_by_regex_in_rect(
                        ur".*\d{3}\.\d{3}.*",
                    0,comm.y2,100,end-0.1)
            lastservice=None
            for freq in freqitems:
                service=page.get_partially_in_rect(
                    0,freq.y1+0.1,17,freq.y2-0.1)
                if service:
                    lastservice=service[0]
                print lastservice
                assert len(spaces)==0
                for freqstr in re.findall(ur"\d{3}\.\d{3}",freq.text):
                    if freqstr!="121.500" and freqstr!="243.000":
                        freqs.append((lastservice.text.split("/")[0],float(freqstr)))
                
    for nr in xrange(0,p.get_num_pages()): 
        page=p.parse_page_to_items(nr)

        for ats in page.get_by_regex(ur".*ATS\s*AIRSPACE.*",re.DOTALL):
            print "Searching for AD x.x on page %d, below y=%f"%(nr,ats.y2+1),icao
            
            vlim=page.get_by_regex_in_rect(
                        ur".*Vertikalios\s*ribos.*",
                    0,ats.y2,ats.x2,100)[0]
                
            airspaceclass=page.get_by_regex_in_rect(
                    ur".*Erdvės\s*klasifikacija.*",
                    0,ats.y2,100,100)[0]                     
            
            desig=page.get_by_regex_in_rect(
                    ur"CTR",
                    0,ats.y2,100,vlim.y1)[0]                     
                        
            
            coordstr=page.get_lines(page.get_partially_in_rect(
                        desig.x1,ats.y2+0.25,100,vlim.y1-0.1))
            
            spacetype=page.get_partially_in_rect(
                    airspaceclass.x2+0.5,airspaceclass.y1+0.1,100,airspaceclass.y2-0.1)[0].text.strip()
                    
            if coordstr==[] and spacetype=="G":
                continue #no real ATS airspace, it's class G!

                        
            #print "Raw coordstr",coordstr
            spacename=coordstr[0].strip()
            limitstrs=page.get_lines(page.get_partially_in_rect(
                    vlim.x2+0.5,vlim.y1+0.1,100,airspaceclass.y1-0.1))
            #print "limitstrs:",limitstrs
            for limitstr in limitstrs:  
                if limitstr.strip()==spacename.strip():
                    continue
                break
            else:
                raise Exception("No limitstr")
            
            cstr=[]
            spacename=coordstr[0]
            assert spacename=="CTR"
            for sub in coordstr[1:]:
                cstr.append(sub.strip().rstrip("."))
            def fixfunc(m):
                return "".join(m.groups())
            raw=re.sub(ur"(\d{2,3})\s*(\d{2})\s*(\d{2})\s*([NSEW])",
                                                 fixfunc,
                                                 "".join(cstr)).replace(","," - ")
            print "parsing raw:",raw
            points=mapper.parse_coord_str(raw,context='lithuania')
                                                 
            print "Limitstr",limitstr
            floor,ceiling=re.match(ur"(.*)\s*to\s*(.*)",limitstr).groups()
            mapper.parse_elev(floor)
            mapper.parse_elev(ceiling)
            
            spacenamestem=spacename.strip()
            if spacenamestem.endswith("CTR"):
                spacenamestem=spacenamestem[:-3].strip()
            if spacenamestem.endswith("FIZ"):
                spacenamestem=spacenamestem[:-3].strip()
            #construct names
            newfreqs=[]
            for serv,freq in freqs:
                serv=serv.strip()
                if serv=='TWR':
                    servicelong="Tower"
                elif serv.startswith('APP'):
                    servicelong="Approach"
                elif serv=='AFIS':
                    servicelong="Information"
                elif serv=='ATIS':
                    servicelong="ATIS"
                else:
                    print "serv:",serv
                    raise Exception("No translation for service name found")
                
                newfreqs.append((spacenamestem+" "+servicelong,freq))
            
            if len(points)>0:
                spaces.append(
                    dict(
                         name=spacename,
                         points=points,
                         type="CTR",
                         ceiling=ceiling,
                         floor=floor,
                         freqs=newfreqs,
                        ))
                        
                                       


            #not first page:
    return dict(
        name=name,
        pos=pos,
        icao=icao,
        elev=elev,
        ),spaces
            
    

def ey_parse_airfields():
    ads=[]
    spaces=[]
    for icao in ['EYKA',
                'EYVI',
                'EYPA',
                'EYSA']:
        ad,adspaces=ey_parse_airfield(icao)
        ads.append(ad)
        spaces.extend(adspaces)
    return ads,spaces

    
if __name__=='__main__':
    for ad in ey_parse_airfields():
        print ad
        
    
