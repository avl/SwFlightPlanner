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
    
    
    
    all_notams=[]
    for url_ in [
        "https://www.aro.lfv.se/Links/Link/ViewLink?TorLinkId=161&type=AIS",
        "https://www.aro.lfv.se/Links/Link/ViewLink?TorLinkId=163&type=AIS",
        "https://www.aro.lfv.se/Links/Link/ViewLink?TorLinkId=164&type=AIS",
        "https://www.aro.lfv.se/Links/Link/ViewLink?TorLinkId=160&type=AIS",
        "https://www.aro.lfv.se/Links/Link/ViewLink?TorLinkId=166&type=AIS",
        "https://www.aro.lfv.se/Links/Link/ViewLink?TorLinkId=167&type=AIS",
        "https://www.aro.lfv.se/Links/Link/ViewLink?TorLinkId=168&type=AIS"
                 ]:
        print "Downloading",url_ 
        all_notams.append(urllib2.urlopen(
                          url_).read())
        
    
    print "Downloaded all"
    
    
    text="\n".join(
        all_notams)
    
    outfile="notams/%08d"%(nextnotam,)
    #force diff
    #text="5_- "+text
    f=open(outfile,"w")
    f.write(text)
    f.close()
    if text!=lasttext:     
        print "Downloaded notam (%d bytes) did differ from last stored (%d bytes)"%(len(text),len(lasttext))
    else:
        print "Downloaded notam did not differ from last"
        
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
    
