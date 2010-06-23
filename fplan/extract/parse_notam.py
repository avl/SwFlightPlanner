import re
from difflib import Differ,SequenceMatcher
from fplan.model import *    
from datetime import datetime

class NotamItem(object):
    def __init__(self,appearline,category):
        self.text=""
        self.appearline=appearline
        self.category=category
    def __cmp__(self,o):
        if type(o)!=NotamItem: raise Exception("Bad type")
        if type(self)!=NotamItem: raise Exception("Bad type")
        return cmp((self.category,self.text),(o.category,o.text))
    def __hash__(self):
        return hash((self.category,self.text))
    def __repr__(self):
        return "NotamItem(line=%d,category=%s,text_fragment=%s)"%(self.appearline,self.category,self.text.split("\n")[0][:50])
class Notam(object):
    def __init__(self,issued,downloaded,items,notamtext):
        self.issued=issued
        self.downloaded=downloaded
        self.items=items
        self.notamtext=notamtext
    def __cmp__(self,o):
        return self.issued==o.issued and self.items==o.items
    def __hash__(self):
        return hash((self.issued,self.items))

def parse_notam(html):
    almostraw="\n".join(pre for pre in re.findall(u"<pre>(.*?)</pre>",html,re.DOTALL))
    ls=almostraw.splitlines(1)
    out=[]
    category=None
    issued=None
    stale=True
    for appearline,l in enumerate(ls):
        cat=re.match(r"([^\s/]+/.*)\s*",l)
        if cat:
            category=cat.groups()[0].strip()
            continue
        if len(l) and l[0]=='+':
            l=' '+l[1:]
        l=l.lstrip()
        if l.strip()=="CONTINUES ON NEXT PAGE": continue
        if l.strip()=="END OF AIS FIR INFORMATION": continue
        
        iss=re.match(r"\s*AIS FIR INFORMATION\s+ISSUED\s+(\d{6})\s+(\d{4})\s+SFI\d+\s+PAGE\s+\d+\(\d+\)\s*",l)
        if not iss:
            iss=re.match(r"ISSUED BY ODIN ESSA AIS\s+(\d{6})\s+(\d{4})\s+HAVE A NICE FLIGHT",l)
        #print "iss match <%s>: %s"%(l,iss!=None)
        if iss: 
            date,time=iss.groups()
            issued2=datetime.strptime("%s %s"%(date,time),"%y%m%d %H%M")            
            if issued:
                assert issued2==issued
            else:
                issued=issued2
            continue
        if re.match(r"\s*Last\s+updated\s+.* UTC \d{4}\s*",l):continue
        if re.match(r"\s*ALL ACTIVE AND INACTIVE NOTAM INCLUDED\s*",l):continue
        if re.match(r"\s*VALID\s+\d+-\d+\s*ALL\s*FL\s*CS:WWWESAA",l):continue

        if l=="":
            if len(out) and out[-1].text!="":
                stale=True
        else:
            if len(out)==0 or stale: 
                stale=False
                out.append(NotamItem(appearline,category))
            if category!=out[-1].category:
                out.append(NotamItem(appearline,category))
            if out[-1].text!="":
                out[-1].text+=" "
            out[-1].text+=l

    def normalize_item(text):
        return "\n".join([x.strip() for x in text.splitlines() if x.strip()])
    items=[]
    for b in out:
        b.text=normalize_item(b.text)
        if b.text:
            items.append(b)
    downloaded=datetime.utcnow()
    notam=Notam(issued,downloaded,items,"".join(ls))
    return notam
    

def how_similar(at,bt):
    #print "Hos similar:\n%s\n/\n%s"%(at,bt)
    aobj=at
    bobj=bt
    a=aobj.text
    b=bobj.text
    if aobj.category!=bobj.category: 
        #print "similar: 0 c"
        return 0
    afirst=a.splitlines()[0]
    bfirst=b.splitlines()[0]
    if afirst.strip()!=bfirst.strip(): 
        #print "similar: 0 f"
        return 0
    awords=set([x.strip() for x in re.split("\s+",a) if x.strip()])
    bwords=set([x.strip() for x in re.split("\s+",b) if x.strip()])
    #print "Unioncount:%d, maxcount: %d"%(len(awords.intersection(bwords)),max(len(awords),len(bwords)))
    res=100.0*len(awords.intersection(bwords))/float(max(len(awords),len(bwords)))
    #print "Similar: ",res
    return res

    
def diff_notam(a,b):
    #print "Diffing a,b: \n%s\n--------\n%s"%(a.notamtext[:100],b.notamtext[:100])
    aset=set(a.items)
    bset=set(b.items)
    #print "A-items:%s"%(aset,)
    #print "B-items:%s"%(bset,)
    new=bset.difference(aset)
    cancelled=aset.difference(bset)
    #print "Raw cancelled:",cancelled
    #print "Raw new:",new
    modified=set()
    cancelledlist=list(cancelled)
    if len(new):
        for c in cancelledlist:
            cand=max(new,key=lambda n:how_similar(c,n))
            if how_similar(c,cand)>70:
                cancelled.remove(c)
                new.remove(cand)
                modified.add((c,cand))                    
    
    if False:
        for n in sorted(modified):
            print "\n=============================\nModified:\n%s\ninto\n%s"%n
        for n in sorted(new):
            print "New: %s/%s"%(n.category,n.text)
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


