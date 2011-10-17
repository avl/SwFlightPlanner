#manual import controller
import logging
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
import math

log = logging.getLogger(__name__)
def parselatlon(latlon,arplatlon,rwyends,which):
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
            if not 'adchart' in ad: continue            
            projurl=h.url_for(controller='airportproj',action="show",ad=ad['name'])
            found=False
            for proj in meta.Session.query(AirportProjection).filter(sa.and_(
                    AirportProjection.user==session['user'],
                    AirportProjection.airport==ad['name'])).order_by(AirportProjection.updated).all():
                current=(proj.mapchecksum==str(ad['adchart']['checksum']))
                date=proj.updated
                airport=proj.airport
                marks=meta.Session.query(AirportMarker).filter(sa.and_(
                    AirportMarker.user==session['user'],
                    AirportMarker.airport==ad['name'])).all()
                
                worklist.append(dict(current=current,updated=date,airport=airport,url=projurl,marks=marks))
                found=True
            if not found:
                worklist.append(dict(current=False,updated=None,airport=ad['name'],url=projurl,marks=[]))
        return worklist
    def show(self):
        ad=request.params['ad']
        for adobj in ec.get_airfields():
            if adobj['name']==ad and 'adchart' in adobj:
                break
        else:
            self.error("No such airport"+ad)
        projs=meta.Session.query(AirportProjection).filter(sa.and_(
                    AirportProjection.user==session['user'],
                    AirportProjection.airport==ad,
                    AirportProjection.mapchecksum==adobj['adchart']['checksum'])).all()
        c.markers=meta.Session.query(AirportMarker).filter(sa.and_(
                    AirportMarker.user==session['user'],
                    AirportMarker.airport==ad,
                    AirportMarker.mapchecksum==adobj['adchart']['checksum'])).order_by(AirportMarker.latitude,AirportMarker.longitude,AirportMarker.x,AirportMarker.y).all()
        if not projs:            
            proj=AirportProjection()
            proj.user=session['user']
            proj.airport=ad
            proj.mapchecksum=str(adobj['adchart']['checksum'])
            proj.updated=datetime.utcnow()
            proj.matrix=(1,0,0,1,0,0)
            meta.Session.add(proj)
            meta.Session.flush()
            meta.Session.commit()
        else:
            proj,=projs
            proj.mapchecksum=str(proj.mapchecksum)
            
        A=proj.matrix[0:4]
        T=proj.matrix[4:6]
        transform=customproj.Transform(A,T)
        c.matrix=proj.matrix
                
        c.curadmarker=session.get('curadmarker',(0,0))
        c.img=adobj['adchart'].get('image',adobj['icao']+'.png')
        c.flash=None
        c.ad=ad
        c.mapchecksum=adobj['adchart']['checksum']
        
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
                    
    
    def showimg(self):
        adimg=request.params['adimg']
        response.headers['Content-Type'] = 'image/png'
        response.headers['Pragma'] = ''
        response.headers['Cache-Control'] = 'max-age=20'

        return parse_landing_chart.get_chart_png(adimg)
    def save(self):
        ad=request.params['ad']        
        for adobj in ec.get_airfields():
            if adobj['name']==ad and 'adchart' in adobj:
                break
        else:
            self.error("No such airport"+ad)
        mapchecksum=request.params['mapchecksum']
        marks=dict()        
        for param,val in request.params.items():
            if param in ["save","ad",'mapchecksum']:
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
            
        try:
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

        print "About to save",proj,"matrix:",proj.matrix,"time",proj.updated
        meta.Session.flush();
        meta.Session.commit();
        
        redirect(h.url_for(controller='airportproj',action='show',ad=ad))
        
        
    def index(self,flash=None):
        user=meta.Session.query(User).filter(
                User.user==session['user']).one()
        c.worklist=self.get_worklist()
        c.flash=flash
        return render('/airportsproj.mako')
            
