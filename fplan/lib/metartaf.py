import socket
from urllib2 import urlopen
import os
from datetime import datetime,timedelta
import lxml.html
import re
import fplan.model
from fplan.model import meta,Metar,Taf,SharedTrip
import fplan.extract.fetchdata as fetchdata
from copy import copy
import sys

timeout=300
host=socket.gethostname()
dev_computer=os.getenv('SWFP_DEVCOMP')

cache=dict()

def too_old(item):
    now=datetime.utcnow()
    age=now-item.last_sync
    print "Host:",host,"dev:",dev_computer
    if dev_computer==host:
        print "Is on dev:"
        return True
        maxage=timedelta(0,0)
    else:
        maxage=timedelta(0,timeout)
    if age>maxage:
        #print "Too old",age
        return True
    #print "Not too old",age
    return False

def getpage(what,area):
    
    data,last_sync=fetchdata.getdata(geturl(what,area),country="raw",maxcacheage=timeout/2,no_dev_comp_exception=True)    
    #print "Fetched data, last sync",last_sync
    parser=lxml.html.HTMLParser()
    parser.feed(data)
    tree=parser.close()
    out=[]
    for cand in tree.xpath(".//tr"):
        elems=[]
        for elem in cand.xpath(".//td"):
            if elem.text and elem.text.strip():
                elems.append(elem.text.strip())
        if len(elems)<2: continue
        icao=elems[0].strip()
        if not re.match(r"[A-Z]{4}",icao):
            continue
        metar=" ".join(elems[1:]).strip()
        
        
        if what=='TAF':
            out.append(Taf(icao,last_sync,metar))
        else:
            out.append(Metar(icao,last_sync,metar))
    return out

def get_and_store(what,area,icao):
    klass=getklass(what)
    ret=None
    for item in getpage(what,area):
        xs=meta.Session.query(klass).filter(klass.icao==item.icao).all()
        if len(xs)==0:
            meta.Session.add(item)
            if icao==item.icao:
                ret=item            
        else:
            xs[0].last_sync=item.last_sync
            xs[0].text=item.text
            if icao==item.icao:
                ret=xs[0]            
            meta.Session.add(xs[0])
    return ret

def get_area(icao):
    if icao.startswith("ES"):
        return "Sweden"
    if icao.startswith("EF"):
        return "Finland"    
    if icao.startswith("EN"):
        return "Norway"    
    if icao.startswith("EK"):
        return "Denmark"    
    if icao.startswith("BI"): #Iceland
        return "Iceland"    
    return "Baltic"
def getklass(what):
    if what=='TAF':
        klass=Taf
    else:
        klass=Metar
    return klass

def get_data_age(item,nowfun=datetime.utcnow):
    m=re.match(r"^.*?(\d{1,2})(\d{2})(\d{2})Z.*",item.text)
    if not m:
        return None
    day,hour,minute=m.groups()
    day=int(day)
    hour=int(hour)
    minute=int(minute)
    now=nowfun()
    monthdelta=0
    if now.day<5:
        if day>25:
            monthdelta=-1
    if now.day>25:
        if day<5:
            monthdelta=+1
    year=now.year
    month=now.month+monthdelta
    if month<1:
        month=12
        year-=1
    elif month>12:
        month=1
        year+=1
    itemtime=datetime(year,month,day,hour,minute,0)
    age=now-itemtime
    return age
        
last_parse=dict()
def get_some(what,icao):
    klass=getklass(what)
    #items=meta.Session.query(Metar).filter(Metar.icao==icao).all()
    items=meta.Session.query(klass).filter(klass.icao==icao).all()
    #if len(items):
    #    #print "Item age:",items[0].last_sync
    #print "Querying",icao,what
    if len(items)==0 or too_old(items[0]):
        area=get_area(icao)
        key=(area,what)
        now=datetime.utcnow()
        if key in last_parse:        
            age=now-last_parse[key]
            if age<timedelta(0,timeout/2):                
                if len(items)==0:
                    #print "Not reparsing, already done it recently, inserting dummy"
                    obj=klass(icao,datetime.utcnow(),"")
                    meta.Session.add(obj)                
                    meta.Session.flush()
                    meta.Session.commit()
                else:
                    #not reparsing, returning too-old item instead
                    obj=items[0]            
                return obj
        last_parse[key]=now
        #print "Reparsing"
        item=get_and_store(what,area,icao)
        if item!=None:
            #print "Found in new dump"
            return item
        #Store a dummy, so we don't re-parse on next click/fetch
        if len(items)==0:
            #print "Not existing, inserting dummy"
            obj=klass(icao,datetime.utcnow(),"")            
        else:
            obj=items[0]
            obj.text=""
            #print "Obj exists, storing dummy"
            obj.last_sync=datetime.utcnow()
        meta.Session.add(obj)                
        meta.Session.flush()
        meta.Session.commit()
        return obj
    #print "Obj exists, using it"
    return items[0]
def get_metar(icao):
    try:
        return get_some("METAR",icao)
    except Exception:
        return Metar(icao,datetime.utcnow(),"")
def get_taf(icao):
    try:
        return get_some("TAF",icao)
    except Exception:
        return Taf(icao,datetime.utcnow(),"")



def geturl(what,area):
    if area=='Sweden':    
        if what=='TAF':
            return "https://www.aro.lfv.se/Links/Link/ViewLink?TorLinkId=177&type=MET"
        if what=='METAR': 
            return "https://www.aro.lfv.se/Links/Link/ViewLink?TorLinkId=175&type=MET"
    if area=='Denmark':    
        if what=='TAF':
            return "https://www.aro.lfv.se/Links/Link/ViewLink?TorLinkId=196&type=MET"
        if what=='METAR': 
            return "https://www.aro.lfv.se/Links/Link/ViewLink?TorLinkId=194&type=MET"
    if area=='Norway':    
        if what=='TAF':
            return "https://www.aro.lfv.se/Links/Link/ViewLink?TorLinkId=182&type=MET"
        if what=='METAR': 
            return "https://www.aro.lfv.se/Links/Link/ViewLink?TorLinkId=174&type=MET"
    if area=='Finland':    
        if what=='TAF':
            return "https://www.aro.lfv.se/Links/Link/ViewLink?TorLinkId=183&type=MET"
        if what=='METAR': 
            return "https://www.aro.lfv.se/Links/Link/ViewLink?TorLinkId=176&type=MET"
    if area=='Iceland':    
        if what=='TAF':
            return "https://www.aro.lfv.se/Links/Link/ViewLink?TorLinkId=197&type=MET"
        if what=='METAR': 
            return "https://www.aro.lfv.se/Links/Link/ViewLink?TorLinkId=195&type=MET"
    if area=='Baltic':    
        if what=='TAF':
            return "https://www.aro.lfv.se/Links/Link/ViewLink?TorLinkId=199&type=MET"
        if what=='METAR': 
            return "https://www.aro.lfv.se/Links/Link/ViewLink?TorLinkId=179&type=MET"


        
    raise



#def test_get_metar():
if __name__=='__main__':
    from sqlalchemy import engine_from_config
    from paste.deploy import appconfig
    from fplan.config.environment import load_environment
    conf = appconfig('config:%s'%(os.path.join(os.getcwd(),"development.ini"),))    
    load_environment(conf.global_conf, conf.local_conf)
    print "Running"
    print "Shared:",meta.Session.query(SharedTrip).filter(SharedTrip.user=="hej").all()
    print get_some(*sys.argv[1:])
    meta.Session.flush()
    meta.Session.commit()

def test_metar_age():
    class Taf():pass
    t=Taf()
    t.text="312020Z akdsjfal dfkj"
    age=get_data_age(t,lambda:datetime(2013,1,1,0,20))
    #print age
    assert age==timedelta(0,3600*4)
def test_metar_age2():
    class Taf():pass
    t=Taf()
    t.text="010020Z akdsjfal dfkj"
    age=get_data_age(t,lambda:datetime(2013,12,31,23,59))
    #print age
    assert age==-timedelta(0,60*21)

def test_metar_age3():
    class Taf():pass
    t=Taf()
    t.text="250000Z akdsjfal dfkj"
    age=get_data_age(t,lambda:datetime(2013,7,10,00,00))
    #print age
    assert age==-timedelta(15,0)
    
    
