#encoding=utf8
import fplan.extract.fetchdata as fetchdata
import lxml.html
import fplan.lib.mapper as mapper
import re
from fplan.lib.poly_cleaner import clean_up_polygon

def alltextlist(x):
    if x.text:
        s=[x.text]
    else:
        s=[]
    for child in x.getchildren():
        if child.tag.lower() in ['p','br']:
            s.append("\n")
        childitems=alltextlist(child)
        s.extend(childitems)
        if child.tag.lower()=="p":
            s.append("\n")
    if x.tail:    
        s.append(x.tail)
    return s
def alltext(x):
    l=alltextlist(x)
    return (" ".join(l)).strip()

def ev_parse_obst():
    url="/EV-ENR-5.4-en-GB.html"
    parser=lxml.html.HTMLParser()
    data,date=fetchdata.getdata(url)
    parser.feed(data)
    tree=parser.close()
    got_fir=False
    res=[]
    for table in tree.xpath("//table"):
        for row in table.xpath(".//tr"):
            tds=row.xpath(".//td")
            if len(tds)!=5: continue
            name,type,coord,elev,light=[alltext(x) for x in tds]
            elev,height=elev.split("/")
            res.append(
                dict(
                    name=name,
                    pos=mapper.parsecoord(coord),
                    height=mapper.parse_elev(height.strip()),
                    elev=mapper.parse_elev(elev),
                    lighting=light,
                    kind=type
                     ))
    return res
        


def ev_parse_r():
    out=[]
    out.extend(ev_parse_x(url="/EV-ENR-5.1-en-GB.html"))
    out.extend(ev_parse_x(url="/EV-ENR-5.2-en-GB.html"))
    out.extend(ev_parse_x(url="/EV-ENR-5.3-en-GB.html"))
    out.extend(ev_parse_x(url="/EV-ENR-5.5-en-GB.html"))
    return out
def ev_parse_x(url):
    out=[]
    parser=lxml.html.HTMLParser()
    data,date=fetchdata.getdata(url)
    parser.feed(data)
    tree=parser.close()
    got_fir=False
    for table in tree.xpath("//table"):
        #print "Table with %d children"%(len(table.getchildren()),)
        rows=list(table.xpath(".//tr"))

        #for idx,col in enumerate(cols):
        #    print "Col %d, %s"%(idx,alltext(col)[:10])
        headingcols=rows[0].xpath(".//th")
        if len(headingcols)==0: continue
        name,alt=headingcols[0:2]
        if alltext(name).count("QNH") and len(headingcols)>6:
            continue
        print alltext(name)
        assert alltext(name).lower().count("name") or alltext(name).lower().count("lateral")
        print alltext(alt)
        assert alltext(alt).lower().count("limit")
        for row in rows[1:]:
            cols=list(row.xpath(".//td"))
            if len(cols)!=3: continue
            name,alt,remark=cols
            lines=[x.strip() for x in alltext(name).split("\n") if x.strip()]
            if len(lines)==0: continue
            assert len(lines)
            spacename=lines[0].strip()
            print spacename            
            assert spacename[:3] in ["EVR","EVP","TSA","TRA"]
            altcand=[]
            for altc in alltext(alt).split("\n"):
                if altc.count("Real-time"): continue
                altcand.append(altc.strip())
            floor,ceiling=[x.strip() for x in " ".join(altcand).split("/")]
            mapper.parse_elev(ceiling)            
            mapper.parse_elev(floor)
            
            freqs=[]
            coords=mapper.parse_coord_str(" ".join(lines[1:]),context='latvia')
            for cleaned in clean_up_polygon(coords):
                out.append(dict(
                        name=spacename,
                        points=cleaned,
                        type="R",
                        freqs=freqs,
                        floor=floor,
                        url=url,
                        date=date,
                        ceiling=ceiling))
                
    
    return out


def ev_parse_tma():
    out=[]
    parser=lxml.html.HTMLParser()
    url="/Latvia_EV-ENR-2.1-en-GB.html"
    data,date=fetchdata.getdata(url)
    parser.feed(data)
    tree=parser.close()
    got_fir=False
    for table in tree.xpath("//table"):
        #print "Table with %d children"%(len(table.getchildren()),)
        rows=list(table.xpath(".//tr"))
        for idx in xrange(5):
            headingrow=rows[idx]
            cols=list(headingrow.xpath(".//th"))
            #print len(cols)
            if len(cols)==5:        
                break
        else:
            raise Exception("No heading row")
        assert idx==0
        #for idx,col in enumerate(cols):
        #    print "Col %d, %s"%(idx,alltext(col)[:10])
        name,unit,callsign,freq,remark=cols
        assert alltext(name).lower().count("name")
        assert alltext(unit).lower().count("unit")
        assert re.match(ur"call\s*sign",alltext(callsign).lower())
        for row in rows[1:]:
            cols=list(row.xpath(".//td"))
            if len(cols)!=5: continue
            name,unit,callsign,freq,remark=cols
            lines=[x.strip() for x in alltext(name).split("\n") if x.strip()]
            if len(lines)==0: continue
            spacename=lines[0].strip()
            
            if re.match(ur"RIGA\s*UTA|RIGA\s*CTA|RIGA\s*AOR.*",spacename):
                continue
            freqstr=alltext(freq)
            callsignstr=alltext(callsign)
            if freqstr.strip():
                print freqstr
                freqmhzs=re.findall(ur"\d{3}\.\d{3}",freqstr)
                assert len(freqmhzs)<=2
                callsigns=[callsignstr.split("\n")[0].strip()]
                freqs=[]
                for idx,freqmhz in enumerate(freqmhzs):
                    if freqmhz=='121.500': continue
                    freqs.append((callsigns[idx],float(freqmhz)))
                print "freqs:",freqs
            else:
                freqs=[]
            assert len(lines)
            
            classidx=next(idx for idx,x in reversed(list(enumerate(lines)))
                                 if x.lower().count("class of airspace"))
            
            if re.match(ur"RIGA\s*FIR.*UIR",spacename,re.UNICODE):
                got_fir=True
                lastspaceidx=classidx-2
                floor="GND"
                ceiling="-"
                type_="FIR"
            else:
                if lines[classidx-1].count("/")==1:
                    floor,ceiling=lines[classidx-1].split("/")
                    lastspaceidx=classidx-1
                else:
                    floor=lines[classidx-1]
                    ceiling=lines[classidx-2]
                    lastspaceidx=classidx-2
                mapper.parse_elev(ceiling)
                mapper.parse_elev(floor)
                type_="TMA"
            tcoords=lines[1:lastspaceidx]
            #verify that we got actual altitudes:
            coords=[]
            for coord in tcoords:
                coord=coord.strip()
                if coord.endswith(u"E") or coord.endswith("W"):
                    coord=coord+" -"
                coords.append(coord)
                    
            coords=mapper.parse_coord_str(" ".join(coords),context='latvia')
            for cleaned in clean_up_polygon(coords):
                out.append(dict(
                        name=spacename,
                        points=cleaned,
                        type=type_,
                        freqs=freqs,
                        floor=floor,
                        url=url,
                        date=date,
                        ceiling=ceiling))
                
    
    return out



if __name__=='__main__':
    for obst in ev_parse_obst():
        print "obst:",obst
    for space in ev_parse_r():
        print "name:",space['name']
        print "  floor:",space['floor']
        print "  ceiling:",space['ceiling']
        print "  coords:",space['points']
    for space in ev_parse_tma():
        print "name:",space['name']
        print "  floor:",space['floor']
        print "  ceiling:",space['ceiling']
        print "  coords:",space['points']
        print "  freqs:",space['freqs']
        
    


    