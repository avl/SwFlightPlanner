#encoding=utf8
import parse
from parse import Item
import re
import fplan.lib.mapper as mapper
from itertools import izip,chain
from datetime import datetime
import fplan.extract.miner as miner
from fplan.extract.fetchdata import getdata

def ek_parse_airfield(icao):
    #http://www.slv.dk
    #raise Exception("This doesn't work - you need to click through web-interface for the links to work")
    #url="/Dokumenter/dsweb/Get/Document-1492/EK_AD_2_%s_en.pdf"%(icao,)
    data,date=getdata(url,country="ek",maxcacheage=86400*7)
    if 0:
        pages,date=miner.parse(url,
                           maxcacheage=86400,
                           country='ek',usecache=True)
    print icao,"bytes:",len(data)
def ek_parse_airfields():
    #http://www.slv.dk
    raise Exception("This doesn't work - you need to click through web-interface for the links to work")

    pages,date=miner.parse("/Dokumenter/dsweb/Get/Document-6465/EK_AD_1_3_en.pdf",
                           maxcacheage=86400,
                           country='ek',usecache=True)
    icaos=[]
    print "Nr pages:",len(pages)
    for nr,page in enumerate(pages):
        for item in page.get_by_regex(ur".*Aerodrome.*",re.UNICODE|re.IGNORECASE):
            print "Icao",item
            for icaoitem in page.get_partially_in_rect(item.x1,item.y1+0.1,item.x2,100):
                for icao in re.findall(ur"\b(EK[A-Z]{2})\b",icaoitem.text):                        
                    assert len(icao)==4
                    icaos.append(icao)
    ads=[]
    for icao in icaos:
        assert len(icao)==4 and icao.isupper()
        ads.append(ek_parse_airfield(icao))
    return ads


if __name__=='__main__':
    for ad in ek_parse_airfields():
        print ad
        
        