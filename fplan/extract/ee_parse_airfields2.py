#encoding=utf8
import fplan.extract.fetchdata as fetchdata
import lxml.html
import sys
import fplan.lib.mapper as mapper
import re
from fplan.lib.poly_cleaner import clean_up_polygon
from fplan.extract.html_helper import alltext,alltexts
from datetime import datetime
from ee_common import get_airac_date
import rwy_constructor
import fplan.extract.parse_landing_chart as parse_landing_chart
def ee_parse_airfields2():
    ads=[]
    spaces=[]
    airac_date=get_airac_date()
    print "airac",airac_date
    overview_url="/%s/html/eAIP/EE-AD-0.6-en-GB.html"%(airac_date,)
        
    parser=lxml.html.HTMLParser()
    data,date=fetchdata.getdata(overview_url,country='ee')
    parser.feed(data)
    tree=parser.close()
    icaos=[]
    for cand in tree.xpath(".//h3"):
        txts=alltexts(cand.xpath(".//a"))
        aps=re.findall(r"EE[A-Z]{2}"," ".join(txts))
        if aps:
            icao,=aps
            if alltext(cand).count("HELIPORT"):
                print "Ignore heliport",icao
                continue
            icaos.append(icao)
    
    for icao in icaos:
        ad=dict(icao=icao)
        url="/%s/html/eAIP/EE-AD-2.%s-en-GB.html"%(airac_date,icao)
        data,date=fetchdata.getdata(url,country='ee')
        parser.feed(data)
        tree=parser.close()
        thrs=[]


        
        for h3 in tree.xpath(".//h3"):
            txt=alltext(h3)
            print repr(txt)
            ptrn=ur"\s*%s\s+[—-]\s+(.*)"%(unicode(icao.upper()),)
            m=re.match(ptrn,txt,re.UNICODE)
            if m:
                assert not 'name' in ad
                ad['name']=m.groups()[0]
                
        for tr in tree.xpath(".//tr"):
            txt=alltext(tr)
            m=re.match(r".*coordinates\s*and\s*site.*(\d{6}N\s*\d{7}E).*",txt)
            #print "Matching,",txt,":",m 
            if m:
                crds,=m.groups()
                ad['pos']=mapper.anyparse(crds)
                
        space=dict()
        for table in tree.xpath(".//table"):
            for tr in table.xpath(".//tr"):
                trtxt=alltext(tr)
                if trtxt.count("Designation and lateral limits"):
                    space=dict()
                    coords=tr.getchildren()[2]
                    lines=alltext(coords).split("\n")
                    if lines[0].strip()=='NIL':
                        continue
                    
                    
                    zname,what,spill=re.match(ur"(.*)\s+(CTR|TIZ|FIZ)(.*)",lines[0]).groups()
                    if spill and spill.strip():
                        rest=[spill]+lines[1:]
                    else:
                        rest=lines[1:]
                    what=what.strip()
                    assert ad['name'].upper().strip().count(zname.upper().strip())
                    assert what in ['FIZ','TIZ','CTR']
                    space['type']=what
                    space['points']=mapper.parse_coord_str("\n".join(rest))

                    space['name']=zname+" "+what
                    space['date']=date
                    space['url']=fetchdata.getrawurl(url,'ee')
                 
                    
                if trtxt.count("Vertical limits"):
                    vlim=alltext(tr.getchildren()[2])
                    if vlim.strip()=='NIL': continue
                    space['floor'],space['ceiling']=vlim.split(" to ")
                    
                #space['freqs']=x
                
        #hlc=False
        for h4 in tree.xpath(".//h4"):
            txt=alltext(h4)
            if txt.lower().count("charts"):
                par=h4.getparent()
                for table in par.xpath(".//table"):
                    for idx,tr in enumerate(table.xpath(".//tr")):
                        name,page=\
                            tr.getchildren()
                        nametxt=alltext(name)
                        print "nametxt:",nametxt,"link:"
                        if re.match(r"Aerodrome.*Chart.*",nametxt):
                            for a in page.xpath(".//a"):
                                print "linklabel",a.text
                                print "attrib:",a.attrib
                                href=a.attrib['href']
                                print "Bef repl",href
                                if href.lower().endswith("pdf"):
                                    href=href.replace("../../graphics","/%s/graphics"%(airac_date,))
                                    print "href:",href,airac_date
                                    
                                    parse_landing_chart.help_plc(ad,href,
                                                    icao,ad['pos'],"ee",variant="")
                                    """arp=ad['pos']
                                    lc=parse_landing_chart.parse_landing_chart(
                                            href,
                                            icao=icao,
                                            arppos=arp,country="ee")
                                    assert lc
                                    if lc:
                                        ad['adcharturl']=lc['url']
                                        ad['adchart']=lc
                                        hlc=True
                                        #chartblobnames.append(lc['blobname'])
                                    """                                                    
        #assert hlc
        for h4 in tree.xpath(".//h4"):
            txt=alltext(h4)
            if txt.count("RUNWAY PHYSICAL"):
                par=h4.getparent()

                for table in par.xpath(".//table"):
                    prevnametxt=""
                    for idx,tr in enumerate(table.xpath(".//tr")):
                        if idx==0:
                            fc=alltext(tr.getchildren()[0])
                            print "FC",fc
                            if not fc.count("Designations"):
                                break #skip table
                        if idx<2:continue
                        if len(tr.getchildren())==1:continue
                        print "c:",tr.getchildren(),alltexts(tr.getchildren())
                        desig,trubrg,dims,strength,thrcoord,threlev=tr.getchildren()
                        rwy=re.match(r"(\d{2}[LRC]?)",alltext(desig))
                        altc=alltext(thrcoord)
                        print "Matching",altc
                        print "rwymatch:",alltext(desig)
                        m=re.match(r"\s*(\d+\.?\d*N)[\s\n]*(\d+\.?\d*E).*",altc,re.DOTALL|re.MULTILINE)                        
                        if m:
                            lat,lon=m.groups()
                            print "Got latlon",lat,lon
                            thrs.append(dict(pos=mapper.parse_coords(lat,lon),thr=rwy.groups()[0]))         
                        
                                
        space['freqs']=[]
        for h4 in tree.xpath(".//h4"):
            txt=alltext(h4)
            if txt.count("ATS COMMUNICATION"):
                par=h4.getparent()
                for table in par.xpath(".//table"):
                    for idx,tr in enumerate(table.xpath(".//tr")):
                        service,callsign,frequency,hours,remarks=\
                            tr.getchildren()
                        callsigntxt=alltext(callsign)
                        if idx<2:
                            if idx==0:
                                assert callsigntxt.strip()=="Call sign"
                            if idx==1:
                                 assert callsigntxt.strip()=="2"
                            continue
                        ftext=alltext(frequency)
                        print "matching freq",ftext
                        freq,=re.match(ur"\s*(\d+\.\d+)\s*MHz\s*",ftext).groups()
                        freqmhz=float(freq)
                        
                        space['freqs'].append((callsigntxt.strip(),freqmhz))
                              
        if space and 'points' in space:
            assert 'freqs' in space
            assert 'points' in space
            assert 'floor' in space
            assert 'ceiling' in space
            assert 'type' in space
            spaces.append(space)
        if thrs:
            ad['runways']=rwy_constructor.get_rwys(thrs)
        ad['date']=date
        ad['url']=fetchdata.getrawurl(url,'ee')   
        print "AD:",ad
        assert 'pos' in ad
        assert 'name' in ad
        ads.append(ad)
        
    """    
    
    ads=[]
    spaces=[]
    seen=set()
    for icao in ["EVRA",
                "EVLA",
                "EVTA",
                "EVVA"]:
        url="/EV-AD-2.%s-en-GB.html"%(icao,)
        parser=lxml.html.HTMLParser()
        data,date=fetchdata.getdata(url)
        parser.feed(data)
        tree=parser.close()
        elev=None
        pos=None
        ctrarea=None
        ctr=None
        ctralt=None
        ctrname=None
        adnametag,=tree.xpath("//p[@class='ADName']")
        adnamestr=alltext(adnametag)
        print adnamestr
        name,=re.match(ur"%s\s*[-—]\s*([\w\s]+)"%(icao,),adnamestr,re.UNICODE).groups()
        freqs=[]
        for table in tree.xpath("//table"):
            rows=list(table.xpath(".//tr"))
            
            headings=list(table.xpath(".//th"))
            
            if len(headings)==5:
                if headings[2]=="Frequency":
                    for row in rows:
                        cols=alltexts(table.xpath(".//td"))
                        desig,name=cols[0:2]
                        freq,=re.match(ur"\d{3}\.\d{3}\s*MHz",cols[2]).groups()
                        if freq!="121.500":
                            freqs.append((desig+" "+name,float(freq)))                        
                        
                    continue
                
            
            for row in rows:
                cols=alltexts(row.xpath(".//td"))
                if len(cols)<2: continue
                if not pos and re.match(ur".*ARP\s*coordinates.*",cols[1]):
                    pos,=mapper.parsecoords(cols[2])
                if not elev and re.match(ur"Elevation.*",cols[1]):
                    elev,=re.match(ur"(\d+) FT.*",cols[2]).groups()
                
                if not ctr and re.match(ur"Designation\s*and\s*lateral\s*limits",cols[1]):
                    lines=cols[2].split("\n")
                    ctr=True
                    print "Got lateral limits",lines[0]
                    ctrname,type_=re.match(ur"^([\w\s]+)(CTR|TIZ)",lines[0]).groups()
                    assert ctrname.strip()
                    ctrname=ctrname.strip()+" "+type_
                    ctrarea=" ".join(lines[1:])
                #print ".",cols[1],"."
                if not ctralt and re.match(ur".*Vertical\s*limits.*",cols[1],re.UNICODE):
                    ctralt=True
                    #print "<",cols[2],">"
                    alts=cols[2].split("/")
                    if len(alts)==1:                    
                        ceiling=alts[0]
                        floor="GND"
                    else:
                        ceiling,floor=alts
                    print "Parsed",ceiling,floor

        assert pos
        assert type_
        assert elev
        assert name                                        
        assert not ctrname in seen
        seen.add(ctrname)
        ads.append(dict(
            icao=icao,
            name=name,
            elev=elev,
            date=datetime(2011,03,25),
            pos=pos))
            
        spaces.append(dict(
            name=ctrname,
            points=mapper.parse_coord_str(ctrarea),
            ceiling=ceiling,
            type=type_,
            floor=floor,
            freqs=freqs,
            date=datetime(2011,03,25),
            url=url            
                      ))
    ads.append(dict(
        icao="EVRS",
        name="Spilve",
        elev=5,
        date=datetime(2011,04,05),
        pos=mapper.parsecoord("565931N 240428E")
               ))
"""
    return ads,spaces

if __name__=='__main__':
    ads,spaces=ee_parse_airfields2()
    for ad in ads:
        print "Ad:",ad
    for sp in spaces:
        print "Space:",sp

