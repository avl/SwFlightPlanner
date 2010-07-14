import fplan.lib.mapper as mapper
from pyshapemerge2d import Vector,Line2,Vertex




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
            print "========================================="
            apos=mapper.latlon2merc(mapper.from_str(rt.a.pos),13)
            av=Vertex(int(apos[0]),int(apos[1]))
            bpos=mapper.latlon2merc(mapper.from_str(rt.b.pos),13)
            bv=Vertex(int(bpos[0]),int(bpos[1]))
            l=Line2(av,bv)
            linelen=(bv-av).approxlength()
            print rt.a.waypoint," - ",rt.b.waypoint
            actualclosest=l.approx_closest(itemv)
            print item['name'],"A: ",av,"B: ",bv,"clo:",actualclosest
            actualdist=(actualclosest-itemv).approxlength()/onenm
            ls=(actualclosest-av).approxlength()
            print "Length from start:",ls
            print "Linelen:",linelen
            if linelen>1e-3:
                along=ls/linelen
            else:
                along=0
            print "Along:",along
            print "Startalt:",rt.startalt," endalt: ",rt.endalt
            closealt=rt.startalt+(rt.endalt-rt.startalt)*along
            print "Altitude at point: ",closealt, " before: ",rt.a.waypoint,rt.b.waypoint
            altmargin=0
            if 'elev' in item:
                itemalt=mapper.parse_elev(item['elev'])
                altmargin=closealt-itemalt
            else:
                itemalt=None
                altmargin=0
            if actualdist<dist and altmargin<vertdist:
                bear=mapper.approx_bearing_vec(itemv,actualclosest)            
                d=dict(item)
                d['dist']=actualdist
                d['bearing']=bear
                if itemalt!=None:
                    d['vertmargin']=altmargin
                d['closestalt']=closealt
                yield d
      
            
        
