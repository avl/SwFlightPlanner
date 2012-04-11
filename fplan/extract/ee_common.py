




#encoding=utf8
import fplan.extract.fetchdata as fetchdata
import lxml.html
import sys
import fplan.lib.mapper as mapper
import re
from fplan.lib.poly_cleaner import clean_up_polygon
from fplan.extract.html_helper import alltext,alltexts
from datetime import datetime



def get_airac_date():
    urlbase="/index.php?option=com_content&view=article&id=129&Itemid=2&lang=en"
    parser=lxml.html.HTMLParser()
    data,date=fetchdata.getdata(urlbase,country='ee_base')
    parser.feed(data)
    tree=parser.close()
    for x in tree.xpath(".//p"):    
        txt=alltext(x)
        print "par",txt
        
        m=re.match(ur".*Current\s*eAIP\s*with\s*effective\s*date\s*(\d+)\s*([A-Z]+)\s*(\d+).*AIRAC.*",txt,re.UNICODE)
        if m:
            day,months,year=m.groups()
            monthi=dict(JAN=1,
                        FEB=2,
                        MAR=3,
                        APR=4,
                        MAY=5,
                        JUN=6,
                        JUL=7,
                        AUG=8,
                        SEP=9,
                        OCT=10,
                        NOV=11,
                        DEC=12)[months]
            return "%04d-%02d-%02d"%(int(year),int(monthi),int(day))        
    raise Exception("No airac date")
