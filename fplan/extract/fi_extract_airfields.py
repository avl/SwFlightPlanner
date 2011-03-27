#encoding=utf8
import parse
from parse import Item
import re
import sys
import fplan.lib.mapper as mapper
from fplan.lib.mapper import uprint
import fplan.extract.rwy_constructor as rwy_constructor

def fi_parse_airfield(icao=None):
    spaces=[]
    ad=dict()
    ad['icao']=icao
    sigpoints=[]
    #https://ais.fi/ais/eaip/pdf/aerodromes/EF_AD_2_EFET_EN.pdf
    #https://ais.fi/ais/eaip/aipcharts/efet/EF_AD_2_EFET_VAC.pdf
    #vacp=parse.Parser("/ais/eaip/aipcharts/%s/EF_AD_2_%s_VAC.pdf"%(icao.lower(),icao),lambda x: x,country="fi")
    p=parse.Parser("/ais/eaip/pdf/aerodromes/EF_AD_2_%s_EN.pdf"%(icao,),lambda x: x,country="fi")


    #The following doesn't actually work, since finnish VAC are bitmaps!!! :-(
    if 0:
        vacpage=vacp.parse_page_to_items(0)
        repp=vacpage.get_by_regex("\s*REPORTING\s*POINTS\s*")
        assert len(repp)>0
        for item in repp:    
            lines=iter(page.get_lines(page.get_partially_in_rect(item.x1,item.y2+0.1,100,100)))
            for line in lines:
                uprint("Looking for reporting points:%s"%(line,))
                name,lat,lon=re.match(ur"([A-ZÅÄÖ\s ]{3,})\s*([ \d]+N)\s*([ \d]+E).*",line)
                sigpoints.append(dict(
                    name=icao+" "+name.strip(),
                    kind="reporting",
                    pos=mapper.parse_coords(lat.replace(" ",""),lon.replace(" ",""))))


    page=p.parse_page_to_items(0)
    nameregex=ur"%s\s+-\s+([A-ZÅÄÖ\- ]{3,})"%(icao,)
    for item in page.get_by_regex(nameregex):
        #print "fontsize:",item.fontsize
        assert item.fontsize>=14
        ad['name']=re.match(nameregex,item.text).groups()[0].strip()
        break
    for item in page.get_by_regex(ur".*ELEV\s*/\s*REF.*"):
        lines=page.get_lines(page.get_partially_in_rect(0,item.y1+0.1,100,item.y2-0.1))
        for line in lines:
            m,ft=re.match(".*([(\d\.)]+)\s*M\s*\(([\d\.]+)\s*FT\).*",line).groups()
            assert (float(m)-float(ft)*0.3048)<5
            assert not 'elev' in ad
            ad['elev']=float(ft)
        

        
    for item in page.get_by_regex(ur"Mittapisteen.*sijainti"):
        lines=page.get_lines(page.get_partially_in_rect(item.x1,item.y1,100,item.y2))        
        for line in lines:
            for crd in mapper.parsecoords(line):
                assert not ('pos' in ad)
                ad['pos']=crd
    ad['runways']=[]
    thrs=[]
    freqs=[]
    for pagenr in xrange(p.get_num_pages()):
        page=p.parse_page_to_items(pagenr)
        for item in page.get_by_regex("\s*RUNWAY\s*PHYSICAL\s*CHARACTERISTICS\s*"):
            lines=page.get_lines(page.get_partially_in_rect(0,item.y2+0.1,100,100))
            for line in lines:
                if re.match(ur"AD\s+2.13",line): break
                m=re.match(ur".*?(RWY END)?\s*\*?(\d{6}\.\d+N)\s*(\d{6,7}\.\d+E).*",line)
                if not m:continue
                rwyend,lat,lon=m.groups()
                rwytxts=page.get_lines(page.get_partially_in_rect(0,line.y1,12,line.y2))
                print "Rwytxts:",rwytxts
                rwytxt,=rwytxts
                uprint("rwytext:",rwytxt)
                rwy,=re.match(ur"\s*(\d{2}[LRCM]?)\s*[\d.]*\s*",rwytxt).groups()
                have_thr=False
                for thr in thrs:
                    if thr['thr']==rwy:
                        have_thr=True
                if rwyend!=None and have_thr:
                    continue
                thrs.append(dict(pos=mapper.parse_coords(lat,lon),thr=rwy))
        
        for item in page.get_by_regex("ATS AIRSPACE"):
            lines=iter(page.get_lines(page.get_partially_in_rect(0,item.y2+0.1,100,100)))
            spaces=[]
            line=lines.next()
            while True:
                while line.strip()=="":
                    line=lines.next()
                print "Read line:",line
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
                    print "Further:",line                        
                    
                    if line.count("Vertical limits"):
                        print "Breaking"
                        break                            
                    if not re.search(ur"[\d ]+N\s*[\d ]+E",line) and  \
                        not re.search(ur"circle|cent[red]{1,5}|pitkin|point|equal\s*to",line):
                        print "Breaking"
                        break
                    coords.append(line)
                    
                areaspec="".join(coords)
                
                def fixup(m):
                    lat,lon=m.groups()
                    return lat.replace(" ","")+" "+lon.replace(" ","")
                areaspec=re.sub(ur"([\d ]+N)\s*([\d ]+E)",fixup,areaspec)
                
                areaspec=re.sub(ur"\(.*/\s*equal\s*to\s*Malmi\s*CTR\s*lateral\s*limits\)","",areaspec)
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
    

      
    
    
    
    
def fi_parse_airfields(onlyicao=None):
    icaolist=['EFHA',
             'EFHF',
             'EFHK',
             'EFIV',
             'EFJO',
             'EFJY',
             'EFKI',
             'EFKA',
             'EFKE',
             'EFKT',
             'EFKK',
             'EFKU',
             'EFKS',
             'EFLP',
             'EFMA',
             'EFMI',
             'EFOU',
             'EFPO',
             'EFRO',
             'EFSA',
             'EFSI',
             'EFTP',
             'EFTU',
             'EFUT',
             'EFVA',
             'EFVR']
                
    ads=[]
    adspaces=[]
    points=[]
    for icao in icaolist:
        if onlyicao!=None and icao!=onlyicao: continue
        ad,adspace,sigpoints=fi_parse_airfield(icao)
        ads.append(ad)
        points.append(sigpoints)
        adspaces.extend(adspace)
    return ads,adspaces,points
    
    
    
    
if __name__=='__main__':
    if len(sys.argv)==2:
        icaolimit=sys.argv[1]
    else:
        icaolimit=None
    ads,spaces,points=fi_parse_airfields(icaolimit)
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
        
        
