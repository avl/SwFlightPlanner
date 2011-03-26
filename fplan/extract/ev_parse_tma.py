import fplan.extract.fetchdata as fetchdata
import lxml.html
import fplan.lib.mapper as mapper
def alltextlist(x):
    if x.text:
        s=[x.text]
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
        


def parse_tma():
    out=[]
    parser=lxml.html.HTMLParser()
    parser.feed(fetchdata.getdata("latvia_tma_etc"))
    tree=parser.close()
    for table in tree.xpath("//table"):
        assert tree.xpath("//table")==[] #No sub-tables
        rows=list(table.xpath("//tr"))
        headingrow=rows[0]
        name,unit,callsign,freq,remark=headingrow.xpath("//td")
        assert alltext(name).lower().count("Name")
        assert alltext(unit).lower().count("Unit")
        assert re.match(ur"call\s*sign",alltext(callsign).lower())
        for row in rows[1:]:
            name,unit,callsign,freq,remark=row.xpath("//td")
            lines=[x.strip() for x in alltext(name).split("\n") if x.strip()]
            if len(lines)==0: continue
            spacename=lines[0].strip()
            assert len(lines)
            
            classidx=next(idx for idx,x in reversed(enumerate(lines))
                                 if x.lower().count("class of airspace"))
            floor=lines[classidx-1]
            ceiling=lines[classidx-2]
            coords=lines[1:classidx-2]
            mapper.
            list(reversed(dropwhile(
                lambda x:not x.lower().count("class of airspace"),
                reversed(lines))))
            
            
            
            
            
        
            
    
    return out



if __name__=='__main__':
    parse_tma()
    
    


    