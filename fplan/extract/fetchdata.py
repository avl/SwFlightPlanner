#!/usr/bin/python
import os
from datetime import datetime,timedelta
import socket
host=socket.gethostname()
from urllib2 import urlopen

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
    if os.path.exists(cachenamexml):
        cacheddate=get_filedate(cachenamexml)
        print "cachedat:",cacheddate,"nowdate:",nowdate
        age=nowdate-cacheddate
        print "cache-age:",age
        if age<timedelta(0,7200):
            print "Returning cached %s"%(relpath,)
            return open(cachenamexml).read()
        print "Cache to old"
    pdfdata=getrawdata(relpath)
    if not os.path.exists("/tmp/lfv"):
        os.makedirs("/tmp/lfv")
    open(cachenamepdf,"w").write(pdfdata)
    if os.system("pdftohtml -xml -nodrm "+cachenamepdf)!=0:
        raise Exception("pdftohtml failed!")
       
    #modt=int(filedate.strftime('%s'))
    #os.utime(cachenamexml,(modt,modt))
    
    return open(cachenamexml).read() 

def get_raw_weather_for_area(cur_area):
    if host=='macbook':           
        return open("/home/anders/saker/avl_traveltools/fplan/fplan/MetInfo%s.asp"%(cur_area.upper(),)).read()
    else:
        raise Exception("TODO: Add correct urlopen call here!");
    
#def get_raw_notam():
#    return open("/home/anders/saker/avl_traveltools/fplan/fplan/fplan/extract/notam_sample.html").read()



