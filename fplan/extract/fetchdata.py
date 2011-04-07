#!/usr/bin/python
import os
from datetime import datetime,timedelta
import socket
host=socket.gethostname()
from urllib2 import urlopen
import mechanize

dev_computer=os.getenv('SWFP_DEVCOMP')
tmppath=os.path.join(os.getenv("SWFP_DATADIR"),"aip")

caching_enabled=True #True for debug, set to false by background updater

def is_devcomp():
    return host==dev_computer

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
def getrawurl(relpath,country="se"):
    fixed=relpath.replace(" ","%20")
    print fixed
    assert(fixed.startswith("/"))
    if country=="se":
        durl="http://www.lfv.se"+fixed
    elif country=="fi":
        durl="http://ais.fi"+fixed
    elif country=="ee":
        durl="http://aip.eans.ee"+fixed
    elif country=="pl":
        durl="http://localhost"+fixed #TODO; Add something reasonsable here
    elif country=="no":
        durl="http://www.ippc.no"+fixed
    elif country=="ek":
        durl="http://www.slv.dk"+fixed
        print "Fetching:",durl
    elif country=="ep":        
        durl="http://www.ais.pansa.pl"+fixed
    elif country=="wikipedia":
        durl="http://en.wikipedia.org"+fixed
    else:
        raise Exception("Unknown country:"+country)
    return durl
    
    
    

def wiki_download(url):
    mbrowse=mechanize.Browser()
    mbrowse.addheaders = [('user-agent', '   Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.3) Gecko/20100423 Ubuntu/10.04 (lucid) Firefox/3.6.3'),
                     ("Accept-Language", "en-us,en")]    
    
    data=mbrowse.open_novisit(url).read()
    return data
def denmark_download(url):
    mbrowse=mechanize.Browser()
    mbrowse.addheaders = [('user-agent', '   Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.3) Gecko/20100423 Ubuntu/10.04 (lucid) Firefox/3.6.3'),
                     ("Accept-Language", "en-us,en")]    

    mbrowse.open("http://www.slv.dk/Dokumenter/dsweb/")
    clickseq=[
              "Luftfartsinformation (AIS)",
              "AIP Danmark"              
              ""]
    raise "Danish downloads not implemented yet"
    

mbrowse=None
def polish_download(url):
    global mbrowse    
    def mopen(url):
        print "Actually downloading data from polish AIP server"
        data=mbrowse.open_novisit(url).read()
        #print data
        if len(data)<1000:
            print data
            raise Exception("Suspiciously small data file (%d) bytes - is this right?"%(len(data),))
        return data
    if mbrowse:
        try:
            return mopen(url)
        except Exception,cause:
            print cause
            print "Trying a new browser"
    mbrowse=mechanize.Browser()
    print "Logging on to Polish AIP server"
    mbrowse.addheaders = [('user-agent', '   Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.3) Gecko/20100423 Ubuntu/10.04 (lucid) Firefox/3.6.3'),
                     ("Accept-Language", "en-us,en")]    
    mbrowse.open("http://www.ais.pansa.pl/aip/login.php")
    mbrowse.select_form(nr=0)
    username,password=open("polish_aip_login.txt").read().split(",")
    mbrowse['login']=username
    mbrowse['password']=password
    mbrowse.submit()
    return mopen(url)



def getrawdata(relpath,country="se"):
    durl=getrawurl(relpath,country)
    print "Downloading url: "+durl
    if country=='ep':
        data=polish_download(durl)
    elif country=="wikipedia":
        data=wiki_download(durl)
    elif country=="ek":
        data=denmark_download(durl)
    else:
        data=urlopen(durl).read()
    print "Got %d bytes"%(len(data),)
    return data

def getcachename(relpath,datatype):
    return os.path.join(tmppath,stripname(relpath)+datatype)
def getdata(relpath,country="se",maxcacheage=7200):
    nowdate=datetime.now()
    if not os.path.exists(tmppath):
        os.makedirs(tmppath)
    cachename=os.path.join(tmppath,stripname(relpath))    
    print "Checking if cached version exists:",cachename
    if caching_enabled and os.path.exists(cachename):
        cacheddate=get_filedate(cachename)
        print "cachedate:",cacheddate,"nowdate:",nowdate
        age=nowdate-cacheddate
        print "cache-age:",age
        if host==dev_computer:
            maxcacheage=4*7*24*3600
        if age<timedelta(0,maxcacheage):
            print "Returning cached %s"%(relpath,)
            return open(cachename).read(),cacheddate
    data=getrawdata(relpath,country=country)
    open(cachename,"w").write(data)
    return data,nowdate
    
def getxml(relpath,country="se",maxcacheage=7200):
    print "getxml:"+relpath
    assert relpath.startswith("/")
    if not os.path.exists(tmppath):
        os.makedirs(tmppath)
    nowdate=datetime.now()
    cachenamepdf=tmppath+"/"+stripname(relpath)
    cachenamexml=changeext(tmppath+"/"+stripname(relpath),'.pdf',".xml")
    print "cachepath:"+cachenamexml
    if caching_enabled and os.path.exists(cachenamexml):
        cacheddate=get_filedate(cachenamexml)
        print "cachedat:",cacheddate,"nowdate:",nowdate
        age=nowdate-cacheddate
        print "cache-age:",age
        
        if host==dev_computer:
            maxcacheage=4*7*24*3600
        if age<timedelta(0,maxcacheage):
            print "Returning cached %s"%(relpath,)
            return open(cachenamexml).read()
        print "Cache too old"
    try:
        pdfdata=getrawdata(relpath,country=country)
    except Exception,cause:
        if host==dev_computer:
            print "Failed to fetch  ",relpath,cause
            try:
                return open(cachenamexml).read()
            except:
                pdfdata=open(cachenamepdf).read()
        else:
            raise
    if not os.path.exists(tmppath):
        os.makedirs(tmppath)
    open(cachenamepdf,"w").write(pdfdata)
    if os.system("pdftohtml -xml -nodrm "+cachenamepdf)!=0:
        raise Exception("pdftohtml failed!")
       
    #modt=int(filedate.strftime('%s'))
    #os.utime(cachenamexml,(modt,modt))
    
    return open(cachenamexml).read() 

def get_raw_aip_sup_page():
    if host==dev_computer:
        try:
            return urlopen("http://www.lfv.se/sv/FPC/IAIP/AIP-SUP/").read()    
        except:
            return open(os.path.join(os.getenv("SWFP_ROOT"),"AIP SUP.html")).read()
    else:
        #TODO: 
        return urlopen("http://www.lfv.se/sv/FPC/IAIP/AIP-SUP/").read()
        
weathercache=dict()
weatherlookup=dict(
       A="http://www.lfv.se/MetInfo.asp?TextFile=llf.esms-day.txt&TextFile=llf.esms-tot.txt&TextFile=llf.esms-n.txt&TextFile=llf.esms-se.txt&TextFile=llf.esms-sw.txt&Subtitle=Omr%e5de%A0A%A0-%A0Prelimin%e4r%A0prognos%A0f%F6r%A0morgondagen&Subtitle=Omr%e5de%A0A%A0-%A0%F6versikt&Subtitle=Omr%e5de%A0A%A0-%A0Norra%A0delen&Subtitle=Omr%e5de%A0A%A0-%A0Syd%F6stra%A0delen&Subtitle=Omr%e5de%A0A%A0-%A0Sydv%e4stra%A0delen&T=Omr%e5de%A0A%A0-%A0S%F6dra%A0Sverige&Frequency=60",
       B="http://www.lfv.se/MetInfo.asp?TextFile=llf.essa-day.txt&TextFile=llf.essa-tot.txt&TextFile=llf.essa-n.txt&TextFile=llf.essa-nw.txt&TextFile=llf.essa-s.txt&TextFile=llf.essa-se.txt&Subtitle=Omr%e5de%A0B%A0-%A0Prelimin%e4r%A0prognos%A0f%F6r%A0morgondagen&Subtitle=Omr%e5de%A0B%A0-%A0%F6versikt&Subtitle=Omr%e5de%A0B%A0-%A0Norra%A0delen&Subtitle=Omr%e5de%A0B%A0-%A0Nordv%e4stra%A0delen&Subtitle=Omr%e5de%A0B%A0-%A0S%F6dra%A0delen&Subtitle=Omr%e5de%A0B%A0-%A0Syd%F6stra%A0delen&T=Omr%e5de%A0B%A0-%A0Mellersta%A0Sverige&Frequency=60",
       C="http://www.lfv.se/MetInfo.asp?TextFile=llf.esnn-day.txt&TextFile=llf.esnn-tot.txt&TextFile=llf.esnn-n.txt&TextFile=llf.esnn-mid.txt&TextFile=llf.esnn-se.txt&TextFile=llf.esnn-sw.txt&Subtitle=Omr%e5de%A0C%A0-%A0Prelimin%e4r%A0prognos%A0f%F6r%A0morgondagen&Subtitle=Omr%e5de%A0C%A0-%A0%F6versikt&Subtitle=Omr%e5de%A0C%A0-%A0Norra%A0delen&Subtitle=Omr%e5de%A0C%A0-%A0Mellersta%A0delen&Subtitle=Omr%e5de%A0C%A0-%A0Syd%F6stra%A0delen&Subtitle=Omr%e5de%A0C%A0-%A0Sydv%e4stra%A0delen&T=Omr%e5de%A0C%A0-%A0Norra%A0Sverige&Frequency=60")
def get_raw_weather_for_area(cur_area2):
    cur_area=cur_area2.upper()
    if host==dev_computer:    
        print "On devcomputer"       
        return open(os.path.join(os.getenv("SWFP_ROOT"),"MetInfo%s.asp"%(cur_area.upper(),))).read()
    cd=weathercache.get(cur_area,None)
    if cd and (datetime.utcnow()-cd['time'])<timedelta(0,1800):
        return cd['data']        
    cd=dict()
    url=weatherlookup[cur_area]
    cd['data']=urlopen(url).read()
    cd['time']=datetime.utcnow()
    weathercache[cur_area]=cd
    return cd['data']
    



