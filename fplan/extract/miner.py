#TODO Add these back?
"""
    from pdfminer.pdfparser import PDFParser, PDFDocument
    from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
    from pdfminer.pdfdevice import PDFDevice
    from pdfminer.layout import LAParams,LTItem,LTRect,LTTextLineHorizontal,LTTextBoxHorizontal,LTTextLine,LTFigure,LTLine,LTCurve
    from pdfminer.converter import PDFPageAggregator
"""
from parse import ItemStr,Page,Item
from StringIO import StringIO
from fplan.extract.fetchdata import getdata
import fplan.extract.fetchdata as fetchdata
from datetime import datetime,timedelta
import os
import pickle
from fplan.extract.fetchdata import is_devcomp

def get_vertical_lines(stream):
    for item in stream:
        if type(item)==LTTextBoxHorizontal:
            continue
        if type(item)==LTRect:
            yield item.x0,item.y0,item.x1
            yield item.x0,item.y1,item.x1
            continue
        #if type(item)==LTPolygon:
        #    #TODO: SUpport this?
        #    continue
        if type(item)==LTFigure:
            #TODO: SUpport this?
            continue
        if type(item)==LTLine:
            continue
        if type(item)==LTCurve:
            continue
        if type(item)==LTTextLineHorizontal:
            continue
        raise Exception("Unknown type:%s"%(item,))
        
class Continue(Exception):pass
def intersect_line(box,x0,y0,x1):
    if box.x1<=x0 or box.x0>=x1: return None
    if y0>=box.y1 or y0<=box.y0: return None
    subs=list(box)
    subs.sort(key=lambda b:-b.y0)
    for idx,sub in enumerate(subs):
        if sub.y0<y0:
            break
    else:
        return None
    if idx==0: return None
    a=LTTextBoxHorizontal()
    for x in subs[:idx]:
        a.add(x)
    b=LTTextBoxHorizontal()
    for x in subs[idx:]:
        b.add(x)
    
    a.text = ''.join( obj.text for obj in a if isinstance(obj, LTTextLine) )
    b.text = ''.join( obj.text for obj in b if isinstance(obj, LTTextLine) )
    
    return [a,b]
    
    
        
def cutup_textboxes(stream):
    boxes=[]
    for item in stream:
        if type(item)==LTTextBoxHorizontal:
            #print "Encountered:",item.text
            boxes.append(item)
        
    while True:
        try:
            for idx,box in enumerate(boxes):
                for x1,y1,x2 in get_vertical_lines(stream):        
                    splat=intersect_line(box,x1,y1,x2) 
                    if splat:
                        del boxes[idx]
                        boxes.extend(splat)
                        raise Continue            
            break
        except Continue:
            continue
    ret=list(sorted(boxes,key=lambda box:-box.y0))
    #for i in ret:
    #    print ": ",i
    #sys.exit()
    return ret
        
def testparse():
    return parse('/home/anders/saker/avl_fplan_world/precious_aip/poland/Poland_EP_ENR_2_1_en.pdf')

def parse(path,country,maxcacheage=7200,usecache=True):
    mined=fetchdata.getcachename(path,'mined')
    if os.path.exists(mined) and usecache:
        cacheddate=fetchdata.get_filedate(mined)
        print "Cached version exists, date:",mined,cacheddate
        if is_devcomp() or datetime.now()-cacheddate<timedelta(0,86400*3):
            print "Using cache"
            try:
                return pickle.load(open(mined))
            except Exception,cause:
                print "Couldn't unpickle cached parsed version",cause
    print "Re-parsing"
    
    data,date=getdata(path,country=country,maxcacheage=maxcacheage)    
    fp=StringIO(data)    
    # Open a PDF file.
    # fp = open(path, 'rb')
    # Create a PDF parser object associated with the file object.
    parser = PDFParser(fp)
    # Create a PDF document object that stores the document structure.
    doc = PDFDocument()
    # Connect the parser and document objects.
    parser.set_document(doc)
    doc.set_parser(parser)

    doc.initialize("")
    # Check if the document allows text extraction. If not, abort.
    #if not doc.is_extractable:
    #    raise PDFTextExtractionNotAllowed
    # Create a PDF resource manager object that stores shared resources.
    rsrcmgr = PDFResourceManager()
    # Create a PDF device object.
    device = PDFDevice(rsrcmgr)
    # Create a PDF interpreter object.
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    # Process each page contained in the document.
    for page in doc.get_pages():
        interpreter.process_page(page)
        
    # Set parameters for analysis.
    laparams = LAParams()#line_margin=0.75
    # Create a PDF page aggregator object.
    device = PDFPageAggregator(rsrcmgr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    pages=[]
    
    
    
    for idx,page in enumerate(doc.get_pages()):
        interpreter.process_page(page)
        #if idx!=1: continue
        # receive the LTPage object for the page.
        layout = device.get_result()
        page_x1=page_y1=-1e30
        page_x0=page_y0=1e30
        for child in layout:
            page_x0=min(page_x0,child.x0)
            page_x1=max(page_x1,child.x1)
            page_y0=min(page_y0,child.y0)
            page_y1=max(page_y1,child.y1)
        
        def norm(x,y):
            return ((100.0*(x-page_x0)/(page_x1-page_x0)),
                (100.0-100.0*(y-page_y0)/(page_y1-page_y0)))        
        def normalize(*inp):
            x0,y0,x1,y1=inp
            a=norm(x0,y0)
            b=norm(x1,y1)
            ret=a[0],b[1],b[0],a[1]
            #print "normalized(%s) -> %s"%(inp,ret)
            return ret
                    
        #for child in layout:
        #    print "Child:",child
        #    try:
        #        for sub in child:
        #            print "Sub-child:",sub
        #    except:
        #        pass
        #print list(layout)
        cutup=cutup_textboxes(layout)
        items=[]
        for box in cutup:
            subs=[]
            for sub in box:
                x=Item(sub.text,*normalize(sub.x0,sub.y0,sub.x1,sub.y1))
                x.subs='issub'
                subs.append(x)
            item=Item(box.text,*normalize(box.x0,box.y0,box.x1,box.y1))
            item.subs=subs
            items.append(item)
        pages.append(Page(items))
    
    ret=(pages,date)
    f=open(mined,"w")
    pickle.dump(ret,f)
    f.close()
    return pages,date

        
        

          


if __name__=='__main__':
    testparse()
    
