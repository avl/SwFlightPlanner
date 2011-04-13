#encoding=utf8
import fplan.extract.fetchdata as fetchdata
import lxml.html
import fplan.lib.mapper as mapper
import re
from fplan.lib.poly_cleaner import clean_up_polygon
from fplan.extract.html_helper import alltext,alltexts
from datetime import datetime


def ev_parse_airfields():
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
    return ads,spaces


if __name__=='__main__':
    ads,spaces=ev_parse_airfields()
    for ad in ads:
        print "Ad:",ad
    for sp in spaces:
        print "Space:",sp
        