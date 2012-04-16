import fplan.lib.mapper as mapper
from pyshapemerge2d import Vector,Line,Vertex
from fplan.lib.get_terrain_elev import get_terrain_elev_in_box_approx
from datetime import timedelta,datetime
from sunrise import sun_position_in_sky

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
    r=int(tt*(16.0/360.0)+1.0/2.0)
    if r<0: r=0
    if r>15: r=0
    return dirs[r]
def seconds(td):
    return td.days*86400.0+td.seconds+td.microseconds/1e6
def divide(ta,tb):
    return seconds(ta)/seconds(tb)
def get_low_sun_near_route(rts):
    l=len(rts)
    out=[]
    dt=None
    for idx,rt in enumerate(rts):
        if rt.dt==None: continue
        #print "ord:",rt.a.ordering
        tottime=rt.dt-rt.startdt
        merca=rt.subposa
        mercb=rt.subposb
        curtime=timedelta(0)
        real_heading=rt.tt+rt.wca
        while True:
            if curtime>=tottime:
                break
            f=divide(curtime,tottime)
            fi=1.0-f
            merc=(fi*merca[0]+f*mercb[0],fi*merca[1]+f*mercb[1])
            latlon=mapper.merc2latlon(merc,13)        
            when=rt.startdt+curtime
            ele,azi=sun_position_in_sky(when,latlon[0],latlon[1])
            #print "Sun position: ele=%s, azi=%s, heading=%s"%(ele,azi,real_heading)
            if (ele>-0.5 and ele<25):
                off=(azi-real_heading)
                if abs(off)<25:
                    dirclock=int(round(off/15.0))
                    if dirclock<=0:
                        dirclock+=12
                    out.append(dict(
                        name="Low Sun Warning (Direction: %d o'clock, %.0f deg above horizon. Blinding?)"%(
                                dirclock,max(0,ele)),
                        pos=mapper.to_str(latlon),
                        elev="",
                        elevf=0,
                        dist=0,
                        bearing=azi,
                        closestalt=None,
                        kind='lowsun',
                        dist_from_a=mapper.bearing_and_distance(mapper.from_str(rt.a.pos),latlon)[1],
                        dist_from_b=mapper.bearing_and_distance(mapper.from_str(rt.b.pos),latlon)[1],
                        dir_from_a=describe_dir(rt.tt),
                        dir_from_b=describe_dir((rt.tt+180.0)%360.0),
                        a=rt.a,
                        b=rt.b,
                        id=rt.a.id))
                    print "Generated sun warning:",out[-1]
                    break
            curtime+=timedelta(minutes=2)
    return out
    

def get_terrain_near_route(rts,vertdist,interval=10):
    l=len(rts)
    out=[]
    for idx,rt in enumerate(rts):
        #print "ord:",rt.a.ordering
        if rt.dt==None:
            continue
        merca=rt.subposa
        mercb=rt.subposb
        
        minstep=2
                
        stepcount=rt.d/float(minstep)
        if stepcount>100:
            newstep=rt.d/100.0
            if newstep>minstep:
                minstep=newstep
        if interval<minstep:
            interval=minstep        
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
            elev=get_terrain_elev_in_box_approx(latlon,2*minstep)
            
            
            dist_from_a=mapper.bearing_and_distance(mapper.from_str(rt.a.pos),latlon)[1]
            dist_from_b=rt.d-dist_from_a
            if dist_from_b<0: dist_from_b=0
            
                
                
            
            
            #if isfirstorlast and (along_nm<2.5 or along_nm>d-2.5):
            #    along_nm+=minstep
            #    continue
               
            if (alt-elev<vertdist and
                not (rt.a.stay and dist_from_a<5) and
                not ((rt.b.stay or idx==l-1) and dist_from_b<5) ):

                #print "idx",idx,"ord:",rt.a.ordering
                #print "Terrain warning: ",dict(a=rt.a.waypoint,b=rt.b.waypoint,kind=rt.legpart,startalt=rt.startalt,endalt=rt.endalt,along=alongf,end=end)
                out.append(dict(
                    name="Terrain warning",
                    pos=mapper.to_str(latlon),
                    elev="%.0f"%(elev,),
                    elevf=elev,
                    dist=0,
                    bearing=0,
                    closestalt=alt,
                    kind='terrain',
                    dist_from_a=dist_from_a,
                    dir_from_a=describe_dir(rt.tt),
                    dist_from_b=dist_from_b,
                    dir_from_b=describe_dir((rt.tt+180.0)%360.0),
                    a=rt.a,
                    b=rt.b,
                    id=rt.a.id))
                along_nm+=interval
            else:
                along_nm+=minstep
            if end: 
                break
    return out


def get_stuff_near_route(rts,items,dist,vertdist):
    for item in items:
        try:
            itemmerc=mapper.latlon2merc(mapper.from_str(item['pos']),13)
        except Exception:
            print "Bad coord:",item['pos']
            continue
        itemv=Vertex(int(itemmerc[0]),int(itemmerc[1]))
        onenm=mapper.approx_scale(itemmerc,13,1.0)
        for rt in rts:
            if rt.dt==None: continue
            #print "========================================="
            av=Vertex(int(rt.subposa[0]),int(rt.subposa[1]))
            bv=Vertex(int(rt.subposb[0]),int(rt.subposb[1]))
            l=Line(av,bv)
            linelen=(bv-av).approxlength()
            actualclosest=l.approx_closest(itemv)
            #print item['name'],"A: ",av,"B: ",bv,"clo:",actualclosest
            actualdist=(actualclosest-itemv).approxlength()/onenm
            #print "Actualdist: ",actualdist
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
                #print "Yielding."
                d['name']=d['kind']+': ' +d['name']
                d['dist_from_a']=alongnm_a
                d['dist_from_b']=rt.outer_d-alongnm_a
                d['dir_from_a']=describe_dir(rt.tt)
                d['dir_from_b']=describe_dir((rt.tt+180.0)%360.0)
                d['dist']=actualdist
                d['bearing']=bear
                d['elevf']=itemalt
                if itemalt!=None:
                    d['vertmargin']=altmargin
                d['closestalt']=closealt
                d['a']=rt.a
                d['b']=rt.b
                d['id']=rt.a.id
                yield d
      
            
        
