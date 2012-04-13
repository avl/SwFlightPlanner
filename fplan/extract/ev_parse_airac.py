#encoding=utf8
import fplan.extract.fetchdata as fetchdata
import lxml.html
import re
from fplan.extract.html_helper import alltext

def get_cur_airac():
    data,date=fetchdata.getdata("/aiseaip",country='ev')
    parser=lxml.html.HTMLParser()
    parser.feed(data)
    tree=parser.close()    
    for div in tree.xpath(".//div"):
        at=alltext(div)
        if at.count("eAIP"):
            print "Matching:",at
            m=re.match(r".*CURRENTLY EFFECTIVE eAIP:[\n\s]*(\d{1,2}.[A-Z]+.\d{4}).AIRAC.*",alltext(div),re.DOTALL)
            if m:
                return m.groups()[0]
    return None
