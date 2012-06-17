#encoding=utf8
import logging
import math
import cairo
import StringIO
import sqlalchemy as sa
import fplan.extract.extra_airfields as extra_airfields
#from md5 import md5
from fplan.model import meta,User,Aircraft
from datetime import datetime
from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect
import routes.util as h
from fplan.lib.base import BaseController, render
import fplan.extract.gfs_weather as gfs_weather
import fplan.lib.tripsharing as tripsharing
import re
import os
import fplan.lib.metartaf as metartaf
import fplan.lib.mapper as mapper
import traceback
import json
import fplan.extract.extracted_cache as ec
log = logging.getLogger(__name__)
from fplan.controllers.flightplan import strip_accents
import fplan.lib.bsptree as bsptree 
def filter(ad):
    if not 'runways' in ad: return False
    return True
class SufperformanceController(BaseController):

    def search(self):
        print "Search called:",request.params
        
        term=strip_accents(request.params['term']).lower()
        if len(term)<3:
            return json.dumps([])
        response.headers['Content-Type'] = 'application/json'
        
        hits=[]
        for ac in ec.get_airfields():
            if not filter(ac): continue
            if (strip_accents(ac['name']).lower().count(term)):
                hits.append(ac['name'])
        hits.sort()
        return json.dumps(hits[:10])
    def load(self):
        name=request.params['name']
        #print "Loading",repr(name)
        ret=json.dumps(dict(runways=[]))
        for ac in ec.get_airfields():
            if not filter(ac): continue
            if ac['name']==name:
                physical=[]
                if 'runways' in ac:
                    ret=self.load_ad_json(ac)
                    break                                
        response.headers['Content-Type'] = 'application/json'
        return ret
    
    def load_ad_json(self,ac):
        out=[]
        physical=[]
    
        for rwy in ac['runways']:
            curphys=[]
            for i,end in enumerate(rwy['ends']):
                endb=rwy['ends'][(i+1)%2]
                usable_pos=end.get("usable_pos",end['pos'])
                usable_posb=endb.get("usable_pos",endb['pos'])
                brg1,takeoff_dist=mapper.bearing_and_distance(mapper.from_str(usable_pos),mapper.from_str(usable_posb))
                brg2,landing_dist=mapper.bearing_and_distance(mapper.from_str(end['pos']),mapper.from_str(usable_posb))
                brgdummy,threshold_dist=mapper.bearing_and_distance(mapper.from_str(usable_pos),mapper.from_str(end['pos']))
                out.append(dict(
                    name=end['thr'],
                    rwyhdg=brg1,
                    available_landing=landing_dist*1852.0,
                    available_takeoff=takeoff_dist*1852.0,
                    threshold=threshold_dist*1852.0                       
                    ))
                curphys.append(dict(
                        name=end['thr'],
                        pos=end['pos'],
                        usable_pos=end.get("usable_pos",end['pos']),
                        threshold=threshold_dist*1852.0))
            physical.append(curphys)
        jsonstr=json.dumps(dict(runways=out,physical=physical))
        print "JSON:",jsonstr
        return jsonstr

    
    def getmap(self):
        #print "DAta:",request.params
        data=json.loads(request.params['data'])
        ad=data['ad']
        perf=data['perf']
        what=data['what']
        #print "Perf:",perf
        imgsize=300
        im=cairo.ImageSurface(cairo.FORMAT_RGB24,imgsize,imgsize)
        ctx=cairo.Context(im)
        def getpos(xd):
            return xd.get('usable_pos',xd['pos'])
        if 'physical' in ad:
            def getdist_meter(p1,p2):
                brg,dist=mapper.bearing_and_distance(mapper.merc2latlon(p1,20),mapper.merc2latlon(p2,20))
                return dist*1852.0
            def draw_cmds():
                for d in ad['physical']:
                    yield (mapper.latlon2merc(mapper.from_str(getpos(d[0])),20),
                            mapper.latlon2merc(mapper.from_str(getpos(d[1])),20),
                           d[0]['name'],d[1]['name'],d[0]['threshold'],d[1]['threshold'])
            def justmercs():
                for p1,p2,n1,n2,t1,t2 in draw_cmds():
                    yield p1
                    yield p2
                
                
                
            bb=bsptree.bb_from_mercs(justmercs())
            center=(0.5*(bb.x1+bb.x2),0.5*(bb.y1+bb.y2))
            #print "Center:",center
            mercradius=max(bb.x2-bb.x1,bb.y2-bb.y1)
            scaling=(imgsize/1.3)/mercradius
            def topixel(merc):
                off=(merc[0]-center[0],merc[1]-center[1])
                return (off[0]*scaling+imgsize/2,off[1]*scaling+imgsize/2)
            
            def draw_marker(ctx,p1,p2,thresholdratio,msg,col=(1,0,0)):
                ninety=[p2[1]-p1[1],p2[0]-p1[0]]                    
                ninety=[ninety[0],-ninety[1]]
                
                
                
                #if ninety[0]<0:
                #    ninety[0],ninety[1]=-ninety[0],-ninety[1]
                #print "ninety:",ninety
                p1=topixel(p1)
                p2=topixel(p2)
                d=[p1[0]+thresholdratio*(p2[0]-p1[0]),
                    p1[1]+thresholdratio*(p2[1]-p1[1])]
                
                """
                dB=[d[0]+ninety[0],d[1]+ninety[1]]
                
                
                if dB[0]>0.75*imgsize:
                    ninety[0],ninety[1]=-ninety[0],-ninety[1]
                elif dB[0]<0.25*imgsize:
                    ninety[0],ninety[1]=-ninety[0],-ninety[1]
                elif dB[1]<0.25*imgsize:
                    ninety[0],ninety[1]=-ninety[0],-ninety[1]
                elif dB[1]>0.75*imgsize:
                    ninety[0],ninety[1]=-ninety[0],-ninety[1]
                
                dB=[d[0]+ninety[0],d[1]+ninety[1]]
                """
                
                ctx.new_path()
                
                ctx.set_source(cairo.SolidPattern(*(col+(1,))))
                ctx.arc(d[0],d[1],6,0,2*math.pi)
                ctx.fill()
                ctx.new_path()
                
                ctx.move_to(*d)
                ctx.save()
                ang=math.atan2(ninety[1],ninety[0])*180.0/3.1415
                                            
                if ang>90 or ang <-90:
                    ang=(ang+180)%360                                
                    
                angrad=ang*(math.pi/180)
                ctx.translate(*d)
                ctx.rotate(angrad)
                
                ctx.set_font_size(17);                
                ext=ctx.text_extents(msg)[:4]
                w=ext[2]
                cand1=ctx.user_to_device(10+w/2,0)
                cand2=ctx.user_to_device(-10-w/2,0)
                
                def edgedist(x):
                    return min(x[0],x[0]-imgsize,x[1],x[1]-imgsize)
                
                if edgedist(cand1)>edgedist(cand2):
                    dC=[10,-ext[1]/2]
                else:
                    dC=[-10-w,-ext[1]/2]
                #dC=[dB[0],dB[1]]
                ctx.move_to(*dC)                
                ctx.show_text(msg)
                ctx.restore()
                
            
            for p1,p2,n1,n2,t1,t2 in draw_cmds():
                                    
                
                
                print "n1:",n1,"n2:",n2
                print "p1:",mapper.merc2latlon(p1,20)
                print "p2:",mapper.merc2latlon(p2,20)
                pix1=topixel(p1)
                pix2=topixel(p2)
                
                ctx.set_source(cairo.SolidPattern(0.5,0.5,0.5,1))
                ctx.new_path()
                ctx.set_line_width(10)
                ctx.move_to(*pix1)
                ctx.line_to(*pix2)
                ctx.stroke()
                
            for p1,p2,n1,n2,t1,t2 in draw_cmds():
                print "Matching",n1,n2,"to",perf['name']
                if n2==perf['name']:
                    p1,n1,t1,p2,n2,t2=p2,n2,t2,p1,n1,t1 
                if n1==perf['name']:
                    runwaylen=getdist_meter(p1,p2)
                    startratio=perf["start"]/runwaylen
                    start300ratio=perf["start300"]/runwaylen
                    startrollratio=perf["start_roll"]/runwaylen
                    
                    thresholdratio=t1/runwaylen
                    landingratio=thresholdratio+perf["land"]/runwaylen
                    landingrollratio=thresholdratio+perf["landing_roll"]/runwaylen
                    
                    if what=='start':        
                        draw_marker(ctx,p1,p2,0,"Start",col=(1,0,0))
                        draw_marker(ctx,p1,p2,startrollratio,"Lättning",col=(1,0.5,0))
                        draw_marker(ctx,p1,p2,startratio,"15m höjd",col=(1,1,0))
                        draw_marker(ctx,p1,p2,start300ratio,"300 fot höjd",col=(0,1,0))
                    if what=='landing':                        
                        draw_marker(ctx,p1,p2,thresholdratio,"15m tröskelhöjd ",col=(1,0,0))
                        draw_marker(ctx,p1,p2,landingrollratio+0.43*landingratio,"Senaste sättning",col=(1,0.5,0))
                        draw_marker(ctx,p1,p2,1.43*landingratio,"Senaste stopp",(0,1,0))
                        
                    
                    
                
                
        buf=StringIO.StringIO()
        im.write_to_png(buf)
        png=buf.getvalue()
        response.headers['Content-Type'] = 'image/png'
        return png


    def index(self):
        when,valid,fct=gfs_weather.get_prognosis(datetime.utcnow())
        lat=59.45862
        lon=17.70680
        c.qnh=1013
        c.winddir=0
        c.windvel=0
        
        c.defaddata=self.load_ad_json(extra_airfields.frolunda)
        c.field=u"Frölunda"
        c.searchurl=h.url_for(controller='sufperformance',action='search')
        c.airport_load_url=h.url_for(controller='sufperformance',action='load')
        metar=metartaf.get_metar('ESSA')
        print "metar:",metar
        try:
            c.temp,dew=re.match(r".*\b(\d{2})/(\d{2})\b.*",metar.text).groups()
            print "c.temp:",c.temp
            if c.temp.startswith("M"):
                c.temp=-int(c.temp[1:])
            else:
                c.temp=int(c.temp)
        except:
            print traceback.format_exc()
            c.temp=15
        try:
            c.qnh=fct.get_qnh(lat,lon)
            if c.qnh<10:        
                c.qnh=1013
            c.winddir,c.windvel=fct.get_surfacewind(lat,lon)
            c.winddir=int(c.winddir)
            c.windvel=int(c.windvel)
        except:
            print traceback.format_exc()
            pass
        
        return render('/sufperformance.mako')
