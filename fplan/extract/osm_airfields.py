#encoding=utf8
import csv
import os
import lxml.html
from fplan.extract.html_helper import alltext,alltexts
import fplan.lib.mapper as mapper
import fplan.lib.get_terrain_elev as gte
import re
import unicodedata
import pickle

def parse_info():
    out=[]
    for fname in os.listdir("fplan/extract/ads"):
        print "Processing",fname
        p=os.path.join("fplan/extract/ads",fname)
        
        data=open(p).read()
        parser=lxml.html.HTMLParser()
        parser.feed(data)
        tree=parser.close()
        ai=None
        for table in tree.xpath(".//table"):
            #print "New table in",fname
            anyap=False
            for idx,tr in enumerate(table.xpath("tr")):
                tds=[alltext(td).strip() for td in tr.xpath("td|th")]
                if idx==0:
                    for i,td in enumerate(tds):
                        if td.lower().count("airport") or td.lower().count("name"):
                            #print "Td",td,"contains airport",i
                            ai=i
                            break
                    #print "head tds:",tds
                    #assert(ai!=None)
                    #print "ai=",ai
                    continue
                icao=None
                #print "Reg row",repr(tds)
                for i,td in enumerate(tds):
                    m=re.match(r".*\b([A-Z]{4})\b.*",td)                    
                    if m:
                        #print "Match:",tds
                        possicao,=m.groups()
                        if possicao=='ICAO' or possicao=='IATA': 
                            continue
                        possname=tds[ai]
                        if len(possname)<=3:
                            continue
                        name=possname
                        icao=possicao
                        break
                if icao:
                    if type(name)!=unicode:
                        name=unicode(name,"utf8")
                    
                    out.append((name,icao))
                    anyap=True
                    
            if anyap:
                ap=False
                for name,icao in out:
                    if name.lower().count("airport"):
                        ap=True
                if ap==False:
                    print "-------------------------------------"
                    for name,icao in out:
                        print name,icao
                    print "^None of the airport names contained the word airport:",fname
                    raise Exception("Not any airport name")
                
        
    out.append((u"Isle of Man Airport",u"EGNS"))
    out.append((u"Guernsey Airport",u"EGJB"))
    out.append((u"Jersey",u"EGJJ"))
    return out
def alnum(x):
    if x[0] in ['-','/','.','_']:
        return " "
    cat=unicodedata.category(x)
    if cat[0] in ['L','N']:
        return x.upper()
    if cat[0]=='Z':
        return " "
    return ""

def normalize(name):
    assert type(name)==unicode
    name=name.lower()
    name=name.replace(u"milano",u"milan")
    name=name.replace(u"aerodrome",u"")
    
    name=name.replace(u"campo de vuelo",u"")
    name=name.replace(u"campo di volo",u"")
    name=name.replace(u"fliegerhorst",u"")
    
    name=name.replace(u"aeropuerto",u"")
    name=name.replace(u"aeroporto",u"")
    name=name.replace(u"altisurface",u"")
    name=name.replace(u"aviosuperficie",u"")
    name=name.replace(u"letisko",u"")
    name=name.replace(u"lotnisko",u"")
    name=name.replace(u"segelfluggelände",u"")
    name=name.replace(u"sonderlandeplatz",u"")
    
    name=name.replace(u"airport",u"")
    name=name.replace(u"airfield",u"")
    name=name.replace(u"flygplats",u"")
    name=name.replace(u"lufthamn",u"")
    name=name.replace(u"verkehrslandeplatz",u"")
    name=re.sub(ur"\bde\b",u"",name)
    name=re.sub(ur"\bdi\b",u"",name)
    name=re.sub(ur"\bair\b",u"",name)
    name=re.sub(ur"\bbase\b",u"",name)
    name=name.replace(u"segelflugplatz",u"")
    name=name.replace(u"sportflugplatz",u"")
    name=name.replace(u"flugplatz",u"")
    name=name.replace(u"flughafen",u"")
    name=name.replace(u"aeroport",u"")
    name=name.replace(u"aéroport",u"")
    name=name.replace(u"aerodrome",u"")
    name=name.replace(u"aérodrome",u"")
    name=name.replace(u"lufthavn",u"")    
    name=(u''.join((alnum(c) for c in unicodedata.normalize('NFKD', name))))
    name=name.lower()
    namesub=set(name.split())        
    return namesub
def osm_airfields_parse():
    nameicao=parse_info()
    f=open("adnames.txt","w")
    for name,icao in sorted(nameicao,key=lambda x:x[0]):        
        f.write("%s: %s\n"%(icao.encode('utf8'),name.encode('utf8')))
    f.close()
    ads=[]
    hits=0
    misses=[]
    
    name2icao=[]
    for name,icao in nameicao:
        name2icao.append((normalize(name),name,icao))
    
    dupecheck=set()    
    
    for lon,lat,name in csv.reader(open("fplan/extract/aerodromes.txt")):
        name=unicode(name,"utf8")
        if not name.strip(): continue
        
        icao=None
        n1=normalize(name)
        if frozenset(n1) in dupecheck:
            continue
        dupecheck.add(frozenset(n1))
        lastquality=0
        lastname=None
        for n2,iname,iicao in name2icao:
            #print repr(n1),"==",repr(n2)
            minlen=min(len(n1),len(n2))
            if minlen>2:
                minlen=minlen-1
            quality=len(n1.intersection(n2))
            if quality>=minlen and quality>lastquality:
                if icao!=None and icao!=iicao:
                    print "For name:",name,"Previous match:,",icao,"New match:",iicao,"Name:",iname,"last name:",lastname,"quality:",quality,"last:",lastquality,"minlen:",minlen
                    #assert icao==None
                icao=iicao
                lastquality=quality
                lastname=iname
        #print "Ap with name:",name
        if icao:
            hits+=1
            icao=icao
        else:
            icao='ZZZZ'
            misses.append(name)
            #print "Missed:",name
        d=dict(
                icao=icao,
                name=name,
                pos=mapper.to_str((float(lat),float(lon))),
                elev=int(gte.get_terrain_elev((float(lat),float(lon))))
                )
            
        if hits%10==0:
            print "Hits: %d, Misses: %d, Perc: %.1f"%(hits,len(misses),100.0*(float(hits)/(float(hits)+len(misses))))
        ads.append(d)
    print "Misses:"
    f=open("missedads.txt","w")        
    for miss in sorted(misses):
        f.write((miss+" - "+repr(normalize(miss))+u"\n").encode('utf8'))
    f.close()    
    f=open("foundads.txt","w")        
    for norm,name,icao in name2icao:
        f.write((name+" - "+repr(norm)+u"\n").encode('utf8'))
    f.close()    
    print "Hits: ",hits
    print "Misses: ",len(misses)
    
    return ads
                
if __name__=='__main__':
    #onetime_osm_airfields_parse()
    osm_airfields_parse()
