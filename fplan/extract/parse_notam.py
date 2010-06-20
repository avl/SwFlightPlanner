import re
from difflib import Differ,SequenceMatcher
from fplan.model import *    
from datetime import datetime

class NotamItem(object):
    def __init__(self,linenr):
        self.text=""
        self.linenr=linenr
    def __cmp__(self,o):
        return cmp(self.text,o.text)
    def __hash__(self):
        return hash(self.text)
       
class Notam(object):
    def __init__(self,issued,downloaded,items):
        self.issued=issued
        self.downloaded=downloaded
        self.items=items
        
def notam_from_lines(ls):
    out=[]
    category="unknown"
    issued=None
    stale=True
    for linenr,l in enumerate(ls):
        cat=re.match(r"([^\s/]+/.*)\s*",l)
        if cat:
            category=cat.groups()[0].strip()
            continue
        if len(l) and l[0]=='+':
            l=' '+l[1:]
        l=l.lstrip()
        if l.strip()=="CONTINUES ON NEXT PAGE": continue
        
        iss=re.match(r"\s*AIS FIR INFORMATION\s+ISSUED\s+(\d{6})\s+(\d{4})\s+SFI\d+\s+PAGE\s+\d+\(\d+\)\s*",l)
        if iss: 
            date,time=iss.groups()
            issued2=datetime.strptime("%s %s"%(date,time),"%y%m%d %H%M")            
            if issued:
                assert issued2==issued
            else:
                issued=issued2

        if re.match(r"\s*Last\s+updated\s+.* UTC \d{4}\s*",l):continue
        if re.match(r"\s*ALL ACTIVE AND INACTIVE NOTAM INCLUDED\s*",l):continue
        if re.match(r"\s*VALID\s+\d+-\d+\s*ALL\s*FL\s*CS:WWWESAA",l):continue

        if l=="":
            if len(out) and out[-1][1].text!="":
                stale=True
        else:
            if len(out)==0 or stale: 
                stale=False
                out.append([category,NotamItem(linenr)])
            if category!=out[-1][0]:
                out.append([category,NotamItem(linenr)])
            if out[-1][1].text!="":
                out[-1][1].text+=" "
            out[-1][1].text+=l

    items=[(a,b) for a,b in out if b.text.strip()]
    downloaded=datetime.utcnow()
    notam=Notam(issued,downloaded,items)
    return notam
    
def parse_notam(html):
    return notam_from_lines("\n".join(pre for pre in re.findall(u"<pre>(.*?)</pre>",html,re.DOTALL)).splitlines(1))

def how_similar(at,bt):
    #print "Hos similar:\n%s\n/\n%s"%(at,bt)
    acat,aobj=at
    bcat,bobj=bt
    a=aobj.text
    b=bobj.text
    if acat!=bcat: 
        #print "similar: 0 c"
        return 0
    afirst=a.splitlines()[0]
    bfirst=b.splitlines()[0]
    if afirst.strip()!=bfirst.strip(): 
        #print "similar: 0 f"
        return 0
    awords=set([x.strip() for x in re.split("\s+",a) if x.strip()])
    bwords=set([x.strip() for x in re.split("\s+",b) if x.strip()])
    res=100.0*len(awords.union(bwords))/float(max(len(awords),len(bwords)))
    #print "Similar: ",res
    return res

    
def diff_notam(a,b):
    #print "Diffing a,b: \n%s\n--------\n%s"%(a[:100],b[:100])
    aset=set(a.items)
    bset=set(b.items)
    new=bset.difference(aset)
    cancelled=aset.difference(bset)
    modified=set()
    cancelledlist=list(cancelled)
    for c in cancelledlist:
        cand=max(new,key=lambda n:how_similar(c,n))
        if how_similar(c,cand)>10:
            cancelled.remove(c)
            new.remove(cand)
            modified.add((c,cand))                    
    
    for n in sorted(modified):
        print "\n=============================\nModified:\n%s\ninto\n%s"%n
    for n in sorted(new):
        print "New: %s\n%s"%n
    for c in sorted(cancelled):
        print "Cancelled: %s\n%s"%c
        
    print "Total items: %d/%d, Added: %d, Removed: %d, Modified: %d"%(len(a.items),len(b.items),len(new),len(cancelled),len(modified))
    return dict(
        modified=modified,
        new=new,
        cancelled=cancelled)


if __name__=='__main__':
    d1=parse_notam(unicode(open("./fplan/extract/notam_sample.html").read(),'latin1'))
    d2=parse_notam(unicode(open("./fplan/extract/notam_sample2.html").read(),'latin1'))
    diff_notam(d1,d2)


