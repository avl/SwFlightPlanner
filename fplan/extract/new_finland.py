import os
import re
import zipfile
import fplan.lib.mapper as mapper

def getzip():
    raw,nowdate,cachename=fetchdata.getdata('https://www.dropbox.com/sh/m8e1n2d5r6pr7r0/AABfsC8ROhEM5a8KsNI_XLlxa/TXT?dl=1','raw',return_path=True)
    return cachename
    
    
def splitareas(rows):
    idx=0
    collected=[]
    for row in rows:
        if row.strip()=="":
            if len(collected):
                yield collected
                collected=[]
        else:
            collected.append(row)
    if len(collected):
        yield collected

def parse_alt(txt):
    txt=txt.strip()
    if txt in ["GND","UNL","SFC"]:
        return txt
    if re.match(r"\d+ FT MSL",txt):
        return txt
    if re.match(r"\d+ M SFC",txt):
        return txt
    if re.match(r"FL \d+",txt):
        return txt
    raise Exception("Unallowed alt: %s"%(txt,))
def is_alt(txt):
    try:
        parse_alt(txt)
        return True
    except:
        return False
def parse_alts(txt):
    comps=txt.split()
    assert len(comps)>1
    #print "Comps:",comps
    for idx in xrange(1,len(comps)):
        try:
            ceil=parse_alt(" ".join(comps[0:idx]))
            floor=parse_alt(" ".join(comps[idx:]))
            return floor,ceil
        except Exception,cause:
            #print cause
            pass
    return "UNK","UNK"
    #raise Exception("Couldn't parse alt: %s"%(txt,))
    
def fix_circle(coord):
    #print "CirclE:",repr(coord)
    pos,radius=coord.split("-")
    pos=pos.strip()
    radius=radius.strip()
    rad,=re.match(r"RADIUS\s*(\d+.?\d*)\s*NM",radius).groups()
    return "CIRCLE RADIUS %s NM CENTERED ON %s"%(rad,pos)
    
def parse_areas(areas,atype):
    areas=splitareas(areas.split("\n"))
    points=[]

    for area in areas:
        name=area[0].strip()
        assert len(name)
        if len(area)>2 and is_alt(area[-2]):
            ceiling=parse_alt(area[-2])
            floor=parse_alt(area[-1])
            areapart=area[1:-2]
        else:
            try:
                floor,ceiling=parse_alts(area[-1])
                areapart=area[1:-1]
            except:
                floor,ceiling="UNK","UNK"
                areapart=area[1:]
        
        coords="-".join([r.replace(" ","").strip() for r in areapart if not r.startswith("*")])
        if coords.count("RADIUS"):
            coords=fix_circle(coords)
        #print "name:",name,"coords:",coords
        yield dict(name=name,type=atype,floor=floor,freqs=[],ceiling=ceiling,points=mapper.parse_coord_str(coords))

import fetchdata
            
def load_finland():   

    zipname=getzip()
    zf=zipfile.ZipFile(zipname)
    areas=[]
    points=[]
    for fname in zf.namelist():
        #print "File:",fname
        txt=zf.open(fname).read()
        if fname=="WaypointImport.txt":
            for row in txt.split("\n"):
                if row.strip()=="" or row.startswith("*"):
                    continue
                #print repr(row)
                lat,lon,name=re.match(r"(\d+N) (\d+E)\s*(\w+)",row).groups()
                points.append( dict(name=name,kind="sig. point",pos=mapper.parse_coords(lat,lon)) )
                
        else:   
            t="TMA"
            if fname.count("D_Areas") or fname.count("TRA") or fname.count("R_Areas"):
                t="R"
            if fname.count("CTR"):
                t="CTR" 

            if fname.lower().count('finland_fir'):
                t="FIR"
            areas.extend(list(parse_areas(txt,t)))
     
    for area in points:
        print "Point: %s: %s"%(
            area['name'],area['pos'])
    for area in areas:
        print "Area: %s - %s-%s: %s"%(
            area['name'],area['floor'],area['ceiling'],area['points'])
    return areas,points
        
        
if __name__=='__main__':
    load_finland()
            
