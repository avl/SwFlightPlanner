import re
from difflib import Differ,SequenceMatcher
from fplan.model import *    
from datetime import datetime

def fragment(text):
    if len(text)<=100: return text.replace("\n","\\n")
    return (text[:50]+"..."+text[-50:]).replace("\n","\\n")
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
        return "NotamItem(line=%d,category=%s,text_fragment=<%s>)"%(self.appearline,self.category,fragment(self.text))
class Notam(object):
    def __init__(self,downloaded,items,notamtext):
        self.downloaded=downloaded
        self.items=items
        self.notamtext=notamtext
    def __cmp__(self,o):
        return self.items==o.items
    def __hash__(self):
        return hash(self.items)
def normalize_item(text):
    return "\n".join([x.strip() for x in text.splitlines() if x.strip()])


strange_skavsta_notam=normalize_item(
"""584957N0164459E 585018N0164624E 585016N0164836E 584909N0164927E
584744N0164824E 584740N0164633E 584808N0164529E 584957N0164459E
JONAKER-NYKOPING-OXELOSUND
584611N0164031E 584406N0164013E 583747N0165647E 583829N0171100E
584738N0170649E 584611N0164031E
TYSTBERGA
585149N0171322E 585149N0171518E 585110N0171603E 585027N0171535E
585021N0171402E 585106N0171233E 585149N0171322E.
26JUL10 0931 - PERM (ES/1/B2322/10)""")

def fixup(x):
    if x==strange_skavsta_notam:
        print "found strange skavsta notam"
        x="VISUAL APCH NOT PERMITTED WI FOLLOWING AREAS\nSTIGTOMTA\n"+x
    return x

def parse_notam(html):
    print "html lines:",html.count("\n")
    almostraw="\n".join(pre for pre in re.findall(u"<pre>(.*?)</pre>",html,re.DOTALL|re.IGNORECASE))
    almostraw.replace("\r\n","\n")
    almostraw=almostraw.replace("\t","    ")
    #print "Raw lines: %d"%(almostraw.count("\n"),)
    
    def fixer(x):
        #print "Match: <%s>"%(x.group(),)
        return u""
    if 1:
        almostraw=re.sub(
        ur" *\n. *CONTINUES ON NEXT PAGE *\n. *\n *AIS *[^\n]* *INFORMATION *ISSUED *[\d ]*[^\n]*\d+ *PAGE *\d+\(\d+\) *\n *\n",
        lambda x: fixer(x),
        almostraw)        
    #print almostraw
    
    ls=almostraw.splitlines(1)
    out=[]
    category=None
    stale=True
    for appearline,l in enumerate(ls):
        cat=re.match(r"([^\s/]+/.*)\s*",l)
        if cat:
            category=cat.groups()[0].strip()
            continue
        if l.strip()=="ESGT":
            category="ESGT"
            continue
        if len(l) and l[0]=='+':
            l=' '+l[1:]
        l=l.lstrip()
        	
        #if re.match("AIS AREA INFORMATION ISSUED \d+ \d+ SDI\d+ PAGE \d+(\d+)",l.strip()): continue

        if l.strip()=="END OF AIS FIR INFORMATION": continue
        if l.strip()=="ALL ACTIVE AND INACTIVE NOTAM INCLUDED": continue
        if l.strip()=="FIR: ESAA": continue
        if l.strip()=="AERODROMES INCLUDED: ALL": continue            
        if l.strip()=="INSIGNIFICANT NOTAM INCLUDED, EXCEPT OLD PERM NOTAM": continue
        if re.match(r"VALID\s*\d+-\d+\s*ALL\s*FL\s*CS.{3,19}",l.strip()): continue
        iss=re.match(r"\s*AIS\s*(?:FIR|AREA)\s*INFORMATION\s+ISSUED\s+(\d{6})\s+(\d{4})\s+...\d+\s+PAGE\s+\d+\(\d+\)\s*",l)
        if not iss:
            iss=re.match(r"ISSUED BY ODIN ESSA AIS\s+(\d{6})\s+(\d{4})\s+HAVE A NICE FLIGHT",l)
        #print "iss match <%s>: %s"%(l,iss!=None)
        if iss: 
            date,time=iss.groups()
            #print "Issued:",date,time
            continue
        if re.match(r"\s*Last\s+updated\s+.* UTC \d{4}\s*",l):continue
        if re.match(r"\s*ALL ACTIVE AND INACTIVE NOTAM INCLUDED\s*",l):continue
        if re.match(r"\s*VALID\s+\d+-\d+\s*ALL\s*FL\s*CS:WWWESAA",l):continue
        #print "Parsing <%s>"%(l,)
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

    for b in out:
        b.text=fixup(normalize_item(b.text))        

    items=[]
    seen=set()
    for b in out:
        if b.text and not (b.text in seen):
            seen.add(b.text)
            items.append(b)
    print "Items:",len(items)
    downloaded=datetime.utcnow()
    notam=Notam(downloaded,items,"".join(ls))
    return notam
    

def how_similar(at,bt):
    aobj=at
    bobj=bt
    a=aobj.text
    b=bobj.text
    if aobj.text.count("TYSTBERGA") or bobj.text.count("TYSTBERGA"):
        print "How similar:\n%s\n/\n%s"%(at,bt)
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
            if len(new)==0: break
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
    d1=parse_notam(unicode(open("./fplan/extract/notam_sample6.html").read(),'latin1'))
    #d2=parse_notam(unicode(open("./fplan/extract/notam_sample2.html").read(),'latin1'))
    #diff_notam(d1,d2)
    #for item in d2.items:
    #    print item
    #print d2
    


