#manual import controller
import logging
from datetime import datetime
from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect
from fplan.model import meta,User,AirportProjection,AirportMarker
import fplan.extract.extracted_cache as ec
import fplan.lib.mapper as mapper
from fplan.model import meta,User,AirportProjection
import sqlalchemy as sa
import routes.util as h
from fplan.lib.base import BaseController, render
import os
import re

log = logging.getLogger(__name__)
def parselatlon(latlon):
    if latlon==None: 
        return None
    if type(latlon) in [int,float]:
        return float(latlon)
    if latlon.strip()=="": return None
    if latlon.count(" "):
        deg,dec=latlon.split()
        deg=int(deg)
        dec=float(dec)
        assert deg>0
        return deg+dec/60.0
    return float(latlon)

class AirportprojController(BaseController):
    def __init__(self):
        self.worklist=[]
        
    def error(self,err):
        redirect(h.url_for(controller='airportproj',action="index",flash=err))
        
    def update_worklist(self):
        self.worklist=[]
        for ad in sorted(ec.get_airfields(),key=lambda x:x['name']):
            if not 'adchart' in ad: continue            
            projurl=h.url_for(controller='airportproj',action="show",ad=ad['name'])
            for proj in meta.Session.query(AirportProjection).filter(sa.and_(
                    AirportProjection.user==session['user'],
                    AirportProjection.airport==ad['name'])).order_by(AirportProjection.updated).all():
                current=(proj.mapchecksum==ad['adchart']['checksum'])
                date=proj.updated
                airport=proj.airport
                self.worklist.append(dict(current=current,updated=date,airport=airport,url=projurl))
            else:
                self.worklist.append(dict(current=False,updated=None,airport=ad['name'],url=projurl))
                
    def show(self):
        ad=request.params['ad']
        for adobj in ec.get_airfields():
            if adobj['name']==ad and 'adchart' in adobj:
                break
        else:
            self.error("No such airport"+ad)
        projs=meta.Session.query(AirportProjection).filter(sa.and_(
                    AirportProjection.user==session['user'],
                    AirportProjection.airport==ad)).all()
        c.markers=meta.Session.query(AirportMarker).filter(sa.and_(
                    AirportMarker.user==session['user'],
                    AirportMarker.airport==ad)).order_by(AirportMarker.x+AirportMarker.y).all()
        if not projs:            
            proj=AirportProjection()
            proj.user=session['user']
            proj.airport=ad
            proj.mapchecksum=adobj['adchart']['checksum']
            proj.updated=datetime.utcnow()
            proj.matrix=[1,0,0,1,0,0]
            meta.Session.add(proj)
            meta.Session.flush()
            meta.Session.commit()
        else:
            proj,=projs
        c.arp=mapper.from_str(adobj['pos'])
        c.matrix=proj.matrix
                
        c.curadmarker=session.get('curadmarker',(0,0))
        print "marker",c.curadmarker        
        c.img=adobj['adchart'].get('image',adobj['icao']+'.png')
        c.flash=None
        c.ad=ad
        c.mapchecksum=adobj['adchart']['checksum']
        
        return render('/airportproj.mako')
                    
    
    def showimg(self):
        adimg=request.params['adimg']
        tmppath=os.path.join(os.getenv("SWFP_DATADIR"),"adcharts",adimg)
        response.headers['Content-Type'] = 'image/png'
        response.headers['Pragma'] = ''
        response.headers['Cache-Control'] = 'max-age=20'

        return open(tmppath).read()
    def save(self):
        ad=request.params['ad']        
        mapchecksum=request.params['mapchecksum']
        marks=dict()        
        print request.params
        for param,val in request.params.items():
            if param in ["save","ad",'mapchecksum']:
                continue
            if param.startswith("del"):
                continue
            if param.startswith("set_"):
                x,y=[int(v) for v in param.split("_")[1:]]
                session['curadmarker']=(x,y)
                session.save()
                print "set marker",session['curadmarker']
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
                print maxx
                marks[(maxx,0)]=dict(latitude=None,longitude=None,x=maxx,y=0)
                session['curadmarker']=(maxx,0)
                session.save()
                continue
            print "param:",param
            sx,sy,attrib=re.match(ur"mark_(\d+)_(\d+)_(\w*)",param).groups()
            x=int(sx)
            y=int(sy)
            marks.setdefault((x,y),dict())[attrib]=val
        
        for param,val in request.params.items():
            if param.startswith("del_"):
                x,y=[int(v) for v in param.split("_")[1:]]
                marks.pop((x,y))
                continue
            
        meta.Session.query(AirportMarker).filter(sa.and_(
                AirportMarker.user==session['user'],
                AirportMarker.airport==ad)).delete()
        print "Saving",marks
        for (x,y),val in marks.items():
            m=AirportMarker()
            m.user=session['user']
            m.airport=ad
            m.mapchecksum=mapchecksum
            m.x=int(val['x'])
            m.y=int(val['y'])
            m.latitude=parselatlon(val['latitude'])
            m.longitude=parselatlon(val['longitude'])
            meta.Session.add(m)
                           
            
                
        meta.Session.flush();
        meta.Session.commit();
        
        redirect(h.url_for(controller='airportproj',action='show',ad=ad))
        
        
    def index(self,flash=None):
        user=meta.Session.query(User).filter(
                User.user==session['user']).one()
        if self.worklist==[]:
            self.update_worklist()
        c.flash=flash
        c.worklist=self.worklist
        return render('/airportsproj.mako')
            
