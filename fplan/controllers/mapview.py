import logging
import math
from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from fplan.model import meta,User,Trip,Waypoint
import fplan.lib.mapper as mapper
#import fplan.lib.gen_tile as gen_tile
from fplan.lib.base import BaseController, render


import sqlalchemy as sa
import routes.util as h
log = logging.getLogger(__name__)

class MapviewController(BaseController):      

    def get_waypoints(self,parms):
        wpst=dict()
        print "Parms:",parms
        for key,val in parms.items():
            if not key.count('_')==2: continue
            row,ordinal,key=key.split("_")
            assert row=='row'            
            wpst.setdefault(ordinal,dict())[key]=val
        wps=dict()
        for ordinal,wp in wpst.items():
            wp['ordinal']=ordinal
            origpos=wp['origpos']
            newpos=wp['pos']
            olat,olon=mapper.from_str(origpos)
            nlat,nlon=mapper.from_str(newpos)
            dist=math.sqrt((olat-nlat)**2+(olon-nlon)**2)
            print "Wp #%s dist: %s"%(ordinal,dist)
            if (dist<1.0/3600.0):
                wp['pos']=wp['origpos']
                print "Wp #%s has not moved"%(ordinal,)
            d=wps.setdefault(wp['pos'],dict())
            d.update(wp)
            
        return wps
            
        
    def save(self):
        try:

            wps=self.get_waypoints(request.params)
            
            user=meta.Session.query(User).filter(
                User.user==session['user']).one()
            oldname=request.params.get('oldtripname','')
            tripname=request.params.get('tripname','')
            if 'showarea' in request.params and request.params['showarea']:
                sha=request.params['showarea']
                if (sha=='.'):
                    session['showarea']=''
                else:
                    session['showarea']=sha
                    session['showtrack']=None
                    print "Saved showarea:",sha                
                session.save()
            
            #print "Req:",request.params
            oldtrip=None
            if oldname.strip():
                oldtrips=meta.Session.query(Trip).filter(sa.and_(Trip.user==user.user,Trip.trip==oldname)).all()
                if len(oldtrips)==1:
                    oldtrip=oldtrips[0]
            if oldtrip:
                trip=oldtrip
                trip.trip=tripname
            else:
                trip = Trip(user.user, tripname)
                meta.Session.add(trip)                    
            
            oldwps=set([wp.pos for wp in meta.Session.query(Waypoint).filter(sa.and_(
                    Waypoint.user==user.user,Waypoint.trip==trip.trip)).all()])
            newwps=set(wps.keys())
            #print "NEW WPS",wps
            removed=oldwps.difference(newwps)
            added=newwps.difference(oldwps)
            updated=newwps.intersection(oldwps)
            for rem in removed:
                meta.Session.query(Waypoint).filter(
                    sa.and_(Waypoint.user==user.user,Waypoint.trip==trip.trip,
                            Waypoint.pos==rem)).delete()
                #print "\n\n====DELETING!=====\n%s\n\n"%(rem,)
                    
            for add in added:                
                wp=wps[add]
                waypoint=Waypoint(user.user,trip.trip,wp['pos'],wp['ordinal'],wp['name'])
                #print "\n\n====ADDING!=====\n%s %s %s\n\n"%(waypoint.ordinal,waypoint.pos,waypoint.waypoint)
                meta.Session.add(waypoint)
            for upd in updated:
                wp=wps[upd]
                us=meta.Session.query(Waypoint).filter(
                    sa.and_(Waypoint.user==user.user,Waypoint.trip==trip.trip,
                            Waypoint.pos==upd)).all()
                if len(us)>0:
                    u=us[0]
                    u.pos=wp['pos']
                    u.waypoint=wp['name']
                    u.ordinal=wp['ordinal']
                    #print "\n\n====UPDATING!=====\n%s %s %s\n\n"%(u.ordinal,u.pos,u.waypoint)
            meta.Session.flush()
            meta.Session.commit();
            
            return "ok"
        except Exception,cause:                    
            raise
            return "notok"        
        
    
    def zoom(self):
        print "zoom called"
        user=meta.Session.query(User).filter(
                User.user==session['user']).one()
                
        if request.params['zoom']=='auto':
            print "showarea: ",session.get('showarea','')
            if session.get('showarea','')!='':                
                zoom=13
                minx=1e30
                maxx=-1e30
                miny=1e30
                maxy=-1e30                
                for vert in mapper.parse_lfv_area(session.get('showarea')):
                    merc=mapper.latlon2merc(mapper.from_str(vert),zoom)
                    minx=min(minx,merc[0])
                    miny=min(miny,merc[1])
                    maxx=max(maxx,merc[0])
                    maxy=max(maxy,merc[1])                
                if maxy<-1e29:                                    
                    session['zoom']=6 #no vertices...   
                    session['last_pos']=mapper.latlon2merc((59,18),6)
                else:
                    size=max(maxx-minx,maxy-miny)
                    if (maxx==minx and maxy==miny):
                        zoom=10
                    else:
                        nominal_size=400
                        while zoom>=0 and size>nominal_size:
                            zoom-=1
                            size/=2.0                            
                    session['zoom']=zoom                    
                    pos=(int(0.5*(maxx+minx)),int(0.5*(maxy+miny)))                    
                    latlon=mapper.merc2latlon(pos,13)
                    session['last_pos']=mapper.latlon2merc(latlon,zoom)
            #elif session.get('showtrack',None)!=None:
            #    pass
            else:
                #mapper.parse_lfv_area()
                session['zoom']=6               
                session['last_pos']=mapper.latlon2merc((59,18),6)
            print "Autozoom zooming to level %d at %s"%(session['zoom'],session['last_pos'])
        else:
            zoomlevel=float(request.params['zoom'])
            if zoomlevel<0: zoomlevel=0
            if zoomlevel>13: zoomlevel=13
            print "Zoomlevel: %s"%(zoomlevel,)
    
            pos=mapper.from_str(request.params['center'])
            session['last_pos']=pos
            session['zoom']=zoomlevel

        pos=session['last_pos']
        zoomlevel=session['zoom']

        mercmaxx=mapper.max_merc_x(zoomlevel)    
        mercmaxy=mapper.max_merc_y(zoomlevel)
            
        pos=list(pos)          
        if pos[0]<0:
            pos[0]=0
        if pos[0]>mercmaxx:
            pos[0]=mercmaxx    
        if pos[1]<0:
            pos[1]=0
        if pos[1]>mercmaxy:
            pos[1]=mercmaxy    
        
        session['last_pos']=pos
        session['zoom']=zoomlevel
        session.save()        
        redirect_to(h.url_for(controller='mapview',action="index"))
    
    def upload_track(self):
        print "In upload",request.params.get("gpstrack",None)
        t=request.params.get("gpstrack",None)
        if t!=None:
            session['showtrack']=str(t.value)
            print "Filesize",len(session['showtrack'])
            session['showarea']=''
            session.save()
            
        redirect_to(h.url_for(controller='mapview',action="zoom",zoom='auto'))
        
    def index(self):
        print "index called"
        user=meta.Session.query(User).filter(
                User.user==session['user']).one()
        
        if 'current_trip' in session and meta.Session.query(Trip).filter(sa.and_(
                Trip.user==session['user'],
                Trip.trip==session['current_trip']
                    )).count()==0:
            session['current_trip']=None
                        
        if not 'current_trip' in session or session['current_trip']==None:
            trips=meta.Session.query(Trip).filter(
                Trip.user==session['user']).all()
            if len(trips)==0:
                trip = Trip(user.user, "Default Trip")
                meta.Session.add(trip)
                meta.Session.flush()
                meta.Session.commit()
            else:
                trip=trips[0]
            session['current_trip']=trip.trip
            session.save()
            trip=None

        zoomlevel=int(session.get('zoom',5))
        pos=session.get('last_pos',mapper.latlon2merc((59,18),zoomlevel)) #Pos is always in the _old_ zoomlevel, even if zoomlevel changes (for now)
                                
        c.merc_x=int(pos[0]);
        c.merc_y=int(pos[1]);        
        c.waypoints=list(meta.Session.query(Waypoint).filter(sa.and_(
             Waypoint.user==session['user'],Waypoint.trip==session['current_trip'])).order_by(Waypoint.ordinal).all())
        c.tripname=session['current_trip']
        c.showarea=session.get('showarea','')
        c.showtrack=session.get('showtrack',None)!=None
        print "Showtrack: %s"%(c.showtrack,)
        c.show_airspaces=session.get('showairspaces',True)
        print "Zoomlevel active: ",zoomlevel
        
        c.zoomlevel=zoomlevel
        return render('/mapview.mako')
        
