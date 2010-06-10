import logging
import math
from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from fplan.model import meta,User,Trip,Waypoint,Route
import fplan.lib.mapper as mapper
#import fplan.lib.gen_tile as gen_tile
from fplan.lib.base import BaseController, render
from fplan.lib.parse_gpx import parse_gpx
from fplan.lib.maptilereader import merc_limits
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
            wpst.setdefault(int(ordinal),dict())[key]=val
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
            d=wps.setdefault(wp['ordinal'],dict())
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
                    session['showtrack']=None
                else:
                    session['showarea']=sha
                    session['showtrack']=None
                    print "Saved showarea:",sha                
            
            if int(request.params.get('showairspaces',0)):
                session['showairspaces']=True
            else:
                session['showairspaces']=False
                
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
            
            oldwps=set([(wp.ordinal) for wp in meta.Session.query(Waypoint).filter(sa.and_(
                    Waypoint.user==user.user,Waypoint.trip==trip.trip)).all()])
            
            newwps=set(wps.keys())
            #print "NEW WPS",wps
            removed=oldwps.difference(newwps)
            added=newwps.difference(oldwps)
            updated=newwps.intersection(oldwps)
            for remord in removed:
                meta.Session.query(Waypoint).filter(
                    sa.and_(Waypoint.user==user.user,Waypoint.trip==trip.trip,
                            Waypoint.ordinal==remord)).delete()
                #print "\n\n====DELETING!=====\n%s\n\n"%(rem,)
            resultant_by_ordinal=dict()
            for add in added:                
                wp=wps[add]
                waypoint=Waypoint(user.user,trip.trip,wp['pos'],wp['ordinal'],wp['name'])
                resultant_by_ordinal[wp['ordinal']]=waypoint
                #print "\n\n====ADDING!=====\n%s %s %s\n\n"%(waypoint.ordinal,waypoint.pos,waypoint.waypoint)
                meta.Session.add(waypoint)
            for upd in updated:
                wp=wps[upd]
                us=meta.Session.query(Waypoint).filter(
                    sa.and_(Waypoint.user==user.user,Waypoint.trip==trip.trip,
                            Waypoint.ordinal==upd)).all()
                if len(us)>0:
                    u=us[0]
                    u.pos=wp['pos']
                    u.waypoint=wp['name']
                    u.ordinal=wp['ordinal']
                    resultant_by_ordinal[wp['ordinal']]=u
                    #print "\n\n====UPDATING!=====\n%s %s %s\n\n"%(u.ordinal,u.pos,u.waypoint)
            
            print "Resultant by ordinal: %s"%(resultant_by_ordinal,)
            seq=list(sorted(resultant_by_ordinal.items()))
            newroutes=set()
            for (ord1,waypoint1),(ord2,waypoint2) in zip(seq[:-1],seq[1:]):
                if not int(ord1)+1==int(ord2):
                    print "Waypoints %s and %s not consecutive (#%d, #%d)"%(waypoint1,waypoint2,int(ord1),int(ord2))
                assert int(ord1)+1==int(ord2)
                newroutes.add((waypoint1.ordinal,waypoint2.ordinal))
            oldroutes=set([(route.waypoint1,route.waypoint2) for route in meta.Session.query(Route).filter(sa.and_(
                    Route.user==user.user,Route.trip==trip.trip)).all()])
            
            #Routes:
            removed=oldroutes.difference(newroutes)
            added=newroutes.difference(oldroutes)
            updated=newroutes.intersection(oldroutes)
            print "Removed routes:",removed
            print "Added routes:",added
            print "Kept routes: ",updated
            for rem1,rem2 in removed:
                meta.Session.query(Route).filter(
                    sa.and_(Route.user==user.user,Route.trip==trip.trip,
                            Route.waypoint1==rem1,Route.waypoint2==rem2)).delete()
            for a1,a2 in added:
                r=Route(user.user,trip.trip,
                        a1,a2,0,0,75,None,1000)
                meta.Session.add(r)
            
            session.save()

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
            elif session.get('showtrack',None)!=None:
                strack=session.get('showtrack')
                zoom=13
                minx,miny=mapper.latlon2merc(strack.bb1,zoom)
                maxx,maxy=mapper.latlon2merc(strack.bb2,zoom)
                size=max(maxx-minx,maxy-miny,1)
                nominal_size=400
                while zoom>=0 and size>nominal_size:
                    zoom-=1
                    size/=2.0                            
                    session['zoom']=zoom                    
                pos=(int(0.5*(maxx+minx)),int(0.5*(maxy+miny)))                    
                latlon=mapper.merc2latlon(pos,13)
                session['last_pos']=mapper.latlon2merc(latlon,zoom)
                
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
            if len(t.value)>30000000:
                redirect_to(h.url_for(controller='error',action="document",message="GPX file is too large."))
            session['showtrack']=parse_gpx(t.value,request.params.get('start'),request.params.get('end'))
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
        c.show_airspaces=session.get('showairspaces',True)
        print "Zoomlevel active: ",zoomlevel
        c.merc_limx1,c.merc_limy1,c.merc_limx2,c.merc_limy2=merc_limits(zoomlevel)
        c.zoomlevel=zoomlevel
        return render('/mapview.mako')
        
