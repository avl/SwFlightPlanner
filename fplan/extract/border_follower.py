from pyshapemerge2d import Vertex,Line,Polygon,vvector
import fplan.lib.mapper as mapper
import os
import pickle
from itertools import izip,chain
import math

borders=None
def clear_cache():
    global borders
    borders=None
def get_borders(pcountry):
    print "Getting for",pcountry
    global borders
    if not borders:
        if not os.path.exists("fplan/extract/lands.bin"):
            if os.system("bunzip2 fplan/extract/lands.bin.bz2")!=0:
                raise Exception("Couldn't unbzip2 lands.bin.bz2")
        f=open("fplan/extract/lands.bin")
        tborders=pickle.load(f)
        f.close()
        out=dict()
        for country,parts in tborders.items():
            outparts=[]
            tot=0
            for part in parts:
                outpart=[]
                poly_coords=[]
                last=None
                for coord in part:
                    merc=mapper.latlon2merc(mapper.from_str(coord),13)
                    if merc==last: continue
                    last=merc
                    outpart.append(merc)
                    tot+=1
                    poly_coords.append(Vertex(int(merc[0]),int(merc[1])))
                assert len(outpart)>=3
                if outpart[0]==outpart[-1]:
                    outpart=outpart[:-1]
                    poly_coords=poly_coords[:-1]
                poly=Polygon(vvector(poly_coords))
                assert poly.is_ccw()

                outparts.append(outpart)
            print "Parts in ",country,len(outparts),tot
            out[country]=outparts
        borders=out
    #if pcountry!="sweden":
    #    raise Exception("Debug, just allow sweden for now. just remove this after.")
    return borders[pcountry]

def find_closest(parts,point):
    pointv=Vertex(int(point[0]),int(point[1]))
    def gen_cands():
        for partnum,part in enumerate(parts):
            for idx,(a,b) in enumerate(izip(part,chain(part[1:],part[0:1]))):
                av=Vertex(int(a[0]),int(a[1]))
                bv=Vertex(int(b[0]),int(b[1]))
                l=Line(av,bv)
                clo=l.approx_closest(pointv)
                actualdist=(clo-pointv).approxlength()
                yield partnum,actualdist,(clo.get_x(),clo.get_y()),idx
    partnum,dist,closest,idx=min(gen_cands(),key=lambda x:x[1])
    return partnum,idx,closest

def circle(part,startpos,idx1,idx2,endpos,dir):
    if len(part)<3: raise Exception("Too few vertices in part")
    l=len(part)
    if dir>0:
        idx1=(idx1+1)%l
    if dir<0:
        idx2=(idx2+1)%l       
    cur=idx1  
    out=[startpos]
    if  idx1==idx2:
        dist=math.sqrt(sum((xa-xb)**2 for xa,xb in izip(startpos,endpos)))
        return [startpos,endpos],dist
    assert idx1<l
    assert idx2<l
    assert dir in [-1,1]
    while True:
        #print cur
        out.append(part[cur])
        if cur==idx2:
            out.append(endpos)
            break
        cur+=dir
        cur%=l
    totdist=0
    for a,b in izip(out,out[1:]):
        totdist+=math.sqrt(sum((xa-xb)**2 for xa,xb in izip(a,b)))
        
    return out,totdist
    
def follow_along(country,start,end):
    out=[]
    for merc in follow_along13(country,
            mapper.latlon2merc(start,13),
            mapper.latlon2merc(end,13)):
        out.append( mapper.merc2latlon(merc,13) )
    return out

def follow_along13(country,start,end):
    borders=get_borders(country)
    print "start,end",start,end
    part1,idx1,pos1=find_closest(borders,start)
    part2,idx2,pos2=find_closest(borders,end)
    print "Found",pos1,pos2
    if part1!=part2: raise Exception("Start and endpoint are not on same island!")
    part=part1
    print "from,to",idx1,idx2
    if idx1==idx2:
        return [start,end]
    res1,dist1=circle(borders[part],pos1,idx1,idx2,pos2,-1)
    res2,dist2=circle(borders[part],pos1,idx1,idx2,pos2,1)
    if dist1<dist2:
        ret=res1
    else:
        ret=res2        
    return [start]+ret+[end]

if __name__=='__main__':
    fa=follow_along("sweden",(59.0,11.4),(61.0,12.5))
    print " - ".join(mapper.to_str(pos) for pos in fa)
        
    