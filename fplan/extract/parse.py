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
    def __init__(self,text,x1,y1,x2,y2,font=None,fontsize=None,bold=False,italic=False):
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
    def __init__(self,items):
        self.items=items
    def count(self,str):
        cnt=0
        for item in self.items:
            cnt+=item.text.count(str)
        return cnt
    def get_by_regex(self,regex,flags=0):
        out=[]
        for item in self.items:
            if re.match(regex,item.text,flags):
                out.append(item)
        return out
    def get_by_regex_in_rect(self,regex,x1,y1,x2,y2,flags=0):
        out=[]
        #print "Question:",x1,y1,x2,y2
        for item in self.items:
            ##if item.text.count("FREQUENCY"):
            #    print "- Candidate:",item
            if item.x2<x1: continue;
            if item.x1>x2: continue;
            if item.y2<y1: continue;
            if item.y1>y2: continue;
            #if item.text.count("FREQUENCY"):
            #    print "*  Candidate:",item 
            if re.match(regex,item.text,flags):
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
    def get_lines(self,items,fudge=0.40,meta=None):
        si=sorted(items,key=lambda x:x.x1)
        si=sorted(si,key=lambda x:x.y1)
        if len(si)<=0:
            return []
        if len(si)==1:
            ret=ItemStr(si[0].text.strip())
            ret.expandbb(si[0])
            return [ret]        
        last=si[0]
        cand=[[]]
        linesize=None
        for item in si:
            delta=item.y1-last.y1
            if delta<fudge:
                cand[-1].append(item)
            else:
                cand.append([item])
                if last:
                    if linesize: 
                        linesize=min(linesize,delta)
                    else:
                        linesize=delta
            last=item
            
        out=[]
        lastline=None
        for c in cand:
            #print "  Cand: %s"%(c,),"linesize:",linesize
            last=None
            for item in sorted(c,key=lambda x:x.x1):
                
                if lastline:
                    delta=item.y1-lastline.y2
                    #print "delta",delta
                    if (delta>1.5*(lastline.y2-lastline.y1) or (linesize and delta>linesize*1.5)) and len(out)>0:
                        out.append(ItemStr(""))
                        out[-1].x1=min(out[-2].x1,item.x1)
                        out[-1].x2=max(out[-2].x2,item.x2)
                        out[-1].y1=out[-2].y2
                        out[-1].y2=item.y1
                        #print "Inserted newline",out[-1]
                lastline=item
                if last==None:
                    out.append(ItemStr(item.text.strip()))
                    out[-1].expandbb(item)
                else:                                                                                        
                    if item.x1>last.x2-3:
                        repcnt=max(int(item.x1-last.x2),1)  
                        expandedspaces="".join(repeat(" ",repcnt))
                        out[-1]=ItemStr(out[-1]+expandedspaces+item.text.strip())
                        out[-1].expandbb(last)
                        out[-1].expandbb(item)
                    else:
                        out.append(ItemStr(item.text.strip()))
                        out[-1].expandbb(item)
                last=item
        return out                
        
            
            
            
        last=None
        out=[]
        linesize=None
        
        
        
"""        
        def is_right_order(old,item):
            if old.x2>item.x1+7.0:
                print "Wrong order: %s - %s"%((old.x1,old.y1,old.x2,old.y2,old),item)
                return False
            return True
            #assert old.x2<item.x1
        for item in si:
            if last==None:
                out.append(ItemStr(item.text.strip()))
                out[-1].expandbb(item)
                last=item
                continue
            ystep=abs(last.y1-item.y1)
            print "\n**Last: %s, cur: %s"%(last,item)
            old=out[-1]
            same_line=True
            if linesize==None:
                if ystep<fudge:
                    same_line=True
                else:
                    same_line=False
            else:
                ldiff=abs(ystep-linesize)
                print "New linesize:",ystep,"linesize:",linesize
                print "ldiff:",ldiff,"linesize:",ystep
                if ldiff<fudge:
                    same_line=True
            if same_line and not is_right_order(old,item):
                if old.x2<item.x1+1.0:
                    #TODO: MAke clearer: First calculate lines locations, then assign content to them!
                    
            elif same_line and is_right_order(old,item):
                repcnt=max(int(item.x1-old.x2),1)  
                expandedspaces="".join(repeat(" ",repcnt))
                out[-1]=ItemStr(out[-1]+expandedspaces+item.text.strip())
                out[-1].expandbb(old)
                out[-1].expandbb(item)
            else:
                print "Not same line: ",last,item
                if linesize==None:
                    assert ystep>0
                    linesize=ystep
                else:
                    if ystep>1.75*linesize:
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
"""

class Parser(object):
    def load_xml(self,path,loadhook=None,country="se"):
        raw=fetchdata.getxml(path,country=country)
        
        if loadhook:
            raw=loadhook(raw)
        url=fetchdata.getrawurl(path,country)
        xml=ElementTree.fromstring(raw)        
        
        self.fonts=dict()
        for page in xml.getchildren():
            for fontspec in page.findall(".//fontspec"):
                fontid=int(fontspec.attrib['id'])
                fontsize=int(fontspec.attrib['size'])
                if fontid in self.fonts:
                    assert self.fonts[fontid]['size']==fontsize
                self.fonts[fontid]=dict(size=fontsize)
        
        return url,xml
        
    def get_num_pages(self):
        return len(self.xml.getchildren())
    def parse_page_to_items(self,pagenr):
        page=self.xml.getchildren()[pagenr]
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
            else:
                fontsize=None

            #print "Parsed fontid: %d, known: %s (size:%s)"%(fontid,fonts.keys(),fontsize)
            it=Item(text=" ".join(t),
              x1=float(item.attrib['left']),
              x2=float(item.attrib['left'])+float(item.attrib['width']),
              y1=float(item.attrib['top']),
              y2=float(item.attrib['top'])+float(item.attrib['height']),
              font=fontid,
              fontsize=fontsize,
              bold=bold,
              italic=italic
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
                font=item.font,
                bold=item.bold,
                italic=item.italic
                )
    def get_url(self):
        return self.url
    def __init__(self,path,loadhook=None,country="se"):
        self.url,self.xml=self.load_xml(path,loadhook,country=country)


