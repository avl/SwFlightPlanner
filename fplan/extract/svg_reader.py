import fetchdata
from datetime import datetime,timedelta
import os
from xml.etree import ElementTree
    
def getsvg(path,pagenr,usecache=True):
    assert type(pagenr)==int
    inputfile=fetchdata.getdatafilename(path,country="se",maxcacheage=7200)
    
    svged=fetchdata.getcachename(path,'svg')
    if os.path.exists(svged) and usecache:
        cacheddate=fetchdata.get_filedate(svged)
        print "Cached svg version exists, date:",svged,cacheddate
        if fetchdata.is_devcomp() or datetime.now()-cacheddate<timedelta(0,86400/2):
            print "Using svg cache"
            try:
                return open(svged).read()
            except Exception,cause:
                print "Couldn't read cached svg version",cause
    else:
        print "Re-parsing .svg"
        if os.path.exists(svged):
            os.unlink(svged)
        assert 0==os.system("pdf2svg \"%s\" \"%s\" %d"%(inputfile,svged,pagenr+1))
        assert os.path.exists(svged)
        return open(svged).read()
    
    
def parsesvg(path,pagenr,usecache=True):
    assert type(pagenr)==int
    svgdata=getsvg(path,pagenr,usecache)
    return ElementTree.fromstring(svgdata)
    