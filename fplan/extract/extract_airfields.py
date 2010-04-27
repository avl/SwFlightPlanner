from fetchdata import getxml
from parse import Parser
import re

def parse_coords(lat,lon):
    latdeg=float(lat[0:2])
    latmin=float(lat[2:4])
    latsec=float(lat[4:6])
    londeg=float(lon[0:3])
    lonmin=float(lon[3:5])
    lonsec=float(lon[5:7])
    latdec=latdeg+latmin/60.0+latsec/(60.0*60.0)
    londec=londeg+lonmin/60.0+lonsec/(60.0*60.0)
    return '%.10f,%.10f'%(latdec,londec)
    
def extract_airfields():
    #print getxml("/AIP/AD/AD 1/ES_AD_1_1_en.pdf")
    ads=[]
    p=Parser("/AIP/AD/AD 1/ES_AD_1_1_en.pdf")
    startpage=None
    for pagenr in xrange(p.get_num_pages()):
        page=p.parse_page_to_items(pagenr)
        if page.count("Aerodrome directory"):
            startpage=pagenr
            break
    if startpage==None:
        raise Exception("Couldn't find aerodrome directory in file")
    #print "Startpage: %d"%(startpage,)
    for pagenr in xrange(startpage,p.get_num_pages()):
        row_y=[]
        page=p.parse_page_to_items(pagenr)
        for item in list(page.get_partially_in_rect(10,0,55,100)):
            #print item
            m=re.match(r"\b\d\dR?L?/\d\dR?L?\b",item.text)
            if m:
                if not page.get_partially_in_rect(0,item.y1-0.6,50,item.y1-0.5) and \
                    page.get_partially_in_rect(0,item.y1,item.x1,item.y1+0.5):                    
                    row_y.append(item.y1)
        for y1,y2 in zip(row_y,row_y[1:]+[100.0]):
            #print "Extacting from y-range: %f-%f"%(y1,y2)
            items=list(page.get_partially_in_rect(0,y1-0.25,5.0,y2+0.25,ysort=True))
            if len(items)>=2:
                ad=dict(name=unicode(items[0].text).strip(),
                        icao=unicode(items[1].text).strip()                    
                        )
                if len(items)>=3:
                    #print "Coord?:",items[2].text
                    m=re.match(r".*(\d{6})N\s*(\d{7})E.*",items[2].text)
                    if m:
                        lat,lon=m.groups()
                        ad['pos']=parse_coords(lat,lon)           
                        elev=re.findall(r"(\d{1,5})\s*ft"," ".join(t.text for t in items[3:]))
                        assert len(elev)==1
                        ad['elev']=int(elev[0])                        
                                     
                ads.append(ad)
                
    for ad in ads:
        if not ad.has_key('pos'):
            icao=ad['icao']
            print "Parsing ",icao
            p=Parser("/AIP/AD/AD 2/%s/ES_AD_2_%s_en.pdf"%(icao,icao))
            te=p.parse_page_to_items(0).get_all_text()
            print te
            coords=re.findall(r"(\d{6})N\s*(\d{7})E",te)
            if len(coords)>1:
                raise Exception("First page of airport info (%s) does not contain exactly ONE set of coordinates"%(icao,))
            if len(coords)==0:
                print "Couldn't find coords for ",icao
            ad['pos']=parse_coords(*coords[0])

            elev=re.findall(r"Elevation.*?(\d{1,5})\s*ft",te,re.DOTALL)
            if len(elev)>1:
                raise Exception("First page of airport info (%s) does not contain exactly ONE elevation in ft"%(icao,))
            if len(elev)==0:
                print "Couldn't find elev for ",icao                
            ad['elev']=int(elev[0])
    print ads
    for ad in ads:
        print "%s: %s - %s (%s ft)"%(ad['icao'],ad['name'],ad['pos'],ad['elev'])
    return ads

                
                
    # getxml("/AIP/AD/AD 2/ESSA/ES_AD_2_ESSA_en.pdf")
    
    
            
if __name__=='__main__':
    extract_airfields()
