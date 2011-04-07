#encoding=utf8
import parse
from parse import Item,Parser
import re
import fplan.lib.mapper as mapper
from itertools import izip,chain
from datetime import datetime
import fplan.extract.miner as miner
import sys

        
def ee_parse_airfield(icao):
    spaces=[]                           
    p=Parser("/ee_%s.pdf"%(icao,),lambda x:x,country='ee')
    freqs=[]
    for nr in xrange(0,p.get_num_pages()): 
        page=p.parse_page_to_items(nr)
        if nr==0:
            #[–-]
            nameregex=ur"\s*%s\s*[-–−]\s*(.+)"%(icao,)
            print "Nameregex",nameregex
            
            nameitem,=page.get_by_regex(nameregex,re.UNICODE)
            name,=re.match(nameregex,nameitem.text,re.UNICODE).groups()
            
            coordhdg,=page.get_by_regex(ur".*ARP\s*koordinaadid.*",re.DOTALL)
            coord,=page.get_partially_in_rect(
                            coordhdg.x2+1,coordhdg.y1+0.1,100,coordhdg.y2-0.1)
            pos,=mapper.parsecoords(coord.text)
            
            elevhdg,=page.get_by_regex(ur".*Kõrgus merepinnast.*",re.DOTALL)
            elevitem,=page.get_partially_in_rect(
                            elevhdg.x2+1,elevhdg.y1+0.1,100,elevhdg.y2-0.1)
            elev,=re.match(ur"(\d+)\s*FT",elevitem.text).groups()
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
                    if freqstr!="121.500":  
                        freqs.append((lastservice.text,float(freqstr)))
                

        for ats in page.get_by_regex(ur".*ATS\s*AIRSPACE.*",re.DOTALL):
            print "Searching for AD x.x on page %d, below y=%f"%(nr,ats.y2+1),icao
            
            vlim=page.get_by_regex_in_rect(
                        ur".*Vertical\s*limits.*",
                    0,ats.y2,ats.x2,100)[0]
                
            airspaceclass=page.get_by_regex_in_rect(
                    ur".*Airspace.*classification.*",
                    0,ats.y2,100,100)[0]                     
            
            coordstr=page.get_lines(page.get_partially_in_rect(
                        ats.x2,ats.y2+0.25,100,vlim.y1-0.1))
            
            class_=page.get_by_regex_in_rect(
                        ur".*Airspace\s*classification.*",
                        0,ats.y2,100,100)[0]
            spacetype=page.get_partially_in_rect(
                    class_.x2+0.5,class_.y1+0.1,100,class_.y2-0.1)[0].text.strip()
                    
            if coordstr==['Ei ole /  NIL']:
                coordstr=[]
            if coordstr==[] and spacetype=="G":
                continue #no real ATS airspace, it's class G!

            
            print "Raw coordstr",coordstr
            spacename=coordstr[0].strip()
            limitstrs=page.get_lines(page.get_partially_in_rect(
                    vlim.x2+0.5,vlim.y1+0.1,100,airspaceclass.y1-0.1))
            print "limitstrs:",limitstrs
            for limitstr in limitstrs:  
                if limitstr.strip()==spacename.strip():
                    continue
                break
            else:
                raise Exception("No limitstr")
            
            cstr=[]
            for sub in coordstr[1:]:
                cstr.append(sub.strip().rstrip("."))
                
            points=mapper.parse_coord_str(" ".join(cstr))
            if limitstr.startswith("CTR:"):
                limitstr=limitstr[4:].strip()
            print "Limitstr",limitstr
            floor,ceiling=re.match(ur"(.*)\s*kuni\s*/\s*to\s*(.*)",limitstr).groups()
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
                elif serv=='APP':
                    servicelong="Approach"
                elif serv=='AFIS':
                    servicelong="Information"
                elif serv=='ATIS':
                    servicelong="ATIS"
                else:
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
            
    
    
def ee_parse_airfields(filtericao=None):
    icaos=[
           "EEKA",
           "EEKE",
           "EEKU",
           "EEPU",
           "EERU",
           "EETN",
           "EETU"
           ]
    ads=[]
    allspaces=[]
    for icao in icaos:
        assert len(icao)==4 and icao.isupper()
        if filtericao==None or filtericao==icao:
            ad,spaces=ee_parse_airfield(icao)
            ads.append(ad)
            allspaces.extend(spaces)
    return ads,allspaces

if __name__=='__main__':
    filter=None
    if len(sys.argv)>1:
        filter=sys.argv[1]
    ads,spaces=ee_parse_airfields(filter)
    for ad in ads:
        print "ad",ad
    for space in spaces:
        print "space",space
        