#!/usr/bin/python
#encoding=utf8

#Doesn't actually parse pdf-files, requires them to have been
#turned into xml using pdftohtml

from elementtree import ElementTree
import fetchdata

class Item(object):
    def __init__(self,text,x1,y1,x2,y2):
        self.text=text
        self.x1=x1
        self.y1=y1
        self.x2=x2
        self.y2=y2
    def __repr__(self):
        return "Item(%.1f,%.1f - %.1f,%.1f : %s)"%(self.x1,self.y1,self.x2,self.y2,repr(self.text))

class Parser(object):
    def load_xml(self,path,loadhook=None):
        raw=fetchdata.getxml(path)
        
        if loadhook:
            raw=loadhook(raw)
           
        xml=ElementTree.fromstring(raw)
        return xml
        
    def get_num_pages(self):
        return len(self.xml.getchildren()[1:])
    def parse_page_to_items(self,pagenr):
        page=self.xml.getchildren()[pagenr+1]
        items=[Item(text=unicode(item.text),
              x1=float(item.attrib['left']),
              x2=float(item.attrib['left'])+float(item.attrib['width']),
              y1=float(item.attrib['top']),
              y2=float(item.attrib['top'])+float(item.attrib['height'])
              ) for item in page.findall("text")]
        return items
        
    def normalize_items(self,items):
        minx=min(x.x1 for x in items)
        miny=min(x.y1 for x in items)
        maxx=max(x.x2 for x in items)
        maxy=max(x.y2 for x in items)
        xfactor=maxx-minx
        yfactor=maxy-miny
        for item in items:
            yield Item(
                text=item.text,
                x1=100.0*(item.x1-minx)/xfactor,
                y1=100.0*(item.y1-miny)/yfactor,
                x2=100.0*(item.x2-minx)/xfactor,
                y2=100.0*(item.y2-miny)/yfactor
                )
    
    def __init__(self,path,loadhook=None):
        self.xml=self.load_xml(path,loadhook)


