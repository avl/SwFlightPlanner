#encoding=utf8
import parse
from parse import Item
import re
import sys
import fplan.lib.mapper as mapper

def fi_parse_airfield(icao=None):
    spaces=[]
    ad=dict()
    ad['freqs']=[]
    ad['icao']=icao
    #https://ais.fi/ais/eaip/pdf/aerodromes/EF_AD_2_EFET_EN.pdf
    #https://ais.fi/ais/eaip/aipcharts/efet/EF_AD_2_EFET_VAC.pdf
    vacp=parse.Parser("/ais/eaip/aipcharts/%s/EF_AD_2_%s_VAC.pdf"%(icao.lower(),icao),lambda x: x,country="fi")
    p=parse.Parser("/ais/eaip/pdf/aerodromes/EF_AD_2_%s_EN.pdf"%(icao,),lambda x: x,country="fi")

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
            lines=iter(page.get_lines(page.get_partially_in_rect(0,item.y2+0.1,100,100)))
            spaces=[]
            while True:
                line=lines.next()
                print "Read line:",line
                if line.count("Vertical limits"):
                    break                            
                m=re.match(ur".*?/\s+Designation and lateral limits\s*(.*\b(?:CTR|FIZ)\b.*?)\s*:?\s*$",line)
                if not m:
                    m=re.match(ur"\s*(.*\b(?:CTR|FIZ)\b.*?)\s*:",line)
                    print "Second try:",m
                    
                spacename,=m.groups()
                print "Got spacename:",spacename
                assert spacename.strip()!=""
                coords=[]
                while True:
                    line=lines.next()
                    print "Further:",line
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
                print "Fixed areaspec",areaspec
                #if icao=="EFKS":
                #    areaspec=areaspec.replace("6615 28N","661528N")
#Error! REstriction areas!
                spaces.append(dict(
                    name=spacename,
                    type="CTR",
                    points=mapper.parse_coord_str(areaspec)))
                if line.count("Vertical limits"):
                    print "Breaking"
                    break                            
            while not line.count("Vertical limits"):
                line=lines.next()
            print "Matching veritcal limits--------------------------------"
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
                    print "Matching ",space['name']," to ",line,"missing:",missing
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
                    print "Missing:"
                    if len(missing)==0: break
                if len(missing)==0: break
                line=lines.next()
                
            freqs=[]      
            for item2 in page.get_by_regex("ATS COMMUNICATION FACILITIES"):
                lines=page.get_lines(page.get_partially_in_rect(0,item2.y2+0.1,100,100))
                for line in lines:
                    if line.count("RADIO NAVIGATION AND LANDING AIDS"): break
                    twr=re.match(ur"TWR.*(\d{3}\.\d{3})",line)
                    if twr:
                        freqs.append(('TWR',float(twr.groups()[0]))) 
                    atis=re.match(ur"ATIS.*(\d{3}\.\d{3})",line)
                    if atis:
                        freqs.append(('ATIS',float(atis.groups()[0])))
            for space in spaces:
                space['freqs']=freqs
                             
    print ad
    return ad,spaces
    

      
    
    
    
    
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
    for icao in icaolist:
        if onlyicao!=None and icao!=onlyicao: continue
        ad,adspace=fi_parse_airfield(icao)
        ads.append(ad)
        adspaces.extend(adspace)
    return ads,adspaces
    
    
    
    
if __name__=='__main__':
    if len(sys.argv[1])==4:
        icaolimit=sys.argv[1]
    else:
        icaolimit=None
    ads,spaces=fi_parse_airfields(icaolimit)
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
        
        
