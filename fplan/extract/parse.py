#!/usr/bin/python
#encoding=utf8

#Doesn't actually parse pdf-files, requires them to have been
#turned into xml using pdftohtml

from xml.etree import ElementTree
import fetchdata
import re
from itertools import repeat
from copy import copy

class Item(object):
    def __init__(self,text,x1,y1,x2,y2,font=None,fontsize=None,bold=False,italic=False,color="#000000"):
        self.text=text
        self.x1=x1
        self.y1=y1
        self.x2=x2
        self.y2=y2
        self.font=font
        if fontsize!=None: fontsize=int(fontsize)
        self.fontsize=fontsize
        self.bold=bold
        self.italic=italic
        self.color=color
    def __repr__(self):
        return "Item(%.1f,%.1f - %.1f,%.1f : %s)"%(self.x1,self.y1,self.x2,self.y2,repr(self.text))
def uprint(s):
    if type(s)==unicode:
        print s.encode('utf8')
    else:
        print s

class ItemStr(unicode):
    def expandbb(self,item):
        if not hasattr(self,'x1'):
            self.x1=item.x1
            self.y1=item.y1
            self.x2=item.x2
            self.y2=item.y2
        else:
            self.x1=min(item.x1,self.x1)
            self.y1=min(item.y1,self.y1)
            self.x2=max(item.x2,self.x2)
            self.y2=max(item.y2,self.y2)
    def expandbb2(self,item_x1,item_y1,item_x2,item_y2):
        if not hasattr(self,'x1'):
            self.x1=item_x1
            self.y1=item_y1
            self.x2=item_x2
            self.y2=item_y2
        else:
            self.x1=min(item_x1,self.x1)
            self.y1=min(item_y1,self.y1)
            self.x2=max(item_x2,self.x2)
            self.y2=max(item_y2,self.y2)

class Page(object):
    def __init__(self,items,width=None,height=None):
        self.width=width
        self.height=height
        self.items=items
    def count(self,str):
        cnt=0
        for item in self.items:
            cnt+=item.text.count(str)
        return cnt
    def get_by_regex(self,regex,flags=0):
        out=[]
        for item in self.items:
            #if item.text.count("EEKA"):
            if re.match(regex,item.text,flags):
                out.append(item)
        return out
    def get_by_regex_in_rect(self,regex,x1,y1,x2,y2,flags=0):
        out=[]
        for item in self.items:
            #if item.text.count("AD"):
            if item.x2<x1: continue;
            if item.x1>x2: continue;
            if item.y2<y1: continue;
            if item.y1>y2: continue;
            if re.match(regex,item.text,flags):
                out.append(item)
        return out
    def get_all_items(self):
        return self.items
    def get_partially_in_rect(self,x1,y1,x2,y2,ysort=False,xsort=False):
        out=[]
        for item in self.items:
            if item.x2<x1: continue;
            if item.x1>x2: continue;
            if item.y2<y1: continue;
            if item.y1>y2: continue;
            out.append(item)
        if xsort:
            out.sort(key=lambda x:x.x1)
        if ysort:
            out.sort(key=lambda x:x.y1) 
        return out
    def get_all_text(self):
        out=[]
        for item in self.items:
            out.append(item.text)
        return "\n".join(out)
    def get_fully_in_rect(self,x1,y1,x2,y2,ysort=False,xsort=False):
        out=[]
        for item in self.items:
            if item.x1<x1: continue;
            if item.x2>x2: continue;
            if item.y1<y1: continue;
            if item.y2>y2: continue;
            out.append(item)
        if xsort:
            out.sort(key=lambda x:x.x1)
        if ysort:
            out.sort(key=lambda x:x.y1)        
        return out
    
    def get_lines2(self,items,fudge=0.40,meta=None):
        """
        Return a number of lines from a set of input text items,
        each possibly containing its own newline-characters.
        side-effect:Strips newlines out of input text-items
        """
        outitems=[]
        for item in items:
            item=copy(item)
            item.text=item.text.strip()
            if item.text.count("\n"):
                stride=(item.y2-item.y1)/float(item.text.count("\n"))
                assert stride>0.01
                cury=item.y1
                for line in item.text.split("\n"):
                    tmp=copy(item)
                    tmp.text=line
                    tmp.y1=cury
                    tmp.y2=cury+stride*0.99
                    cury+=stride
                    outitems.append(tmp)                
            else:
                outitems.append(item)
        return self.get_lines(outitems,fudge=fudge,meta=meta)
    def get_all_lines(self):
        return self.get_lines(self.items)
    def get_lines(self,items,fudge=0.25,meta=None,order_fudge=5):
        si=sorted(items,key=lambda x:x.x1)
        si=sorted(si,key=lambda x:x.y1)
        if len(si)<=0:
            return []
        if len(si)==1:
            ret=ItemStr(si[0].text.strip())
            ret.expandbb(si[0])
            return [ret]        
        last=None
        cand=[[]]
        linesize=None
        #pre-splitting items into line-groups.
        #Every line-group can later be split into
        #multiple lines, but is never joined
        #with another line group 
        for item in si:
            if last==None:
                cand[-1].append(item)
            else:
                delta=item.y1-last.y1
                if delta<fudge:
                    cand[-1].append(item)
                else:
                    cand.append([item])
                    if linesize: 
                        linesize=min(linesize,delta)
                    else:
                        linesize=delta
            last=item
            
        out=[]
        lastline=None
        for c in cand:
            last=None
            for item in sorted(c,key=lambda x:x.x1):
                if lastline:
                    delta=item.y1-lastline.y2
                    spacing_too_big1=delta>1.0*(lastline.y2-lastline.y1)
                    spacing_too_big2=delta>1.0*(item.y2-item.y1)
                    if  (spacing_too_big1 or spacing_too_big2) and len(out)>0:
                        out.append(ItemStr(""))
                        out[-1].x1=min(out[-2].x1,item.x1)
                        out[-1].x2=max(out[-2].x2,item.x2)
                        out[-1].y1=out[-2].y2
                        out[-1].y2=item.y1
                lastline=item
                if last==None:
                    #this is certainly the start of a new line,
                    #as determined by the line pre-splitting
                    out.append(ItemStr(item.text.strip()))
                    out[-1].expandbb(item)
                else:           
                    #we're inside a line-group. Perhaps we
                    #should join up with the last line, or, if order
                    #is too wrong, as some kind of robustness/mitigation
                    #strategy, create a new line for text that overlaps.                                                                             
                    if item.x1>last.x2-order_fudge:
                        #Order is right, join the two candidates to the same line.
                        repcnt=max(int(item.x1-last.x2),1)
                        expandedspaces="".join(repeat(" ",repcnt))
                        out[-1]=ItemStr(out[-1]+expandedspaces+item.text.strip())
                        out[-1].expandbb(last)
                        out[-1].expandbb(item)
                    else:
                        #Order is wrong, emit a new line.
                        out.append(ItemStr(item.text.strip()))
                        out[-1].expandbb(item)
                last=item
        return out                
        
            
            
            
        last=None
        out=[]
        linesize=None
        
        

class Parser(object):
    def load_xml(self,path,loadhook=None,country="se"):
        raw=fetchdata.getxml(path,country=country)
        
        if loadhook:
            print "Running loadhook"
            bef=raw
            raw=loadhook(raw)
            print "Bef==raw:",bef==raw
        url=fetchdata.getrawurl(path,country)
        xml=ElementTree.fromstring(raw)        
        
        self.fonts=dict()
        for page in xml.getchildren():
            for fontspec in page.findall(".//fontspec"):
                fontid=int(fontspec.attrib['id'])
                fontsize=int(fontspec.attrib['size'])
                fontcolor=fontspec.attrib.get('color','#000000')
                if fontid in self.fonts:
                    assert self.fonts[fontid]['size']==fontsize
                self.fonts[fontid]=dict(size=fontsize,color=fontcolor)
        
        return url,xml
        
    def get_num_pages(self):
        return len(self.xml.getchildren())
    def parse_page_to_items(self,pagenr,donormalize=True):
        page=self.xml.getchildren()[pagenr]
        try:
            width=int(page.attrib['width'])
        except Exception:
            width=None
            return#raise
        try:
            height=int(page.attrib['height'])
        except Exception:
            height=None
            raise
                    
        out=[]
        fonts=self.fonts
        for item in page.findall(".//text"):
            t=[]            
            bold=False
            italic=False
            if item.text:
                t.append(item.text)
            for it2 in item.findall(".//*"):
                if it2.tag=="b": bold=True
                if it2.tag=="i": italic=True
                if it2.text!=None:
                    t.append(it2.text)
                if it2.tail!=None:
                    t.append(it2.tail)                        
            fontid=int(item.attrib['font'])
            fontobj=fonts.get(fontid,None)
            if fontobj:
                fontsize=fontobj.get('size',None)
                color=fontobj.get('color',"#000000")
            else:
                fontsize=None
                color="#000000"

            #print "Parsed fontid: %d, known: %s (size:%s)"%(fontid,fonts.keys(),fontsize)
            if color.lower()=="#ffffff":
                continue
            it=Item(text=" ".join(t),
              x1=float(item.attrib['left']),
              x2=float(item.attrib['left'])+float(item.attrib['width']),
              y1=float(item.attrib['top']),
              y2=float(item.attrib['top'])+float(item.attrib['height']),
              font=fontid,
              fontsize=fontsize,
              bold=bold,
              italic=italic,
              color=color
              )
            out.append(it)
        if donormalize:
            n=self.normalize_items(out)
        else:
            n=out        
        return Page(list(n),width=width,height=height)
    def normalize_items(self,items):
        if len(items)==0:
            return
        minx=min(x.x1 for x in items)
        miny=min(x.y1 for x in items)
        maxx=max(x.x2 for x in items)
        maxy=max(x.y2 for x in items)
        xfactor=float(maxx-minx)
        yfactor=float(maxy-miny)
        for item in items:
            yield Item(
                text=item.text,
                x1=100.0*(item.x1-minx)/xfactor,
                y1=100.0*(item.y1-miny)/yfactor,
                x2=100.0*(item.x2-minx)/xfactor,
                y2=100.0*(item.y2-miny)/yfactor,
                fontsize=item.fontsize,
                font=item.font,
                bold=item.bold,
                italic=item.italic,
                color=item.color
                )
    def get_url(self):
        return self.url
    def __init__(self,path,loadhook=None,country="se"):
        self.url,self.xml=self.load_xml(path,loadhook,country=country)


