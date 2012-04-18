#encoding=utf8
import fplan.extract.fetchdata as fetchdata
import lxml.html
import fplan.lib.mapper as mapper
import re
from fplan.lib.poly_cleaner import clean_up_polygon
from fplan.extract.html_helper import alltext,alltexts
from datetime import datetime
from fplan.extract.ev_parse_airac import get_cur_airac
import fplan.extract.parse_landing_chart as parse_landing_chart 
import rwy_constructor
import aip_text_documents
#   #CURRENTLY EFFECTIVE eAIP:
#05-APR-2012-AIRAC (open in new window) 

def ev_parse_airfields():
    ads=[]
    spaces=[]
    seen=set()
    cur_airac=get_cur_airac()
    assert cur_airac
    for icao in ["EVRA",
                "EVLA",
                "EVTJ",
                "EVVA"]:
        thrs=[]
        url="/eAIPfiles/%s-AIRAC/html/eAIP/EV-AD-2.%s-en-GB.html"%(cur_airac,icao)
        data,date=fetchdata.getdata(url,country='ev')
        parser=lxml.html.HTMLParser()
        parser.feed(data)
        tree=parser.close()
        elev=None
        pos=None
        ctrarea=None
        ctr=None
        ctralt=None
        ctrname=None
        adcharturl=None
        adchart=None
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
                        
        addummy=dict()
        
        for h4 in tree.xpath(".//h4"):
            txt=alltext(h4)
            if txt.count("CHARTS"):
                par=h4.getparent()
                
                for table in par.xpath(".//table"):
                    prevnametxt=""
                    for idx,tr in enumerate(table.xpath(".//tr")):
                        namepage=tr
                            
                        nametxt=alltext(tr)
                        print "nametxt:",nametxt,"link:"
                        variantlist=[("Aerodrome Chart",''),
                                     ("Visual Approach Chart",'VAC'),
                                     ('Aerodrome Ground Movement Chart','parking')]
                        
                        for st,variant in variantlist:
                            if nametxt.count(st) or prevnametxt.count(st):
                                for a in namepage.xpath(".//a"):
                                    print "linklabel",a.text
                                    print "attrib:",a.attrib
                                    href=a.attrib['href']
                                    print "Bef repl",href
                                    if href.lower().endswith("pdf"):
                                        href=href.replace("../../graphics","/eAIPfiles/%s-AIRAC/graphics"%(cur_airac,))
                                        print "href:",href,cur_airac
                                        #arp=pos
                                        parse_landing_chart.help_plc(addummy,href,
                                                        icao,pos,"ev",variant=variant)
                                        """
                                        lc=parse_landing_chart.parse_landing_chart(
                                                href,
                                                icao=icao,
                                                arppos=arp,country="ev")
                                        assert lc
                                        if lc:
                                            adcharturl=lc['url']
                                            adchart=lc
                                            #chartblobnames.append(lc['blobname'])
                                        """
                                        nametxt=""
                        prevnametxt=nametxt
                    

        assert pos
        assert type_
        assert elev
        assert name                                        
        assert not ctrname in seen
        seen.add(ctrname)
        ad=dict(
            icao=icao,
            name=name,
            elev=elev,
            date=date,
            runways=rwy_constructor.get_rwys(thrs),
            pos=pos)
        if adcharturl:
            ad['adcharturl']=adcharturl
        if 'adcharts' in addummy:
            ad['adcharts']=addummy['adcharts']
            
        aip_text_documents.help_parse_doc(ad,url,
                        icao,"ev",title="General Information",category="general")
            
        ads.append(ad)            
        spaces.append(dict(
            name=ctrname,
            points=mapper.parse_coord_str(ctrarea),
            ceiling=ceiling,
            type=type_,
            floor=floor,
            freqs=freqs,
            date=date,
            url=url            
                      ))
    ads.append(dict(
        icao="EVRS",
        name="Spilve",
        elev=5,
        date=datetime(2011,04,05),
        pos=mapper.parsecoord("565931N 240428E")
               ))
    return ads,spaces


if __name__=='__main__':
    ads,spaces=ev_parse_airfields()
    for ad in ads:
        print "Ad:",ad
    for sp in spaces:
        print "Space:",sp
        
