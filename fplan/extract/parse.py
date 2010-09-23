#!/usr/bin/python
#encoding=utf8

#Doesn't actually parse pdf-files, requires them to have been
#turned into xml using pdftohtml

from xml.etree import ElementTree
import fetchdata
import re


class Item(object):
    def __init__(self,text,x1,y1,x2,y2,font=None,fontsize=None):
        self.text=text
        self.x1=x1
        self.y1=y1
        self.x2=x2
        self.y2=y2
        self.font=font
        if fontsize!=None: fontsize=int(fontsize)
        self.fontsize=fontsize
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

class Page(object):
    def __init__(self,items):
        self.items=items
    def count(self,str):
        cnt=0
        for item in self.items:
            cnt+=item.text.count(str)
        return cnt
    def get_by_regex(self,regex):
        out=[]
        for item in self.items:
            if re.match(regex,item.text):
                out.append(item)
        return out
    def get_all_items(self):
        return self.items
    def get_partially_in_rect(self,x1,y1,x2,y2,ysort=False,xsort=False):
        out=[]
        #print "Extracting %d-%d"%(y1,y2)
        for item in self.items:
            #print "Considering item: %s"%(item,)
            if item.x2<x1: continue;
            if item.x1>x2: continue;
            if item.y2<y1: continue;
            if item.y1>y2: continue;
            #print "         ^Selected"
            out.append(item)
        if xsort:
            out.sort(key=lambda x:x.x1)
        if ysort:
            out.sort(key=lambda x:x.y1) 
        #print "Returning: %s"%(out,)       
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
    def get_lines(self,items,fudge=0.25,meta=None):
        si=sorted(items,key=lambda x:x.x1)
        si=sorted(si,key=lambda x:x.y1)
        last=None
        out=[]
        linesize=None
        for item in si:
            if last==None:
                out.append(ItemStr(item.text.strip()))
                out[-1].expandbb(item)
                last=item
                continue
            new_linesize=abs(last.y1-item.y1)
            if new_linesize<fudge:
                old=out[-1]
                out[-1]=ItemStr(out[-1]+" "+item.text.strip())
                out[-1].expandbb(old)
                out[-1].expandbb(item)
            else:
                if linesize==None:
                    linesize=new_linesize
                else:
                    if new_linesize>1.75*linesize:
                        assert len(out)>0
                        out.append(ItemStr(""))
                        out[-1].x1=min(out[-2].x1,item.x1)
                        out[-1].x2=max(out[-2].x2,item.x2)
                        out[-1].y1=out[-2].y2
                        out[-1].y2=item.y1
                        
                out.append(ItemStr(item.text.strip()))
                out[-1].expandbb(item)
            last=item
        return out
        
class Parser(object):
    def load_xml(self,path,loadhook=None):
        raw=fetchdata.getxml(path)
        
        if loadhook:
            raw=loadhook(raw)
           
        xml=ElementTree.fromstring(raw)        
        return xml
        
    def get_num_pages(self):
        return len(self.xml.getchildren())
    def parse_page_to_items(self,pagenr):
        page=self.xml.getchildren()[pagenr]
        out=[]
        fonts=dict()
        for fontspec in page.findall(".//fontspec"):
            fontid=int(fontspec.attrib['id'])
            fontsize=int(fontspec.attrib['size'])
            fonts[fontid]=dict(size=fontsize)
        for item in page.findall(".//text"):
            t=[]
            if item.text:
                t.append(item.text)
            for it2 in item.findall(".//*"):
                if it2.text!=None:
                    t.append(it2.text)
                if it2.tail!=None:
                    t.append(it2.tail)                        
            fontid=int(item.attrib['font'])
            fontobj=fonts.get(fontid,None)
            if fontobj:
                fontsize=fontobj.get('size',None)
            else:
                fontsize=None
            #print "Parsed fontid: %d, known: %s (size:%s)"%(fontid,fonts.keys(),fontsize)
            it=Item(text=" ".join(t),
              x1=float(item.attrib['left']),
              x2=float(item.attrib['left'])+float(item.attrib['width']),
              y1=float(item.attrib['top']),
              y2=float(item.attrib['top'])+float(item.attrib['height']),
              font=fontid,
              fontsize=fontsize
              )
            out.append(it)
        
        return Page(list(self.normalize_items(out)))
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
                font=item.font
                )
    
    def __init__(self,path,loadhook=None):
        self.xml=self.load_xml(path,loadhook)


