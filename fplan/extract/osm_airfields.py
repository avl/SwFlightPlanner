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
    name=name.replace(u"aerodrome",u"")
    name=name.replace(u"airport",u"")
    name=name.replace(u"flygplats",u"")
    name=(u''.join((alnum(c) for c in unicodedata.normalize('NFKD', name))))
    name=re.sub(ur"\s+",u"",name)
    name=name.lower()
    assert type(name)==unicode
    return name
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
        
    for lon,lat,name in csv.reader(open("fplan/extract/aerodromes.txt")):
        name=unicode(name,"utf8")
        if not name.strip(): continue
        
        icao=None
        n1=normalize(name)
        for n2,iname,iicao in name2icao:
            #print repr(n1),"==",repr(n2)
            if n1.count(n2) or n2.count(n1):
                icao=iicao
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
            print "Hits: %d, Misses: %d, Perc: %.1f"%(hits,len(misses),float(hits)/(float(hits)+len(misses)))
        ads.append(d)
    print "Misses:"
    for miss in sorted(misses):
        print miss
    print "Hits: ",hits
    print "Misses: ",len(misses)
    
    #f=csv.writer(open("fplan/extract/ads/ads_processed.csv","w"))
    #for ad in ads:
    #    f.writerow((ad['name'].encode('utf8'),ad['icao'],ad['pos'],ad['elev']))
    
    return ads
                
if __name__=='__main__':
    #onetime_osm_airfields_parse()
    osm_airfields_parse()
