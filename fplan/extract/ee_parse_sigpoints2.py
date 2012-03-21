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

def ee_parse_sigpoints2():
    sigs=[]
    parser=lxml.html.HTMLParser()
    airac_date=get_airac_date()
    url="/%s/html/eAIP/EE-ENR-4.4-en-GB.html#ENR-4.4"%(airac_date,)
    data,date=fetchdata.getdata(url,country='ee')    
    parser.feed(data)
    tree=parser.close()
    for tab in tree.xpath(".//table"):        
        for idx,cand in enumerate(tab.xpath(".//tr")):
            if len(cand.getchildren())!=4:
                continue
            if idx==0: continue            
            sig=dict()
            name,coord,ats,remark=cand.getchildren()            
            nametxt=alltext(name).strip()
            coordtxt=alltext(coord).strip()
            
            if idx==1:
                assert nametxt=='1' and coordtxt=='2' 
                continue
            print "Name:",nametxt
            print"coord:",coordtxt
            sig['url']=url
            sig['date']=date
            sig['name']=nametxt            
            subed=re.sub(ur"[\n\s]+"," ",coordtxt,flags=re.UNICODE)
            sig['pos']=mapper.anyparse(subed)
            sigs.append(sig)
    return sigs

if __name__=='__main__':
    for sig in ee_parse_sigpoints2():
        print "sig:",sig
        