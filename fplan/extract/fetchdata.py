#!/usr/bin/python
import os
from datetime import datetime,timedelta
import socket
host=socket.gethostname()
from urllib2 import urlopen

caching_enabled=True #True for debug, set to false by background updater

def get_filedate(path):
    return datetime.fromtimestamp(os.path.getmtime(path))

def stripname(path):
    out=[]
    for c in path:
        if c.isalnum() or c=='.':
            out.append(c)
        else:
            out.append("_")
    return "".join(out)
def changeext(path,from_,to_):
    assert path.endswith(from_)
    path=path[:-len(from_)]
    return path+to_

#def get_date(path):
#    return get_filedate('/home/anders/lfv/www.lfv.se'+path)
def getrawdata(relpath):
    fixed=relpath.replace(" ","%20")
    print relpath
    assert(relpath.startswith("/"))
    #return open('/home/anders/lfv/www.lfv.se'+relpath).read()
    durl="http://www.lfv.se"+fixed
    print "Downloading url: "+durl
    data=urlopen(durl).read()
    print "Got %d bytes"%(len(data),)
    return data
    
def getxml(relpath):
    print "getxml:"+relpath
    assert relpath.startswith("/")
    
    nowdate=datetime.now()
    cachenamepdf="/tmp/lfv/"+stripname(relpath)
    cachenamexml=changeext("/tmp/lfv/"+stripname(relpath),'.pdf',".xml")
    print "cachepath:"+cachenamexml
    if caching_enabled and os.path.exists(cachenamexml):
        cacheddate=get_filedate(cachenamexml)
        print "cachedat:",cacheddate,"nowdate:",nowdate
        age=nowdate-cacheddate
        print "cache-age:",age
        if age<timedelta(0,7200):
            print "Returning cached %s"%(relpath,)
            return open(cachenamexml).read()
        print "Cache too old"
    try:
        pdfdata=getrawdata(relpath)
    except Exception,cause:
        if host=="macbook":
            try:
                return open(cachenamexml).read()
            except:
                pdfdata=open("/home/anders/lfv/www.lfv.se"+relpath).read()
        else:
            raise
    if not os.path.exists("/tmp/lfv"):
        os.makedirs("/tmp/lfv")
    open(cachenamepdf,"w").write(pdfdata)
    if os.system("pdftohtml -xml -nodrm "+cachenamepdf)!=0:
        raise Exception("pdftohtml failed!")
       
    #modt=int(filedate.strftime('%s'))
    #os.utime(cachenamexml,(modt,modt))
    
    return open(cachenamexml).read() 

def get_raw_aip_sup_page():
    if host=='macbook':
        return open("/home/anders/saker/avl_traveltools/fplan/fplan/AIP SUP.html").read()
    else:
        #TODO: 
        return urlopen("http://www.lfv.se/sv/FPC/IAIP/AIP-SUP/").read()
        
weathercache=dict()
weatherlookup=dict(A="http://www.lfv.se/MetInfo.asp?TextFile=llf.esms-day.txt&TextFile=llf.esms-tot.txt&TextFile=llf.esms-n.txt&TextFile=llf.esms-se.txt&TextFile=llf.esms-sw.txt&Subtitle=Omr%e5de%A0A%A0-%A0Prelimin%e4r%A0prognos%A0f%F6r%A0morgondagen&Subtitle=Omr%e5de%A0A%A0-%A0%F6versikt&Subtitle=Omr%e5de%A0A%A0-%A0Norra%A0delen&Subtitle=Omr%e5de%A0A%A0-%A0Syd%F6stra%A0delen&Subtitle=Omr%e5de%A0A%A0-%A0Sydv%e4stra%A0delen&T=Omr%e5de%A0A%A0-%A0S%F6dra%A0Sverige&Frequency=60",
       B="http://www.lfv.se/MetInfo.asp?TextFile=llf.essa-day.txt&TextFile=llf.essa-tot.txt&TextFile=llf.essa-n.txt&TextFile=llf.essa-nw.txt&TextFile=llf.essa-s.txt&TextFile=llf.essa-se.txt&Subtitle=Omr%e5de%A0B%A0-%A0Prelimin%e4r%A0prognos%A0f%F6r%A0morgondagen&Subtitle=Omr%e5de%A0B%A0-%A0%F6versikt&Subtitle=Omr%e5de%A0B%A0-%A0Norra%A0delen&Subtitle=Omr%e5de%A0B%A0-%A0Nordv%e4stra%A0delen&Subtitle=Omr%e5de%A0B%A0-%A0S%F6dra%A0delen&Subtitle=Omr%e5de%A0B%A0-%A0Syd%F6stra%A0delen&T=Omr%e5de%A0B%A0-%A0Mellersta%A0Sverige&Frequency=60",
       C="http://www.lfv.se/MetInfo.asp?TextFile=llf.esnn-day.txt&TextFile=llf.esnn-tot.txt&TextFile=llf.esnn-n.txt&TextFile=llf.esnn-mid.txt&TextFile=llf.esnn-se.txt&TextFile=llf.esnn-sw.txt&Subtitle=Omr%e5de%A0C%A0-%A0Prelimin%e4r%A0prognos%A0f%F6r%A0morgondagen&Subtitle=Omr%e5de%A0C%A0-%A0%F6versikt&Subtitle=Omr%e5de%A0C%A0-%A0Norra%A0delen&Subtitle=Omr%e5de%A0C%A0-%A0Mellersta%A0delen&Subtitle=Omr%e5de%A0C%A0-%A0Syd%F6stra%A0delen&Subtitle=Omr%e5de%A0C%A0-%A0Sydv%e4stra%A0delen&T=Omr%e5de%A0C%A0-%A0Norra%A0Sverige&Frequency=60")
def get_raw_weather_for_area(cur_area2):
    cur_area=cur_area2.upper()
    if host=='macbook':           
        return open("/home/anders/saker/avl_traveltools/fplan/fplan/MetInfo%s.asp"%(cur_area.upper(),)).read()    
    cd=weathercache.get(cur_area,None)
    if cd and (datetime.utcnow()-cd['time'])<timedelta(0,1800):
        return cd['data']        
    cd=dict()
    url=weatherlookup[cur_area]
    cd['data']=urlopen(url).read()
    cd['time']=datetime.utcnow()
    weathercache[cur_area]=cd
    return cd['data']
    
#def get_raw_notam():
#    return open("/home/anders/saker/avl_traveltools/fplan/fplan/fplan/extract/notam_sample.html").read()



