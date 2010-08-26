import fplan.lib.mapper as mapper
from fplan.lib.mapper import parse_coords,uprint
from parse import Parser
import re

def parse_sig_points():
    p=Parser("/AIP/ENR/ENR 4/ES_ENR_4_4_en.pdf")
    points=[]
    for pagenr in xrange(p.get_num_pages()):
        #print "Processing page %d"%(pagenr,)
        page=p.parse_page_to_items(pagenr)
        lines=page.get_lines(page.get_all_items())
        for line in lines:
            cols=line.split()
            if len(cols)>2:
                coordstr=" ".join(cols[1:3])
                #print cols
                if len(mapper.parsecoords(coordstr))>0:
                    crd=mapper.parsecoord(coordstr)
                    #print "Found %s: %s"%(cols[0],crd)
                    points.append(dict(
                        name=cols[0],
                        pos=crd))

    p=Parser("/AIP/ENR/ENR 4/ES_ENR_4_1_en.pdf")
    for pagenr in xrange(p.get_num_pages()):
        page=p.parse_page_to_items(pagenr)
        nameheading,=page.get_by_regex(r".*Name of station.*")
        freqheading,=page.get_by_regex(r".*Frequency.*")
        coordheading,=page.get_by_regex(r".*Coordinates.*")
        items=sorted(list(x for x in page.get_partially_in_rect(nameheading.x1,nameheading.y2+2,nameheading.x1+1,100) if x.text.strip()),key=lambda x:x.y1)
        idx=0
        while True:
            if items[idx].text.strip()=="":
                idx+=1
                continue
            if idx+1>=len(items):
                break
            name=items[idx]
            kind=items[idx+1]
            diffy=kind.y1-name.y2
            #print "Name, kind:",name,kind
            #print name.text,kind.text,diffy
            assert kind.text.count("VOR") or kind.text.count("DME") or kind.text.count("NDB")
            assert diffy<0.5
            #print "Frq cnt: <%s>"%(page.get_partially_in_rect(freqheading.x1,name.y1+0.05,freqheading.x2,kind.y2-0.05),)
            freqraw=" ".join(page.get_lines(page.get_partially_in_rect(freqheading.x1,name.y1+0.05,freqheading.x2,kind.y2-0.05)))
            short,freq=re.match(r"\s*([A-Z]{2,3})?\s*(\d+(?:\.?\d+)\s+(?:MHz|kHz))\s*(?:H24)?\s*",freqraw).groups()
            
            posraw=" ".join(page.get_lines(page.get_partially_in_rect(coordheading.x1,name.y1+0.05,coordheading.x2,kind.y2-0.05)))
            #print "Rawpos<%s>"%(posraw,)
            pos=mapper.parse_coords(*re.match(r".*?(\d+\.\d+[NS]).*?(\d+\.\d+[EW]).*",posraw).groups())
            #print "Name: %s, Shortname: %s, Freq: %s,pos: %s"%(name.text,short,freq,pos)
            points.append(dict(
                name=name.text.strip(),
                short=short,
                pos=pos,
                freq=freq))
            idx+=2        
    
    
    return points


if __name__=='__main__':
    for point in parse_sig_points():
        print "Point '%s' (%s): pos: %s, freq: %s"%(point['name'],point.get('short',''),point['pos'],point.get('freq','None'))
    
    

