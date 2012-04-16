#manual import controller
import logging
import traceback
from datetime import datetime
from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect
from fplan.model import meta,User,AirportProjection,AirportMarker
import fplan.extract.parse_landing_chart as parse_landing_chart 
import fplan.extract.extracted_cache as ec
import fplan.lib.mapper as mapper
from fplan.model import meta,User,AirportProjection
import sqlalchemy as sa
import routes.util as h
from fplan.lib.base import BaseController, render
import os
import re
from fplan.lib import customproj
import fplan.lib.transform_map as transform_map
import math
import StringIO

log = logging.getLogger(__name__)
def parselatlon(latlon,arplatlon,rwyends,which):
    print "Interpreting",repr(latlon),"as latlon"
    if latlon==None: 
        return None,0
    if type(latlon) in [str,unicode]:
        latlon=latlon.strip()
        if latlon.lower()=="arp":
            return arplatlon[which],10
    if type(latlon) in [int,float]:
        return float(latlon)
    if latlon=="": return None,0
    if latlon in rwyends:
        return rwyends[latlon][which],10
    if latlon.count(" "):
        deg,dec=latlon.split()
        deg=int(deg)
        dec=float(dec)
        assert deg>0
        return deg+dec/60.0,1
    if abs(float(latlon))>200 and latlon.count("."):
        whole,dec=latlon.split(".")
        deg=whole[:-4]
        min=whole[-4:-2]
        sec=whole[-2:]
        return float(deg)+float(min)/60.0+float(sec+'.'+dec)/3600.0,1
    return float(latlon),1

class AirportprojController(BaseController):
        
    def error(self,err):
        redirect(h.url_for(controller='airportproj',action="index",flash=err))
        
    def get_worklist(self):
        worklist=[]
        for ad in sorted(ec.get_airfields(),key=lambda x:x['name']):
            if not 'adcharts' in ad: continue
            for adchart in ad['adcharts'].values():
                                    
                projurl=h.url_for(controller='airportproj',action="show",ad=ad['name'],checksum=adchart['checksum'])
                found=False
                for proj in meta.Session.query(AirportProjection).filter(sa.and_(
                        AirportProjection.user==session['user'],
                        AirportProjection.airport==ad['name'])).order_by(AirportProjection.updated).all():
                    current=(proj.mapchecksum==str(adchart['checksum']))
                    date=proj.updated
                    airport=proj.airport
                    marks=meta.Session.query(AirportMarker).filter(sa.and_(
                        AirportMarker.user==session['user'],
                        AirportMarker.airport==ad['name'])).all()
                    
                    if current:
                        if len(proj.matrix)==0 or all([x==0 for x in proj.matrix]):
                            needwork=True
                        else:
                            needwork=False
                        worklist.append(dict(current=current,updated=date,airport=airport,url=projurl,marks=marks,needwork=needwork,variant=adchart['variant'],cksum=str(adchart['checksum'])))
                        found=True
                if not found:
                    worklist.append(dict(current=False,updated=None,airport=ad['name'],url=projurl,marks=[],needwork=True,variant=adchart['variant'],cksum=str(adchart['checksum'])))
        return worklist
    def show(self):
        ad=request.params['ad']
        cksum=request.params['checksum']
        chartobj=None
        for adobj in ec.get_airfields():
            bb=False
            if adobj['name']==ad and 'adcharts' in adobj:                
                for adchart in adobj['adcharts'].values():
                    if adchart['checksum']==cksum:
                        chartobj=adchart
                        bb=True
                        break
            if bb: break
        else:
            self.error("No such airport/picture "+ad+"/"+cksum)
        projs=meta.Session.query(AirportProjection).filter(sa.and_(
                    AirportProjection.user==session['user'],
                    AirportProjection.airport==ad,
                    AirportProjection.mapchecksum==adchart['checksum'])).all()
        c.markers=meta.Session.query(AirportMarker).filter(sa.and_(
                    AirportMarker.user==session['user'],
                    AirportMarker.airport==ad,
                    AirportMarker.mapchecksum==adchart['checksum'])).order_by(AirportMarker.latitude,AirportMarker.longitude,AirportMarker.x,AirportMarker.y).all()
        if not projs:            
            proj=AirportProjection()
            proj.user=session['user']
            proj.airport=ad
            proj.mapchecksum=str(adchart['checksum'])
            proj.updated=datetime.utcnow()
            proj.matrix=(1,0,0,1,0,0)
            meta.Session.add(proj)
            meta.Session.flush()
            meta.Session.commit()
        else:
            proj,=projs
            proj.mapchecksum=str(proj.mapchecksum)
            
        if all([x==0 for x in proj.matrix[4:6]]):
            projmatrix=self.invent_matrix(proj.mapchecksum,adchart['variant'])
        else:            
            projmatrix=proj.matrix
            
        A=projmatrix[0:4]
        T=projmatrix[4:6]
        transform=customproj.Transform(A,T)
        c.matrix=projmatrix
        c.initial_scroll_x=request.params.get("scroll_x",0)
        c.initial_scroll_y=request.params.get("scroll_y",0)
        c.maptype=request.params.get("maptype","chart")
        
        c.variant=adchart['variant']
        c.curadmarker=session.get('curadmarker',(0,0))
        c.img=adchart['blobname']+","+adchart['checksum']
        c.flash=None
        c.ad=ad
        c.mapchecksum=adchart['checksum']
        
        c.runways=[]
        c.arp=transform.to_pixels(mapper.from_str(adobj['pos']))
        arp1m=mapper.latlon2merc(mapper.from_str(adobj['pos']),17)
        arp2m=mapper.latlon2merc(mapper.from_str(adobj['pos']),17)
        arp1m=(arp1m[0],arp1m[1]-250)
        arp2m=(arp2m[0]+250,arp2m[1])
        c.arp1=transform.to_pixels(mapper.merc2latlon(arp1m,17))
        c.arp2=transform.to_pixels(mapper.merc2latlon(arp2m,17))
        def dist(x,y):
            return math.sqrt((x[0]-y[0])**2+(x[1]-y[1])**2)
        c.ratio=abs(dist(c.arp,c.arp1)-dist(c.arp,c.arp2))/max(dist(c.arp,c.arp1),dist(c.arp,c.arp2));

        c.transform_reasonable=True
        x,y=c.arp
        if x<-200 or y<-200 or x>=4000 or y>=4000:
            c.transform_reasonable=False   
        c.revmarkers=[]
        c.width,c.height=chartobj['render_width'],chartobj['render_height']
        
        try:
            c.base_coords=\
                [mapper.latlon2merc(transform.to_latlon((0,0)),13),
                mapper.latlon2merc(transform.to_latlon((c.width,0)),13),
                mapper.latlon2merc(transform.to_latlon((0,c.height)),13),
                mapper.latlon2merc(transform.to_latlon((c.width,c.height)),13)]
        except Exception:
            print "problem with basecoords:",traceback.format_exc()
            c.base_coords=[(0,0) for x in xrange(4)]

        
        for mark in c.markers:
            lat,lon=transform.to_latlon((mark.x,mark.y))
            if mark.latitude:
                lat=mark.latitude
            if mark.longitude:
                lon=mark.longitude
            pos=transform.to_pixels((lat,lon))
            c.revmarkers.append(pos)
        for rwy in adobj.get('runways',[]):
            ends=rwy['ends']
            latlon1=mapper.from_str(ends[0]['pos'])
            latlon2=mapper.from_str(ends[1]['pos'])
            print rwy,"Runway pos",latlon1," to ",latlon2
            p1=transform.to_pixels(latlon1)
            p2=transform.to_pixels(latlon2)
            for p in [p1,p2]:
                x,y=p
                if x<-200 or y<-200 or x>=4000 or y>=4000:
                    c.transform_reasonable=False
            c.runways.append((
                              (int(p1[0]),int(p1[1])),
                              (int(p2[0]),int(p2[1]))
                              ))
        
        return render('/airportproj.mako')
                    
    def invent_matrix(self,cksum,variant):
        print "Variant:",variant
        for ad in ec.get_airfields():
            if not 'adcharts' in ad: continue
            dbb=False
            for adchart in ad['adcharts'].values():
                if adchart['checksum']==cksum:
                    lat,lon=mapper.from_str(ad['pos'])
                    dbb=True
                    break
            if dbb:break
        else:
            raise Exception("Can't find this chart in aipdata") 
        
        w=
        if variant=='.VAC':
            scale=2*1000
        else:
            scale=30*1000

        matrix=[0,1.0/(scale*math.cos(lat/(180/math.pi))),-1.0/(scale),0,lat+1/(scale/1000.0),lon-1/(scale/1000.0)/math.cos(lat/(180/math.pi))]
        print "Fake projection:",matrix
        return matrix
        
    def showimg(self):
        adimg,cksum=request.params['adimg'].split(",")
        maptype=request.params['maptype']
        variant=request.params['variant']
        response.headers['Content-Type'] = 'image/png'
        response.headers['Pragma'] = ''
        response.headers['Cache-Control'] = 'max-age=20'

        if maptype=='chart':
            return parse_landing_chart.get_chart_png(adimg,cksum)
        else:
            
            width,height=parse_landing_chart.get_width_height(adimg,cksum)
            projs=meta.Session.query(AirportProjection).filter(sa.and_(
                        AirportProjection.user==session['user'],
                        AirportProjection.mapchecksum==cksum)).all()
            assert len(projs)<=1
            if len(projs)==1 and not all([x==0 for x in projs[0].matrix[4:6]]):
                matrix=projs[0].matrix
                print "Using real projection",matrix
            else:
                #scale = number of pixels per latlon-increment
                matrix=self.invent_matrix(cksum,variant)
                
            A=matrix[0:4]
            T=matrix[4:6]
            transform=customproj.Transform(A,T)                
            
            llc=transform.to_latlon((width/2,height/2))
            print "Center of map in pixels is on lat lon",llc
            
            ll1=transform.to_latlon((0,0))
            ll2=transform.to_latlon((0,height))
            ll3=transform.to_latlon((width,height))
            ll4=transform.to_latlon((width,0))
            im=transform_map.get_png(width,height,ll1,ll2,ll3,ll4)
            io=StringIO.StringIO()
            im.save(io,format='png')
            io.seek(0)
            return io.read()
        
                
    
    
    
    
    def save(self):
        print request.params
        
        ad=request.params['ad']        
        for adobj in ec.get_airfields():
            if adobj['name']==ad:
                break
        else:
            self.error("No such airport"+ad)
        mapchecksum=request.params['mapchecksum']
        marks=dict()        
        for param,val in request.params.items():
            if param in ["save","ad",'mapchecksum','scroll_x','scroll_y','maptype']:
                continue
            if param.startswith("del"):
                continue
            if param.startswith("set_"):
                x,y=[int(v) for v in param.split("_")[1:]]
                session['curadmarker']=(x,y)
                session.save()
                continue            
            if param=="add":
                xs=meta.Session.query(AirportMarker.x).filter(sa.and_(
                    AirportMarker.user==session['user'],
                    AirportMarker.airport==ad
                    )).all()
                if xs:
                    maxx=max(xs)[0]+1
                else:
                    maxx=0
                marks[(maxx,0)]=dict(latitude=None,longitude=None,x=maxx,y=0)
                session['curadmarker']=(maxx,0)
                session.save()
                continue
            
            sx,sy,attrib=re.match(ur"mark_(\d+)_(\d+)_(\w*)",param).groups()
            x=int(sx)
            y=int(sy)
            marks.setdefault((x,y),dict())[attrib]=val
        
        thresholds=dict()
        for rwy in adobj.get('runways',[]):
            ends=rwy['ends']
            for end in ends:
                thresholds[end['thr']]=mapper.from_str(end['pos'])
            
        for param,val in request.params.items():
            if param.startswith("del_"):
                x,y=[int(v) for v in param.split("_")[1:]]
                marks.pop((x,y))
                continue
            
        meta.Session.query(AirportMarker).filter(sa.and_(
                AirportMarker.user==session['user'],
                AirportMarker.airport==ad)).delete()
        ms=[]
        arppos=mapper.from_str(adobj['pos'])
        
        
        for (x,y),val in marks.items():
            m=AirportMarker()
            m.user=session['user']
            m.airport=ad
            m.mapchecksum=str(mapchecksum)
            m.x=int(val['x'])
            m.y=int(val['y'])
            
            m.latitude,w1=parselatlon(val['latitude'],arppos,thresholds,0)
            m.longitude,w2=parselatlon(val['longitude'],arppos,thresholds,1)
            if w1 or w2:
                m.weight=w1+w2
            else:
                m.weigth=1
                
            meta.Session.add(m)
            ms.append(m)

        proj=meta.Session.query(AirportProjection).filter(sa.and_(
            AirportProjection.user==session['user'],
            AirportProjection.airport==ad,
            AirportProjection.mapchecksum==str(mapchecksum))).one()

        def both_lat_lon(x):
            return x.latitude and x.longitude
        def neither_lat_lon(x):
            return not x.latitude and not x.longitude
        def just_lat(x):
            return x.latitude and not x.longitude
        def just_lon(x):
            return not x.latitude and x.longitude
        ms=[m for m in ms if not neither_lat_lon(m)]
        if (len(ms)==4 and
            len([m for m in ms if just_lat(m)])==2 and
            len([m for m in ms if just_lon(m)])==2):
            extra=[]
            for m in ms:
                n=AirportMarker()
                n.x=m.x
                n.y=m.y                    
                if just_lat(m):
                    n.latitude=m.latitude
                    n.x+=1000
                    extra.append(n)
                if just_lon(m):
                    n.y+=1000                    
                    n.longitude=m.longitude
                    extra.append(n)
            ms.extend(extra)
            
        if len(ms)==2 and all(both_lat_lon(x) for x in ms):
            mark1,mark2=ms            
            lm1,lm2=[mapper.latlon2merc((mark.latitude,mark.longitude),17) for mark in [mark1,mark2]]
            ld=(lm2[0]-lm1[0],lm2[1]-lm1[1])
            pd=(mark2.x-mark1.x,mark2.y-mark1.y)
            lm3=(lm1[0]-ld[1],lm1[1]+ld[0])
            pm3=(mark1.x-pd[1],mark1.y+pd[0])
            llm3=mapper.merc2latlon(lm3,17)
            
            m=AirportMarker()
            m.x=pm3[0]
            m.y=pm3[1]
            m.latitude,w1=llm3[0],1
            m.longitude,w2=llm3[1],1
            ms.append(m)
            print "delta pixels",pd
            print "delta latlon",ld
            print "extra end pixels",m.x,m.y
            print "extra end latlon",m.latitude,m.longitude
            
        eqns=0
        for m in ms:
            if both_lat_lon(m): eqns+=2
            elif just_lat(m): eqns+=1
            elif just_lon(m): eqns+=1
            
        try:
            if eqns<4: raise Exception("Unsolvable")
            error,A,T=customproj.solve(ms)
            matrix=list(A)+list(T)
            if proj.matrix:
                oldmatrix=list(proj.matrix)
                newmatrix=list(A)+list(T)
                diff=sum(abs(a-b) for a,b in zip(oldmatrix,newmatrix))
            else:
                diff=1e30 #enough to trigger update
            if diff>1e-12:
                proj.matrix=tuple(newmatrix)
                proj.updated=datetime.utcnow().replace(microsecond=0)
        except Exception,cause:
            print "Couldn't solve projection equation %s"%(cause,)
            proj.matrix=[1,0,0,1,0,0]
            proj.updated=datetime.utcnow().replace(microsecond=0)
            meta.Session.add(proj)

        print "About to save",proj,"matrix:",proj.matrix,"time",proj.updated
        meta.Session.flush();
        meta.Session.commit();
        scroll_x=request.params['scroll_x']
        scroll_y=request.params['scroll_y']
        maptype=request.params['maptype']
        print "scrolls",scroll_x,scroll_y
        redirect(h.url_for(controller='airportproj',action='show',ad=ad,checksum=mapchecksum,scroll_x=scroll_x,scroll_y=scroll_y,maptype=maptype))
        
        
    def index(self,flash=None):
        user=meta.Session.query(User).filter(
                User.user==session['user']).one()
        c.worklist=self.get_worklist()
        c.flash=flash
        return render('/airportsproj.mako')
            
