#encoding=utf8
import fplan.extract.fetchdata as fetchdata
import lxml.html
import fplan.lib.mapper as mapper
import re
from fplan.lib.poly_cleaner import clean_up_polygon
from fplan.extract.html_helper import alltext 
from datetime import datetime



def ev_parse_sigpoints():
    out=[]
    parser=lxml.html.HTMLParser()
    url="/EV-ENR-4.4-en-GB.html"
    data,date=fetchdata.getdata(url)
    parser.feed(data)
    tree=parser.close()
    for table in tree.xpath("//table"):
        #print "Table with %d children"%(len(table.getchildren()),)
        rows=list(table.xpath(".//tr"))
        for row in rows:
            hdr=list(row.xpath(".//th"))
            if hdr: continue
            cols=list(row.xpath(".//td"))
            pos=mapper.parsecoord(alltext(cols[1]))
            nameraw=alltext(cols[0])
            print "raw:",repr(nameraw)
            name,=re.match(ur"\s*(\w{5})\s*",nameraw).groups()

            out.append(dict(name=name,
                kind='sig. point',
                pos=pos))
              
    for manual in """PARKS:570014N 0241039E:entry/exit point
VISTA:565002N 0241034E:entry/exit point
ARNIS:565427N 0234611E:entry/exit point
KISHI:565609N 0234608E:entry/exit point
HOLDING WEST:565530N 0235327E:holding point
HOLDING EAST:565351N 0240313E:holding point""".split("\n"):
        name,poss,kind=manual.split(":")
        out.append(dict(
            name=name.strip(),
            pos=mapper.parsecoord(poss),            
            kind=kind))
        

    return out
if __name__=='__main__':
    print ev_parse_sigpoints()
    
