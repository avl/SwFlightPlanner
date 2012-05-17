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
import ee_parse_tma2

def ee_parse_gen_r2(url):
    spaces=[]
    parser=lxml.html.HTMLParser()
    data,date=fetchdata.getdata(url,country='ee')
    parser.feed(data)
    tree=parser.close()
    print "Parsed tree"
    for tab in tree.xpath(".//table"):
        print "Found table"
        for idx,cand in enumerate(tab.xpath(".//tr")):
            if len(cand.getchildren())<3:
                continue
            space=dict()
            #print list(cand.getchildren())
            what,vert,remark=list(cand.getchildren())[0:3]         
            whattxt=alltext(what).replace(u"–","-").replace(u"\xa0"," ")
            
            verttxt=alltext(vert)
            
            while True:
                w=re.sub(ur"\(.*?\)","",whattxt)
                if w!=whattxt:
                    whattxt=w 
                    continue
                break
            
            #print idx,whattxt
            if idx<3:
                if idx==1: assert (whattxt.count("Identification") or whattxt.count("ateral limits"))
                if idx==2: assert whattxt.strip()=="1"
                continue 
            verttxt=verttxt.replace(u"\xa0",u" ")
            vertlines=[x for x in verttxt.split("\n") if x.strip()]
            if len(vertlines)==1:
                vertlines=[x for x in verttxt.split("  ") if x.strip()]
            print "Verlintes:",repr(vertlines)
            #print "wha------------------------ t",whattxt
            space['ceiling'],space['floor']=vertlines[:2]
            mapper.parse_elev(space['ceiling'])
            ifloor=mapper.parse_elev(space['floor'])
            if ifloor>=9500: continue
            lines=whattxt.split("\n")
            out=[]
            merged=""
            for line in lines[1:]:
                line=line.strip().replace(u"–","-")
                if line=="":continue
                if line.endswith("point"):
                    out.append(line+" ")
                    continue
                if line.endswith("ircle with radius of") or line.endswith(",") or line.endswith("on") or line.endswith("radius"):
                    merged=" ".join([merged,line])
                    print "<---Merged:",merged
                    continue
                if merged:
                    line=" ".join([merged,line])
                merged=""
                if not line.endswith("-"):
                    line=line+" -"
                out.append(line+"\n")
            
            space['name']=lines[0].strip()
            w="".join(out)
            print "Parsing:",w
            if space['name'].startswith('EER1 '):                
                w=ee_parse_tma2.eer1txt
                fir=mapper.parse_coord_str(ee_parse_tma2.firtxt,context='estonia')
                fir_context=[fir]
                space['points']=mapper.parse_coord_str(w,fir_context=fir_context)
            else:
                space['points']=mapper.parse_coord_str(w,context='estonia')
            space['type']='R'
            space['date']=date
            space['freqs']=[]
            space['url']=fetchdata.getrawurl(url,'ee')            
            spaces.append(space)
    return spaces

def ee_parse_r_and_tsa2():
    airac_date=get_airac_date()
    spaces=[]
    url="/%s/html/eAIP/EE-ENR-5.2-en-GB.html"%(airac_date,)
    spaces.extend(ee_parse_gen_r2(url))
    url="/%s/html/eAIP/EE-ENR-5.1-en-GB.html"%(airac_date,)
    spaces.extend(ee_parse_gen_r2(url))
    url="/%s/html/eAIP/EE-ENR-5.3-en-GB.html"%(airac_date,)
    spaces.extend(ee_parse_gen_r2(url))
    url="/%s/html/eAIP/EE-ENR-5.5-en-GB.html"%(airac_date,)
    spaces.extend(ee_parse_gen_r2(url))
    return spaces

if __name__=='__main__':
    for space in ee_parse_r_and_tsa2():
        print "Space:",space['name'],":",space["floor"],"-",space["ceiling"]
        