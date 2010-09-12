#encoding=utf8
from fetchdata import getxml
from parse import Parser
import re
import sys
from fplan.lib.mapper import parse_coord_str
import extra_airfields
import fplan.lib.mapper as mapper
from pyshapemerge2d import Vertex,Polygon,vvector
from fplan.lib.mapper import parse_coords,uprint
import csv
from fplan.lib.get_terrain_elev import get_terrain_elev
import math
    
def extract_airfields():
    #print getxml("/AIP/AD/AD 1/ES_AD_1_1_en.pdf")
    ads=[]
    p=Parser("/AIP/AD/AD 1/ES_AD_1_1_en.pdf")
    points=dict()
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

        
    big_ad=set()        
    for ad in ads:
        if not ad.has_key('pos'):
            #if ad['icao']!='ESSB':
            #    continue
            big_ad.add(ad['icao'])

    for ad in ads:        
        icao=ad['icao']
        #if icao!='ESOK': continue
        if icao in big_ad:            
            if icao in ['ESIB','ESNY','ESCM','ESPE']:
                continue
            p=Parser("/AIP/AD/AD 2/%s/ES_AD_2_%s_6_1_en.pdf"%(icao,icao))
            
            for pagenr in xrange(p.get_num_pages()):
                page=p.parse_page_to_items(pagenr)
                icao=ad['icao']
                print "Parsing ",icao
                
                """
                for altline in exitlines:
                    m=re.match(r"(\w+)\s+(\d+N)\s*(\d+E.*)",altline)
                    if not m: continue
                    name,lat,lon=m.groups()
                    try:
                        coord=parse_coords(lat,lon)
                    except:
                        continue
                    points.append(dict(name=name,pos=coord))
                """
                
                for kind in xrange(2):
                    if kind==0:
                        hits=page.get_by_regex(r"H[Oo][Ll][Dd][Ii][Nn][Gg]")
                        kind="holding point"
                    if kind==1:
                        hits=page.get_by_regex(r"[Ee]ntry.*[Ee]xit.*point")                    
                        kind="entry/exit point"
                    if len(hits)==0: continue
                    for holdingheading in hits:

                        items=sorted(page.get_partially_in_rect(holdingheading.x1+2.0,holdingheading.y2+0.1,holdingheading.x1+0.5,100),
                            key=lambda x:x.y1)
                        items=[x for x in items if not x.text.startswith(" ")]
                        #print "Holding items:",items
                        for idx,item in enumerate(items):
                            print
                            y1=item.y1
                            if idx==len(items)-1:
                                y2=100
                            else:
                                y2=items[idx+1].y2
                            items2=[x for x in page.get_partially_in_rect(holdingheading.x1,y1+0.3,holdingheading.x1+40,y2-0.1) if x.y1>=item.y1-0.05]
                            s=(" ".join(page.get_lines(items2))).strip()

                            if s.startswith("ft Left/3"): #Special case for ESOK
                                s,=re.match("ft Left/3.*?([A-Z]{4,}.*)",s).groups()
                            if s.startswith("LjUNG"): #Really strange problem with ESCF
                                s=s[0]+"J"+s[2:]
                            if s.lower().startswith("holding"):
                                sl=s.split(" ",1)
                                if len(sl)>1:
                                    s=sl[1]
                            s=s.strip()
                            if kind=="entry/exit point" and s.startswith("HOLDING"):
                                continue #reached HOLDING-part of VAC
                                
                            #Check for other headings
                            print "Holding item",item,"s:<%s>"%(s,)
                            m=re.match(r"([A-Z]{2,}).*?(\d+N)\s*(\d+E).*",s)
                            if not m:                                
                                m=re.match(r".*?(\d+N)\s*(\d+E).*",s) 
                                if not m:
                                    continue
                                assert m
                                lat,lon=m.groups()
                                #skavsta
                                if icao=="ESKN":
                                    if s.startswith(u"Hold north of T"):
                                        name="NORTH"
                                    elif s.startswith(u"Hold south of B"):
                                        name="SOUTH"                     
                                    else:
                                        assert 0
                                #add more specials here            
                                else:
                                    continue
                            else:
                                name,lat,lon=m.groups()
                            print name,lat,lon
                            try:
                                coord=parse_coords(lat,lon)
                            except:
                                print "Couldn't parse:",lat,lon
                                continue
                            
                            if name.count("REMARK") or len(name)<=2:
                                print "Suspicious name: ",name
                                #sys.exit(1)
                                continue
                            points[icao+' '+name]=dict(name=icao+' '+name,icao=icao,pos=coord,kind=kind)


    for point in points.items():
        print point


    #sys.exit(1)


    for ad in ads:
        icao=ad['icao']
        if icao in big_ad:
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
            freqs=[]
            found=False
            for pagenr in xrange(0,p.get_num_pages()):
                page=p.parse_page_to_items(pagenr)
                
                matches=page.get_by_regex(r".*ATS\s+COMMUNICATION\s+FACILITIES.*")
                print "Matches of ATS COMMUNICATION FACILITIES on page %d: %s"%(pagenr,matches)
                if len(matches)>0:
                    commitem=matches[0]
                    #commitem,=page.get_by_regex("ATS\s+COMMUNICATION\s+FACILITIES")
                    curname=None
                    for idx,item in enumerate(page.get_lines(page.get_partially_in_rect(0,commitem.y1,100,100))):
                        if item.strip()=="":
                            curname=None
                        if re.match(".*RADIO\s+NAVIGATION\s+AND\s+LANDING\s+AIDS.*",item):
                            break
                        m=re.match(r"(.*?)\s*(\d{3}\.\d{1,3})\s+MHz.*",item)
                        if not m: continue
                        who,sfreq=m.groups()
                        freq=float(sfreq)
                        if abs(freq-121.5)<1e-4:
                            if who.strip():
                                curname=who
                            continue #Ignore emergency frequency, it is understood
                        if not who.strip():
                            if curname==None: continue
                            freqs.append((curname,freq))
                        else:
                            curname=who
                            freqs.append((who,freq))
                                
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
                    print "Altlines:",altlines
                    anonymous_alt=False
                    for item in altlines:
                        if item.strip()=="": continue
                        print "Matchin alt <%s>"%(item,)
                        m=re.match(r"(.*?)(?:(\d{3,5})\s*ft\s*.*(?:(GND)|(MSL))|\s*(GND)\s*)",item)
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
                    
                    print "\nSubspacelines:\n===========================\n%s"%(subspacelines,)
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
                            points=parse_coord_str(" ".join(subspacelines[spacename])),
                            freqs=freqs
                            )
                        
                        if True:
                            vs=[]
                            for p in space['points']:
                                x,y=mapper.latlon2merc(mapper.from_str(p),13)
                                vs.append(Vertex(int(x),int(y)))                    
                            p=Polygon(vvector(vs))
                            if p.calc_area()<=30*30:
                                print space
                                print "Area:",p.calc_area()
                            assert p.calc_area()>30*30
                            print "Area: %f"%(p.calc_area(),)
                        
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

    #sys.exit(1)
            
    for extra in extra_airfields.extra_airfields:
        ads.append(extra)
    print
    print
    for k,v in sorted(points.items()):
        print k,v
        
    print "Num points:",len(points)
    
    origads=list(ads)
    for flygkartan_id,name,lat,lon,dummy in csv.reader(open("fplan/extract/flygkartan.csv"),delimiter=";"):
        found=None
        lat=float(lat)
        lon=float(lon)
        if type(name)==str:
            name=unicode(name,'utf8')
        mercf=mapper.latlon2merc((lat,lon),13)
        for a in origads:
            merca=mapper.latlon2merc(mapper.from_str(a['pos']),13)
            dist=math.sqrt((merca[0]-mercf[0])**2+(merca[1]-mercf[1])**2)
            if dist<120:
                found=a
                break
        if found:
            found['flygkartan_id']=flygkartan_id
        else:
            ads.append(
                dict(
                    icao='ZZZZ',
                    name=name,
                    pos=mapper.to_str((lat,lon)),
                    elev=int(get_terrain_elev((lat,lon))),
                    flygkartan_id=flygkartan_id
                ))
                
    for ad in ads:     
        if ad['name'].count(u"Långtora"):            
            ad['pos']=mapper.to_str(mapper.from_aviation_format("5944.83N01708.20E"))
            
    print ads
    for ad in ads:
        print "%s: %s - %s (%s ft) (%s)"%(ad['icao'],ad['name'],ad['pos'],ad['elev'],ad.get('flygkartan_id','inte i flygkartan'))
        if 'spaces' in ad:
            print "   spaces: %s"%(ad['spaces'],)
    return ads,points.values()

                
                
    # getxml("/AIP/AD/AD 2/ESSA/ES_AD_2_ESSA_en.pdf")
    
    
            
if __name__=='__main__':
    extract_airfields()
    
    
