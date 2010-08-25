import fplan.lib.mapper as mapper
from pyshapemerge2d import Vector,Line2,Vertex
from fplan.lib.get_terrain_elev import get_terrain_elev


dirs=["N",
      "NNE",
      "NE",
      "ENE",
      "E",
      "ESE",
      "SE",
      "SSE",
      "S",
      "SSW",
      "SW",
      "WSW",
      "W",
      "WNW",
      "NW",
      "NNW"
      ]
def describe_dir(tt):
    tt=tt%360.0
    if tt<0: tt+=360.0
    r=int(tt*(16.0/360.0)+1.0/32.0)
    if r<0: r=0
    if r>15: r=15
    return dirs[r]

    

def get_terrain_near_route(rts,vertdist,interval=10):
    l=len(rts)
    out=[]
    for idx,rt in enumerate(rts):
        print "ord:",rt.a.ordinal
        merca=rt.subposa
        mercb=rt.subposb
        minstep=min(1.0,interval)
        df=rt.d
        if df<1e-3:
            df=1e-3
        along_nm=0.0
        #isfirstorlast=(idx==0 or idx==l-1)        
        while True:
            alongf=float(along_nm)/float(df)
            end=False
            if alongf>1.0:
                alongf=1.0
                end=True
            merc=((1.0-alongf)*merca[0]+(alongf)*mercb[0],
                  (1.0-alongf)*merca[1]+(alongf)*mercb[1])
            alt=(1.0-alongf)*rt.startalt+(alongf)*rt.endalt
            latlon=mapper.merc2latlon(merc,13)
            elev=get_terrain_elev(latlon)
            
            #if isfirstorlast and (along_nm<2.5 or along_nm>d-2.5):
            #    along_nm+=minstep
            #    continue
               
            if alt-elev<vertdist:
                #print "idx",idx,"ord:",rt.a.ordinal
                out.append(dict(
                    name="Terrain warning",
                    pos=mapper.to_str(latlon),
                    elev="%.0f"%(elev,),
                    elevf=elev,
                    dist=0,
                    bearing=0,
                    closestalt=alt,
                    kind='terrain',
                    dist_from_a=float(along_nm),
                    dir_from_a=describe_dir(rt.tt),
                    a=rt.a,
                    b=rt.b,
                    ordinal=rt.a.ordinal))
                along_nm+=interval
            else:
                along_nm+=minstep
            if end: 
                break
    return out

def get_stuff_near_route(rts,items,dist,vertdist):
    for item in items:
        #if not item['name'].count("NG/DOMKYR"): continue
        
        try:
            itemmerc=mapper.latlon2merc(mapper.from_str(item['pos']),13)
        except:
            print "Bad coord:",item['pos']
            continue
        itemv=Vertex(int(itemmerc[0]),int(itemmerc[1]))
        onenm=mapper.approx_scale(itemmerc,13,1.0)
        for rt in rts:
            #print "========================================="
            av=Vertex(int(rt.subposa[0]),int(rt.subposa[1]))
            bv=Vertex(int(rt.subposb[0]),int(rt.subposb[1]))
            l=Line2(av,bv)
            linelen=(bv-av).approxlength()
            actualclosest=l.approx_closest(itemv)
            #print item['name'],"A: ",av,"B: ",bv,"clo:",actualclosest
            actualdist=(actualclosest-itemv).approxlength()/onenm
            
            ls=(actualclosest-av).approxlength()
            #print "Length from start:",ls
            #print "Linelen:",linelen
            if linelen>1e-3:
                along=ls/linelen
            else:
                along=0
            #print "Along:",along
            #print "Startalt:",rt.startalt," endalt: ",rt.endalt
            alongnm=rt.d*along
            alongnm_a=rt.relstartd+alongnm
            #print "NM from ",rt.a.waypoint," is ",alongnm_a
            closealt=rt.startalt+(rt.endalt-rt.startalt)*along
            #print "Altitude at point: ",closealt, " before: ",rt.a.waypoint,rt.b.waypoint
            altmargin=0
            if 'elev' in item:
                itemalt=mapper.parse_elev(item['elev'])
                altmargin=closealt-itemalt
            else:
                itemalt=None
                altmargin=0
            if actualdist<dist and altmargin<vertdist:
                bear=mapper.approx_bearing_vec(actualclosest,itemv)            
                d=dict(item)
                d['name']=d['kind']+': ' +d['name']
                d['dist_from_a']=alongnm_a
                d['dir_from_a']=describe_dir(rt.tt)
                d['dist']=actualdist
                d['bearing']=bear
                d['elevf']=itemalt
                if itemalt!=None:
                    d['vertmargin']=altmargin
                d['closestalt']=closealt
                d['a']=rt.a
                d['b']=rt.b
                d['ordinal']=rt.a.ordinal
                yield d
      
            
        
