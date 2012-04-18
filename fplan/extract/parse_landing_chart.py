#encoding=utf8
import re
import StringIO
import sys
import math
import cairo
import pickle
import traceback
from itertools import izip
import fplan.lib.mapper as mapper
import md5
import fetchdata
import parse
import svg_reader
import numpy
import numpy.linalg as linalg
import os
import Image
from fplan.lib.blobfile import BlobFile
from datetime import datetime,timedelta

def get_icao_prefix(country):            
    if country=='se':
        return "ES"
    elif country=='ee':
        return "EE"
    elif country=='fi':
        return "EF"
    elif country=='ev':
        return "EV"
    else:
        None
            

def diff(x,y):
    return (x[0]-y[0],x[1]-y[1])
def dist(x,y):
    return math.sqrt((x[0]-y[0])**2+(x[1]-y[1])**2)
def cartesian(xs,ys):
    for x in xs:
        for y in ys:
            yield x,y

            
def chop_up(inputfile,outputfile,level):
    im=Image.open(inputfile)
    w,h=im.size
    fac=1<<level
    w/=fac
    h/=fac
    print "Size",w,h    
    limitx2=256*(int((w+255)/256))
    limity2=256*(int((h+255)/256))
    blob=BlobFile(outputfile,0,
            0,0,limitx2,limity2,'w')
    for x in xrange(0,limitx2,256):
        for y in xrange(0,limity2,256):
            view=im.crop((fac*x,fac*y,fac*(x+256),fac*(y+256)))
            view=view.resize((256,256),Image.ANTIALIAS)
            view.save("tmp/temp%d_%d_%d.png"%(level,x,y))
            io=StringIO.StringIO()
            view.save(io,'png')
            io.seek(0)
            pngdata=io.read()
            blob.add_tile(x,y,pngdata)
    blob.close()
    pass
def get_all_issues(blobname):
    icao=blobname[0:4]
    tmppath=os.path.join(os.getenv("SWFP_DATADIR"),"adcharts",icao)
    out=[]
    #print "tmppath:",tmppath
    for afile in os.listdir(tmppath):
        m=re.match(r"^%s\.(.*)-0.bin$"%(blobname,),afile)
        if m:
            tmppath2=os.path.join(tmppath,afile)
            stamp=os.path.getmtime(tmppath2)
            out.append(dict(cksum=m.groups()[0],stamp=stamp))
    return out
    
            
def parse_landing_chart(path,arppos,icao,country='se',variant=''):
    icao=icao.upper()
    if variant and not variant.startswith("."):
        variant="."+variant
    print "Running parse_landing_chart"
    print "country:",country
    #p=parse.Parser(path,country=country)
    arppos=mapper.from_str(arppos)
    res=[]    
    #assert p.get_num_pages()<=2
    url=fetchdata.getrawurl(path,country=country)
    ret=dict()
    ret['url']=url
    data,nowdate=fetchdata.getdata(path,country=country,maxcacheage=7200)
    cksum=md5.md5(data).hexdigest()
    ret['checksum']=cksum
    #page=p.parse_page_to_items(0, donormalize=False)
    #ret['width']=page.width
    #ret['height']=page.height
    #width=page.width
    #height=page.height
    #scale=2048.0/min(width,height)
    #width*=scale
    #height*=scale
    #width=int(width+0.5)
    #height=int(height+0.5)
    
    blobname=icao+variant
    
    tmppath=os.path.join(os.getenv("SWFP_DATADIR"),"adcharts",icao)
    if not os.path.exists(tmppath):
        os.makedirs(tmppath)
    assert len(icao)==4
    outpath=os.path.join(tmppath,blobname+"."+cksum+".png")
    def render(inputfile,outputfile):
        ext=inputfile.split(".")[-1].lower()
        if ext=='pdf':
            r="pdftoppm -f 0 -l 0 -scale-to 2500 -png -freetype yes -aa yes -aaVector yes %s >%s"%(
                      inputfile,outputfile)
            print "rendering",r
            assert 0==os.system(r)
        elif ext=='jpg' or ext=='png':
            assert 0==os.system("convert -adaptive-resize 2500x2500 %s %s"%(inputfile,outputfile))            
        else:
            raise Exception("Unknown landing chart format: %s"%(inputfile,))
            
    ret['image']=blobname+"."+cksum+".png"
    fetchdata.getcreate_derived_data_raw(
                path,outpath,render,"png",country=country)
    
    outpath2=os.path.join(tmppath,blobname+"."+cksum+".2.png")
    def greyscale(input,output):
        assert 0==os.system("convert -define png:color-type=3 -depth 8 -type Palette -define \"png:compression-level=9\" %s %s"%(input,output))
    
    fetchdata.getcreate_local_data_raw(
                outpath,outpath2,greyscale)
    i=Image.open(outpath2)
    width,height=i.size
    #ret['width']=page.width
    #ret['height']=page.height    
    ret['render_width']=width
    ret['render_height']=height
 
    if country!='raw':
        icao_prefix=get_icao_prefix(country)
        assert icao.startswith(icao_prefix)
    
    for level in xrange(5):
        hashpath=os.path.join(tmppath,"%s.%s-%d.bin"%(blobname,cksum,level))
        fetchdata.getcreate_local_data_raw(
                    outpath2,hashpath,lambda input,output:chop_up(input,output,level))    

    
    ret['blobname']=blobname
    ret['variant']=variant
    
    return ret


def help_plc(ad,url,icao,arp,country,variant=""):
    f=open("parse_landing_chart.log","a")
    try:
        icao=icao.upper()
        lc=parse_landing_chart(
                url,
                icao=icao,
                arppos=arp,country=country,variant=variant)
        ad.setdefault('adcharts',dict())[variant]=lc
        f.write("Success for airport: %s\n\n"%(icao,))
    except KeyboardInterrupt:
        raise        
    except Exception:
        f.write("Failed for airport: %s\n%s\n\n"%(icao,traceback.format_exc()))
    f.close()
    
def get_filedate(path):
    return datetime.utcfromtimestamp(os.path.getmtime(path))
def get_fileage(path):
    d=get_filedate(path)
    return datetime.utcnow()-d

                
        

def get_chart(blobname,cksum,level):
    icao=blobname[0:4]
    tmppath=os.path.join(os.getenv("SWFP_DATADIR"),"adcharts",icao)
    blobpath=os.path.join(tmppath,"%s.%s-%d.bin"%(blobname,cksum,level))
    return open(blobpath).read(),cksum

def get_chart_png(chartname,cksum):
    icaoprefix=chartname[0:4].upper()
    tmppath=os.path.join(os.getenv("SWFP_DATADIR"),"adcharts",icaoprefix)
    pngpath=os.path.join(tmppath,chartname+"."+cksum+".2.png")
    return open(pngpath).read()

def get_width_height(chartname,cksum):
    icao=chartname[0:4]
    tmppath=os.path.join(os.getenv("SWFP_DATADIR"),"adcharts",icao)
    pngpath=os.path.join(tmppath,chartname+"."+cksum+".2.png")
    im = Image.open(pngpath)
    return im.size

def get_timestamp(blobname,cksum,level):
    icao=blobname[0:4]
    tmppath=os.path.join(os.getenv("SWFP_DATADIR"),"adcharts",icao)
    path=os.path.join(tmppath,"%s.%s-%d.bin"%(blobname,cksum,level))
    return os.path.getmtime(path)


if __name__=='__main__':
    if len(sys.argv)>1:
        cur_icao=sys.argv[1]
    else:
        cur_icao='ESMQ'    
    arppos=mapper.parse_coords("564108N","0161715E")
    ret=parse_landing_chart("/AIP/AD/AD 2/%s/ES_AD_2_%s_2_1_en.pdf"%(cur_icao,cur_icao),icao=cur_icao,arppos=arppos)
    print "returns",ret
