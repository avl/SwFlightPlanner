from time import sleep
import os
import urllib2
import random
from datetime import datetime,timedelta
import sys

def download_notam():
    notamlist=[fname for fname in os.listdir("notams") if fname.isdigit() ]
    if len(notamlist)>0:    
        last=max(notamlist)
        print "Last notam"
        assert int(last)>=0
        lasttext=open("notams/%s"%(last,),"r").read()
    else:
        last=0
        lasttext=""       
    
    nextnotam=int(last)+1
    all_notams_but_seldom_updated=urllib2.urlopen(
                          "http://www.lfv.se/AISInfo.asp?TextFile=odinesaa.txt&SubTitle=&T=SWEDEN&Frequency=250").read()
    north=urllib2.urlopen("http://www.lfv.se/AISInfo.asp?TextFile=odinesun.txt&SubTitle=&T=SWEDEN%20-%20North&Frequency=250").read()
    mid=urllib2.urlopen(  "http://www.lfv.se/AISInfo.asp?TextFile=odinesos.txt&SubTitle=&T=SWEDEN%20-%20Middle&Frequency=250").read()
    south=urllib2.urlopen("http://www.lfv.se/AISInfo.asp?TextFile=odinesmm.txt&SubTitle=&T=SWEDEN%20-%20South&Frequency=250").read()
    print "Downloaded swedish, now Finnish"
    
    finland_n=urllib2.urlopen("http://www.lfv.se/AISInfo.asp?TextFile=odinefps.txt&SubTitle=&T=Finland%20N&Frequency=250").read()
    finland_s=urllib2.urlopen("http://www.lfv.se/AISInfo.asp?TextFile=odinefes.txt&SubTitle=&T=Finland%20S&Frequency=250").read()
    finland_all=urllib2.urlopen("http://www.lfv.se/AISInfo.asp?TextFile=odinefin.txt&SubTitle=&T=Finland&Frequency=250").read()
    print "Downloaded Finnish"
    
    text="\n".join([north,mid,south,
        all_notams_but_seldom_updated,
        finland_n,finland_s,finland_all
        ])
    
    outfile="notams/%08d"%(nextnotam,)
    f=open(outfile,"w")
    f.write(text)
    f.close()    
    print "Downloaded notam (%d bytes) did differ from last stored (%d bytes)"%(len(text),len(lasttext))
    ret=os.system("fplan/lib/notam_db_update.py %s 1"%(outfile,))
    if ret:
        raise Exception("notam_db_update failed: %s"%(ret,))


def clean_notam_files():
    now=datetime.now()
    too_old=[]
    for fname in sorted(os.listdir("notams")):
        if not fname.isdigit():
            continue
        path="notams/"+fname
        stamp=datetime.fromtimestamp(os.path.getmtime(path))
        age=now-stamp            
        if age>timedelta(days=31):
            too_old.append(path)
            if len(too_old)>500:
                break
    if len(too_old)>=500:
        if os.system("tar -cjf %s %s"%(too_old[0]+".tar.bz2"," ".join(too_old)))==0:
            print "Zipped %d notam files"%(len(too_old),) 
            for p in too_old:
                os.unlink(p)
        
                                

def download_notams():
    if not os.path.exists("notams"):
        os.makedirs("notams")
    while True:
        try:
            download_notam()
            clean_notam_files()
        except Exception,cause:
            print "download failed:",cause
            raise
        print "Time now",datetime.utcnow()
        sleep(random.randrange(3600,4000))        
    


if __name__=="__main__":
    if len(sys.argv)>1 and sys.argv[1]=='clean':
        clean_notam_files()
    else:
        download_notams()
    
