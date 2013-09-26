#encoding=utf8
from fetchdata import getxml
from parse import Parser,Item
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
from itertools import izip
import fplan.extract.rwy_constructor as rwy_constructor
import md5    
import codecs
import parse_landing_chart
import aip_text_documents
def extract_airfields(filtericao=lambda x:True,purge=True):
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
    #nochartf=open("nochart.txt","w")
    for pagenr in xrange(startpage,p.get_num_pages()):
        row_y=[]
        page=p.parse_page_to_items(pagenr)
        allines=[x for x in (page.get_lines(page.get_partially_in_rect(0,0,15,100))) if x.strip()]
        for item,next in zip(allines,allines[1:]+[""]):
            #print "item:",item
            
            m=re.match(ur"^\s*[A-ZÅÄÖ]{3,}(?:/.*)?\b.*",item)
            if m:
                #print "Candidate, next is:",next
                if re.match(r"^\s*[A-Z]{4}\b.*",next):
                    #print "Matched:",item
                    #print "y1:",item.y1                    
                    row_y.append(item.y1)
        for y1,y2 in zip(row_y,row_y[1:]+[100.0]):
            #print "Extacting from y-range: %f-%f"%(y1,y2)
            items=list(page.get_partially_in_rect(0,y1-0.25,5.0,y2+0.25,ysort=True))
            if len(items)>=2:
                #print "Extract items",items
                ad=dict(name=unicode(items[0].text).strip(),
                        icao=unicode(items[1].text).strip()                    
                        )
                #print "Icao:",ad['icao']
                assert re.match(r"[A-Z]{4}",ad['icao'])
                if not filtericao(ad): continue
                if len(items)>=3:
                    #print "Coord?:",items[2].text
                    m=re.match(r".*(\d{6}N)\s*(\d{7}E).*",items[2].text)
                    if m:
                        lat,lon=m.groups()
                        ad['pos']=parse_coords(lat,lon)           
                        #print "Items3:",items[3:]   
                        elev=re.findall(r"(\d{1,5})\s*ft"," ".join(t.text for t in items[3:]))
                        #print "Elev:",elev
                        assert len(elev)==1
                        ad['elev']=int(elev[0])                        
                                     
                ads.append(ad)

        
    big_ad=set()        
    for ad in ads:
        if not ad.has_key('pos'):
            big_ad.add(ad['icao'])
            
    for ad in ads:        
        icao=ad['icao']
        if icao in big_ad:            
            if icao in ['ESIB','ESNY','ESCM','ESPE']:
                continue                    
            
            try:
                p=Parser("/AIP/AD/AD 2/%s/ES_AD_2_%s_6_1_en.pdf"%(icao,icao))
            except:
                p=Parser("/AIP/AD/AD 2/%s/ES_AD_2_%s_6-1_en.pdf"%(icao,icao))

            ad['aipvacurl']=p.get_url()
            for pagenr in xrange(p.get_num_pages()):
                page=p.parse_page_to_items(pagenr)
                
                """
                for altline in exitlines:
                    m=re.match(r"(\w+)\s+(\d+N)\s*(\d+E.*)",altline)
                    if not m: continue
                    name,lat,lon=m.groups()
                    try:
                        coord=parse_coords(lat,lon)
                    except Exception:
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
                            print "Holding item",item
                            y1=item.y1
                            if idx==len(items)-1:
                                y2=100
                            else:
                                y2=items[idx+1].y1
                            items2=[x for x in page.get_partially_in_rect(item.x1+1,y1+0.3,item.x1+40,y2-0.1) if x.x1>=item.x1-0.25 and x.y1>=y1-0.05 and x.y1<y2-0.05]
                            s=(" ".join(page.get_lines(items2))).strip()
                            print "Holding lines:",repr(page.get_lines(items2))
                            #if s.startswith("ft Left/3"): #Special case for ESOK
                            #    s,=re.match("ft Left/3.*?([A-Z]{4,}.*)",s).groups()
                            #m=re.match("ft Left/\d+.*?([A-Z]{4,}.*)",s)
                            #if m:
                            #    s,=m.groups()
                                
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
                            #Fixup strange formatting of points in some holding items: (whitespace between coord and 'E')                            
                            s=re.sub(ur"(\d+)\s*(N)\s*(\d+)\s*(E)",lambda x:"".join(x.groups()),s)

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
                            try:
                                coord=parse_coords(lat,lon)
                            except Exception:
                                print "Couldn't parse:",lat,lon
                                continue
                            #print name,lat,lon,mapper.format_lfv(*mapper.from_str(coord))
                            
                            if name.count("REMARK") or len(name)<=2:
                                print "Suspicious name: ",name
                                #sys.exit(1)
                                continue
                            points[icao+' '+name]=dict(name=icao+' '+name,icao=icao,pos=coord,kind=kind)


    #for point in points.items():
    #    print point


    #sys.exit(1)


    for ad in ads:
        icao=ad['icao']
        if icao in big_ad:
            #print "Parsing ",icao
            p=Parser("/AIP/AD/AD 2/%s/ES_AD_2_%s_en.pdf"%(icao,icao))
            ad['aiptexturl']=p.get_url()
            firstpage=p.parse_page_to_items(0)
            te="\n".join(firstpage.get_all_lines())                        
            #print te
            coords=re.findall(r"ARP.*(\d{6}N)\s*(\d{7}E)",te)
            if len(coords)>1:
                raise Exception("First page of airport info (%s) does not contain exactly ONE set of coordinates"%(icao,))
            if len(coords)==0:
                print "Couldn't find coords for ",icao
            #print "Coords:",coords
            ad['pos']=parse_coords(*coords[0])

            elev=re.findall(r"Elevation.*?(\d{1,5})\s*ft",te,re.DOTALL)
            if len(elev)>1:
                raise Exception("First page of airport info (%s) does not contain exactly ONE elevation in ft"%(icao,))
            if len(elev)==0:
                print "Couldn't find elev for ",icao                
            ad['elev']=int(elev[0])
            freqs=[]
            found=False
            thrs=[]
            #uprint("-------------------------------------")
            for pagenr in xrange(p.get_num_pages()):
                page=p.parse_page_to_items(pagenr)
                #uprint("Looking on page %d"%(pagenr,))
                if 0: #opening hours are no longer stored in a separate document for any airports. No need to detect which any more (since none are).
                    for item in page.get_by_regex(".*OPERATIONAL HOURS.*"):
                        lines=page.get_lines(page.get_partially_in_rect(0,item.y2+0.1,100,100))
                        for line in lines:
                            things=["ATS","Fuelling","Operating"]
                            if not line.count("AIP SUP"): continue
                            for thing in things:
                                if line.count(thing):
                                    ad['aipsup']=True
                        
                    
                for item in page.get_by_regex(".*\s*RUNWAY\s*PHYSICAL\s*CHARACTERISTICS\s*.*"):
                    #uprint("Physical char on page")
                    lines=page.get_lines(page.get_partially_in_rect(0,item.y2+0.1,100,100))
                    seen_end_rwy_text=False
                    for line,nextline in izip(lines,lines[1:]+[None]):
                        #uprint("MAtching: <%s>"%(line,))
                        if re.match(ur"AD\s+2.13",line): break
                        if line.count("Slope of"): break
                        if line.lower().count("end rwy:"): seen_end_rwy_text=True
                        if line.lower().count("bgn rwy:"): seen_end_rwy_text=True
                        m=re.match(ur".*(\d{6}\.\d+)[\s\(\)\*]*(N).*",line)
                        if not m:continue
                        m2=re.match(ur".*(\d{6,7}\.\d+)\s*[\s\(\)\*]*(E).*",nextline)                            
                        if not m2:continue
                        latd,n=m.groups()
                        lond,e=m2.groups()
                        assert n=="N"
                        assert e=="E"
                        lat=latd+n
                        lon=lond+e
                        rwytxts=page.get_lines(page.get_partially_in_rect(0,line.y1+0.05,12,nextline.y2-0.05))
                        uprint("Rwytxts:",rwytxts)
                        rwy=None
                        for rwytxt in rwytxts:
                            #uprint("lat,lon:%s,%s"%(lat,lon))
                            #uprint("rwytext:",rwytxt)
                            m=re.match(ur"\s*(\d{2}[LRCM]?)\b.*",rwytxt)
                            if m:
                                assert rwy==None
                                rwy=m.groups()[0]
                        if rwy==None and seen_end_rwy_text:
                            continue
                        print "Cur airport:",icao
                        already=False
                        assert rwy!=None
                        seen_end_rwy_text=False
                        for thr in thrs:
                            if thr['thr']==rwy:
                                raise Exception("Same runway twice on airfield:"+icao)
                        thrs.append(dict(pos=mapper.parse_coords(lat,lon),thr=rwy))
            assert len(thrs)>=2
            for pagenr in xrange(0,p.get_num_pages()):
                page=p.parse_page_to_items(pagenr)                                              
                
                matches=page.get_by_regex(r".*ATS\s+COMMUNICATION\s+FACILITIES.*")
                #print "Matches of ATS COMMUNICATION FACILITIES on page %d: %s"%(pagenr,matches)
                if len(matches)>0:
                    commitem=matches[0]
                    curname=None
                    
                    callsign=page.get_by_regex_in_rect(ur"Call\s*sign",0,commitem.y1,100,commitem.y2+8)[0]
                    
                    
                    for idx,item in enumerate(page.get_lines(page.get_partially_in_rect(callsign.x1-0.5,commitem.y1,100,100),fudge=0.3,order_fudge=15)):
                        if item.strip()=="":
                            curname=None
                        if re.match(".*RADIO\s+NAVIGATION\s+AND\s+LANDING\s+AIDS.*",item):
                            break
                        #print "Matching:",item
                        m=re.match(r"(.*?)\s*(\d{3}\.\d{1,3})\s*MHz.*",item)
                        #print "MHZ-match:",m
                        if not m: continue
                        #print "MHZ-match:",m.groups()
                        who,sfreq=m.groups()
                        freq=float(sfreq)
                        if abs(freq-121.5)<1e-4:
                            if who.strip():
                                curname=who
                            continue #Ignore emergency frequency, it is understood
                        if not who.strip():
                            if curname==None: continue
                        else:
                            curname=who
                        freqs.append((curname.strip().rstrip("/"),freq))


            for pagenr in xrange(0,p.get_num_pages()):
                page=p.parse_page_to_items(pagenr)                                              
                                
                matches=page.get_by_regex(r".*ATS\s*AIRSPACE.*")
                #print "Matches of ATS_AIRSPACE on page %d: %s"%(pagenr,matches)
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

                    #print "Spaces:",subspacelines
                    #print "ICAO",ad['icao']
                    #altlines=page.get_lines(page.get_partially_in_rect(vertitem.x2+1,vertitem.y1,100,airspaceclass.y1-0.2))
                    
                    #print "Altlines:",altlines
                    subspacealts=dict()
                    subspacekeys=subspacelines.keys()
                        
                    allaltlines=" ".join(page.get_lines(page.get_partially_in_rect(vertitem.x1+0.5,vertitem.y1+0.5,100,airspaceclass.y1-0.2)))
                    single_vertlim=False
                    totalts=list(mapper.parse_all_alts(allaltlines))
                    #print "totalts:",totalts 
                    if len(totalts)==2:
                        single_vertlim=True
                    
                    for subspacename in subspacekeys:
                        ceil=None
                        floor=None
                        subnames=[subspacename]
                        if subspacename.split(" ")[-1].strip() in ["TIA","TIZ","CTR","CTR/TIZ"]:
                            subnames.append(subspacename.split(" ")[-1].strip())
                        #print "Parsing alts for ",subspacename,subnames
                        try:                        
                            for nametry in subnames:
                                if single_vertlim: #there's only one subspace, parse all of vertical limits field for this single one.
                                    items=[vertitem]
                                else:
                                    items=page.get_by_regex_in_rect(nametry,vertitem.x2+1,vertitem.y1,100,airspaceclass.y1-0.2)
                                for item in items: 
                                    alts=[]
                                    for line in page.get_lines(page.get_partially_in_rect(item.x1+0.5,item.y1+0.5,100,airspaceclass.y1-0.2)):
                                        #print "Parsing:",line
                                        line=line.replace(nametry,"").lower().strip()
                                        parsed=list(mapper.parse_all_alts(line))
                                        if len(parsed):
                                            alts.append(mapper.altformat(*parsed[0]))
                                        if len(alts)==2: break
                                    if alts:
                                        #print "alts:",alts
                                        ceil,floor=alts
                                        raise StopIteration
                        except StopIteration:
                            pass
                        assert ceil and floor
                        subspacealts[subspacename]=dict(ceil=ceil,floor=floor)             
                        
                    spaces=[]                                        
                    for spacename in subspacelines.keys():
                        altspacename=spacename
                        #print "Altspacename: %s, subspacesalts: %s"%(altspacename,subspacealts)
                        space=dict(
                            name=spacename,
                            ceil=subspacealts[altspacename]['ceil'],
                            floor=subspacealts[altspacename]['floor'],
                            points=parse_coord_str(" ".join(subspacelines[spacename])),
                            freqs=list(set(freqs))
                            )
                        
                        if True:
                            vs=[]
                            for p in space['points']:
                                x,y=mapper.latlon2merc(mapper.from_str(p),13)
                                vs.append(Vertex(int(x),int(y)))                    
                            p=Polygon(vvector(vs))
                            if p.calc_area()<=30*30:
                                pass#print space
                                pass#print "Area:",p.calc_area()
                            assert p.calc_area()>30*30
                            #print "Area: %f"%(p.calc_area(),)
                        
                        spaces.append(space)
                        #print space
                    ad['spaces']=spaces
                    found=True
                if found:
                    break
            assert found                            
            ad['runways']=rwy_constructor.get_rwys(thrs)
                            
                            
            #Now find any ATS-airspace
    chartblobnames=[]
    for ad in ads:        
        icao=ad['icao']
        if icao in big_ad:          
            parse_landing_chart.help_plc(ad,"/AIP/AD/AD 2/%s/ES_AD_2_%s_2_1_en.pdf"%(icao,icao),
                            icao,ad['pos'],"se",variant="")
            parse_landing_chart.help_plc(ad,"/AIP/AD/AD 2/%s/ES_AD_2_%s_6_1_en.pdf"%(icao,icao),
                            icao,ad['pos'],"se",variant="vac")
            if icao!='ESSA':
                parse_landing_chart.help_plc(ad,"/AIP/AD/AD 2/%s/ES_AD_2_%s_2_3_en.pdf"%(icao,icao),
                                icao,ad['pos'],"se",variant="parking")
            else:
                parse_landing_chart.help_plc(ad,"/AIP/AD/AD 2/%s/ES_AD_2_%s_2_7_en.pdf"%(icao,icao),                                             
                                icao,ad['pos'],"se",variant="parking")
            
            
            #aip_text_documents.help_parse_doc(ad,"/AIP/AD/AD 2/%s/ES_AD_2_%s_6_1_en.pdf"%(icao,icao),
            #            icao,"se",title="General Information",category="general")
                                    
            
            aip_text_documents.help_parse_doc(ad,"/AIP/AD/AD 2/%s/ES_AD_2_%s_en.pdf"%(icao,icao),
                        icao,"se",title="General Information",category="general")
            
                  

    
    #if purge:
    #    parse_landing_chart.purge_old(chartblobnames,country="se")        
    
    #sys.exit(1)

    for extra in extra_airfields.extra_airfields:
        if filtericao(extra):
            ads.append(extra)
    print
    print
    for k,v in sorted(points.items()):
        print k,v,mapper.format_lfv(*mapper.from_str(v['pos']))
        
    #print "Num points:",len(points)
    
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
            d=dict(
                    icao='ZZZZ',
                    name=name,
                    pos=mapper.to_str((lat,lon)),
                    elev=int(get_terrain_elev((lat,lon))),
                    flygkartan_id=flygkartan_id)
            if filtericao(d):
                ads.append(d)
                    
    minor_ad_charts=extra_airfields.minor_ad_charts
        
                    
    for ad in ads:     
        if ad['name'].count(u"Långtora"):            
            ad['pos']=mapper.to_str(mapper.from_aviation_format("5944.83N01708.20E"))
            
        if ad['name'] in minor_ad_charts:
            charturl=minor_ad_charts[ad['name']]
            arp=ad['pos']
            if 'icao' in ad and ad['icao'].upper()!='ZZZZ':
                icao=ad['icao'].upper()
            else:
                icao=ad['fake_icao']
                
            parse_landing_chart.help_plc(ad,charturl,icao,arp,country='raw',variant="landing")
            """
            assert icao!=None
            lc=parse_landing_chart.parse_landing_chart(
                    charturl,
                    icao=icao,
                    arppos=arp,country="raw")
            assert lc
            if lc:
                ad['adcharturl']=lc['url']
                ad['adchart']=lc
            """
            
    #print ads
    for ad in ads:
        print "%s: %s - %s (%s ft) (%s)"%(ad['icao'],ad['name'],ad['pos'],ad['elev'],ad.get('flygkartan_id','inte i flygkartan'))
        for space in ad.get('spaces',[]):
            for freq in space.get('freqs',[]):
                print "   ",freq
        #if 'spaces' in ad:
        #    print "   spaces: %s"%(ad['spaces'],)
        #if 'aiptext' in ad:
        #    print "Aip texts:",ad['aiptext']
        #else:
        #    print "No aiptext"
    print "Points:"
    for point in sorted(points.values(),key=lambda x:x['name']):
        print point
        
    f=codecs.open("extract_airfields.regress.txt","w",'utf8')    
    for ad in ads:
        r=repr(ad)
        d=md5.md5(r).hexdigest()
        f.write("%s - %s - %s\n"%(ad['icao'],ad['name'],d))
    f.close()
    f=codecs.open("extract_airfields.regress-details.txt","w",'utf8')    
    for ad in ads:
        r=repr(ad)
        f.write(u"%s - %s - %s\n"%(ad['icao'],ad['name'],r))
    f.close()
    
    return ads,points.values()

                
                
    # getxml("/AIP/AD/AD 2/ESSA/ES_AD_2_ESSA_en.pdf")
    
    
            
if __name__=='__main__':
    purge=False
    def filter_expr(ad):    
        if len(sys.argv)==2:
            av1=sys.argv[1]
            if len(av1)==4 and av1.isupper():
                return ad['icao']==av1
            else:
                return eval(sys.argv[1],dict(icao=ad['icao'],name=ad['name']))
        return True
    extract_airfields(filter_expr,purge)
    
    
