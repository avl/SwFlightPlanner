import os
import traceback
import md5
import fetchdata

def help_parse_doc(ad,url,icao,country,title,category):
    f=open("aip_text_documents.log","a")
    try:
        ret=parse_doc(path=url,icao=icao,title=title,category=category,country=country)
        ad.setdefault('aiptext',[]).append(ret)
        f.write("Succeeded parsing %s %s\n"%(icao,category))
    except Exception:
        f.write("Failed parsing %s %s\n%s\n\n"%(icao,category,traceback.format_exc()))
    f.close()  
    
def get_doc(icao,category,cksum):
    blobname=icao+"_"+category
    tmppath=os.path.join(os.getenv("SWFP_DATADIR"),"aiptext",icao)
    
    if not os.path.exists(tmppath):
        os.makedirs(tmppath)
    path=os.path.join(tmppath,blobname+"."+cksum+".html")
    return open(path).read()
    
    
def parse_doc(path,icao,country,title,category):
    print "Parsing AIP doc"
    icao=icao.upper()
    assert len(icao)==4
    url=fetchdata.getrawurl(path,country=country)
    ret=dict()
    ret['icao']=icao
    ret['url']=url
    ret['title']=title
    ret['name']=icao+" - "+title
    ret['category']=category
    #data,nowdate=fetchdata.getdata(path,country=country,maxcacheage=7200)
    blobname=icao+"_"+category
    tmppath=os.path.join(os.getenv("SWFP_DATADIR"),"aiptext",icao)
    if not os.path.exists(tmppath):
        os.makedirs(tmppath)
    
    if path.lower().endswith("pdf"):
        outpath_inter=os.path.join(tmppath,blobname+".tmp.html")
        def render(inputfile,outputfile):
            r="pdftohtml -i -zoom 2 -noframes -s -c -nodrm %s %s"%(inputfile,outputfile)  #-s is not supported on older pdftohtml, and doesn't appear necessary either.
            print "running",r
            assert 0==os.system(r)
                
        fetchdata.getcreate_derived_data_raw(
                    path,outpath_inter,render,"html",country=country)
        
        whole=open(outpath_inter).read()
        
        fixed=(whole.replace("<BODY bgcolor=\"#A0A0A0\"","<BODY bgcolor=\"#FFFFFF\"")
                .replace("<TITLE>Microsoft Word - ","<TITLE>"))
        
    else:
        assert path.endswith("html")
        fixed,date=fetchdata.getdata(path,country=country)
        
    cksum=md5.md5(fixed).hexdigest()
    outpath=os.path.join(tmppath,blobname+"."+cksum+".html")
    f=open(outpath,"w")
    f.write(fixed)        
    f.close()
    #print "Wrote raw:",out,outpath
        
    ret['checksum']=cksum
    ret['date']=fetchdata.get_filedate(outpath)
    ret['blobname']=blobname
    
    return ret

    
