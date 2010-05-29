from fetchdata import getxml
from parse import Parser
import re
import sys
from fplan.lib.mapper import parse_coord_str
import extra_airfields
from fplan.lib.mapper import parse_coords,uprint
    
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
                    m=re.match(r".*(\d{6}N)\s*(\d{7}E).*",items[2].text)
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
            coords=re.findall(r"(\d{6}N)\s*(\d{7}E)",te)
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
            
            found=False
            for pagenr in xrange(0,p.get_num_pages()):
                page=p.parse_page_to_items(pagenr)
                matches=page.get_by_regex(r".*ATS\s*AIRSPACE.*")
                print "Matches of ATS_AIRSPACE on page %d: %s"%(pagenr,matches)
                if len(matches)>0:
                    heading=matches[0]
                    desigitem,=page.get_by_regex("Designation and lateral limits")
                    vertitem,=page.get_by_regex("Vertical limits")
                    airspaceclass,=page.get_by_regex("Airspace classification")
                    
                    lastname=None
                    subspacelines=dict()
                    subspacealts=dict()
                    for idx,item in enumerate(page.get_lines(page.get_partially_in_rect(desigitem.x2+1,desigitem.y1,100,vertitem.y1-1))):
                        
                        if item.count("ATS airspace not established"):
                            assert idx==0
                            break
                            
                        if item.strip()=="": continue
                        m=re.match(r"(.*?)(\d{6}N\s+.*)",item)
                        if m:
                            name,coords=m.groups()                            
                            name=name.strip()
                        else:
                            name=item.strip()
                            coords=None
                        if name:
                            lastname=name
                        if coords:
                            subspacelines.setdefault(lastname,[]).append(coords)
                        assert lastname
                    lastname=None
                    altnum=0
                    print "Spaces:",subspacelines
                    print "ICAO",ad['icao']
                    altlines=page.get_lines(page.get_partially_in_rect(vertitem.x2+1,vertitem.y1,100,airspaceclass.y1))
                    anonymous_alt=False
                    for item in altlines:
                        if item.strip()=="": continue
                        print "Matchin alt <%s>"%(item,)
                        m=re.match(r"(.*?)(?:(\d{3,5})\s*ft\s*/.*(?:(GND)|(MSL))|\s*(GND)\s*)",item)
                        if not m:
                            continue
                        name,alt,agnd,amsl,gnd=m.groups()
                        print "Matched alt:",name,alt,agnd,amsl,gnd
                        if alt:
                            if agnd:
                                altitude="%s ft GND"%(alt,)
                            else:
                                altitude="%s ft"%(alt,)                                
                        else:
                            altitude="GND"
                        name=name.strip()
                        if not name and altnum==0 and len(subspacelines)==1:
                            name=subspacelines.keys()[0]                        
                        if name:
                            altnum=0
                            lastname=name
                            assert lastname
                            subspacealts.setdefault(lastname,dict())['ceil']=altitude
                            print "Ceiling for %s"%(lastname,)
                        else:
                            print "Altnum:",altnum
                            if altnum==0:
                                #no name even on first!
                                assert not anonymous_alt #only one anonymous allow
                                lastname="*"
                                subspacealts.setdefault(lastname,dict())['ceil']=altitude
                                print "Ceil for %s"%(lastname,)
                            else:
                                assert altnum==1
                                assert lastname
                                subspacealts.setdefault(lastname,dict())['floor']=altitude
                                print "Floor for %s"%(lastname,)
                        altnum+=1
                        
                    spaces=[]
                    print "subspacealts:",subspacealts
                    
                    
                    if not '*' in subspacealts and len(subspacealts)!=len(subspacelines):
                        m=re.match("TIA\s+(\d{3,5}\s*ft\s*/.*(?:(MSL)?|(GND)).*?)\s*TIZ\s+(\d{3,5}\s*ft\s*/.*(?:(MSL)?|(GND)).*?)\s*",altlines[0])
                        def fmt(foot,msl,gnd):
                            if gnd:
                                return "%s"%(foot,)
                            else:
                                return "%s GND"%(foot,)
                        if m:
                            upper,amsl1,agnd1,middle,amsl2,agnd2=m.groups()                        
                            subspacealts['TIZ']=dict(ceil=fmt(middle,amsl2,agnd2),floor="GND") 
                            subspacealts['TIA']=dict(ceil=fmt(upper,amsl1,agnd1),floor=fmt(middle,amsl2,agnd2)) 
                        m=re.match("CTR/TIZ\s+(\d{3,5}\s*ft\s*/.*(?:(MSL)?|(GND)).*?)\s*TIA\s+(\d{3,5}\s*ft\s*/.*(?:(MSL)?|(GND)).*?)\s*",altlines[0])
                        if m:
                            middle,amsl1,agnd1,upper,amsl2,agnd2=m.groups()                        
                            subspacealts['CTR/TIZ']=dict(ceil=fmt(middle,amsl2,agnd2),floor="GND") 
                            subspacealts['TIA']=dict(ceil=fmt(upper,amsl1,agnd1),floor=fmt(middle,amsl2,agnd2)) 
                    
                    
                    for spacename in subspacelines.keys():
                        altspacename=spacename
                        if not spacename in subspacealts:
                            if "*" in subspacealts:
                                altspacename="*"                                
                            elif spacename.split(" ")[-1].strip() in ["TIA","TIZ","CTR","CTR/TIZ"]:
                                short=spacename.split(" ")[-1].strip()
                                if short in subspacealts:
                                   altspacename=short
                                                    
                        space=dict(
                            name=spacename,
                            ceil=subspacealts[altspacename]['ceil'],
                            floor=subspacealts[altspacename]['floor'],
                            points=parse_coord_str(" ".join(subspacelines[spacename]))
                            )
                        spaces.append(space)
                        print space
                        #if ad['icao']=="ESKN":
                        #    sys.exit(1)
                        #sys.exit(1)
                    ad['spaces']=spaces
                    found=True
                if found:
                    break
            assert found 
                            
                            
                            
            #Now find any ATS-airspace
            
    for extra in extra_airfields.extra_airfields:
        ads.append(extra)
            
    print ads
    for ad in ads:
        print "%s: %s - %s (%s ft)"%(ad['icao'],ad['name'],ad['pos'],ad['elev'])
        if 'spaces' in ad:
            print "   spaces: %s"%(ad['spaces'],)
    return ads

                
                
    # getxml("/AIP/AD/AD 2/ESSA/ES_AD_2_ESSA_en.pdf")
    
    
            
if __name__=='__main__':
    extract_airfields()
