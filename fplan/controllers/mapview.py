import logging
import math
from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from fplan.model import meta,User,Trip,Waypoint,Route,Aircraft
import fplan.lib.mapper as mapper
#import fplan.lib.gen_tile as gen_tile
from fplan.lib.base import BaseController, render
from fplan.lib.parse_gpx import parse_gpx
from fplan.lib.maptilereader import merc_limits
import sqlalchemy as sa
import routes.util as h
import json
from md5 import md5

log = logging.getLogger(__name__)

class MapviewController(BaseController):      

    def set_pos_zoom(self,latlon=None,zoom=None):
        #print "Setting pos to %s"%(latlon,)
        if latlon==None:
            assert zoom==None
            zoomlevel=session.get('zoom',None)
            if zoomlevel==None:
                zoomlevel=5
                merc_x,merc_y=mapper.latlon2merc((58,18),zoomlevel)
            else:
                merc_x,merc_y=session['last_pos']
        else:
            assert zoom!=None            
            zoomlevel=zoom
            if zoomlevel<5:
                zoomlevel=5
            if zoomlevel>13:
                zoomlevel=13            
            merc_x,merc_y=mapper.latlon2merc(latlon,zoomlevel)
            
        merc_limx1,merc_limy1,merc_limx2,merc_limy2=merc_limits(zoomlevel,conservative=False)
        if merc_x>merc_limx2: merc_x=merc_limx2
        if merc_y>merc_limy2: merc_y=merc_limy2
        if merc_x<merc_limx1: merc_x=merc_limx1
        if merc_y<merc_limy1: merc_y=merc_limy1
    
        session['last_pos']=(merc_x,merc_y)
        session['zoom']=zoomlevel
        #print "Setting pos to %s"%(mapper.merc2latlon(session['last_pos'],zoomlevel),)
        session.save()        

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
            d=wps.setdefault(wp['ordinal'],dict())
            d.update(wp)            
        return wps

    def get_free_tripname(self,tripname):            
        desiredname=tripname
        attemptnr=2
        while meta.Session.query(Trip).filter(sa.and_(Trip.user==session['user'],Trip.trip==tripname)).count():
            tripname=desiredname+"(%d)"%(attemptnr,)
            attemptnr+=1
        return tripname
        
    def save(self):
        try:
            if 'pos' in request.params and 'zoomlevel' in request.params:
                save_merc_x,save_merc_y=[int(x) for x in request.params['pos'].split(",")]
                save_zoom=int(request.params['zoomlevel'])
                pos=mapper.merc2latlon((save_merc_x,save_merc_y),save_zoom)
                self.set_pos_zoom(pos,save_zoom)
                

            wps=self.get_waypoints(request.params)
            
            user=meta.Session.query(User).filter(
                User.user==session['user']).one()
            oldname=request.params.get('oldtripname','')
            tripname=request.params.get('tripname','')
            if 'showarea' in request.params and request.params['showarea']:
                sha=request.params['showarea']
                if (sha=='.'):
                    session['showarea']=''
                    session['showarea_id']=''
                    session['showtrack']=None
                else:
                    session['showarea']=sha
                    session['showarea_id']=md5(sha).hexdigest()
                    session['showtrack']=None
            
            if int(request.params.get('showairspaces',0)):
                session['showairspaces']=True
            else:
                session['showairspaces']=False
                
            #print "Req:",request.params
            oldtrip=None
            if not oldname.strip():
                oldname=tripname
            oldtrips=meta.Session.query(Trip).filter(sa.and_(Trip.user==user.user,Trip.trip==oldname)).all()
            if len(oldtrips)==1:
                oldtrip=oldtrips[0]
            if oldtrip:
                trip=oldtrip
                if trip.trip!=tripname:
                    trip.trip=self.get_free_tripname(tripname)
                session['current_trip']=trip.trip
            else:
                tripname=self.get_free_tripname(tripname)
                trip = Trip(user.user, tripname)
                acs=meta.Session.query(Aircraft).filter(sa.and_(
                    Aircraft.user==session['user'])).all()
                if len(acs):
                    trip.aircraft=acs[0].aircraft

                meta.Session.add(trip)
                session['current_trip']=tripname
            
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
                    prevpos=mapper.from_str(u.pos)
                    newpos=mapper.from_str(wp['pos'])
                    approxdist=(prevpos[0]-newpos[0])**2+(prevpos[1]-newpos[1])**2
                    if approxdist>(1.0/36000.0)**2: #if moved more than 0.1 arc-second, otherwise leave be.                                        
                        u.pos=wp['pos']
                        print "Waypoint %d moved! (%f deg)"%(u.ordinal,math.sqrt(approxdist))
                    else:
                        print "Waypoint %d has only moved a little (%f deg)"%(u.ordinal,math.sqrt(approxdist))
                        
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
            sel_acs=meta.Session.query(Aircraft).filter(sa.and_(
                Aircraft.aircraft==trip.aircraft,Aircraft.user==session['user'])).all()
            if len(sel_acs):
                tas=sel_acs[0].cruise_speed
            else:
                tas=75
            for a1,a2 in added:
                r=Route(user.user,trip.trip,
                        a1,a2,0,0,tas,None,1000)
                meta.Session.add(r)
            
            session.save()

            meta.Session.flush()
            meta.Session.commit();
            
            ret=json.dumps([tripname])
            print "mapview returning json:",ret
            return ret
        except Exception,cause:                    
            raise
            return "notok"        
        
    
    def zoom(self):
        print "zoom called"
        user=meta.Session.query(User).filter(
                User.user==session['user']).one()
                
        if request.params['zoom']=='auto':
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
                    self.set_pos_zoom((59,18),6,)
                else:
                    size=max(maxx-minx,maxy-miny)
                    if (maxx==minx and maxy==miny):
                        zoom=10
                    else:
                        nominal_size=400
                        while zoom>=0 and size>nominal_size:
                            zoom-=1
                            size/=2.0                            
                    pos=(int(0.5*(maxx+minx)),int(0.5*(maxy+miny)))                    
                    latlon=mapper.merc2latlon(pos,13)
                    self.set_pos_zoom(latlon,zoom)
            elif session.get('showtrack',None)!=None:
                strack=session.get('showtrack')
                zoom=13
                minx,miny=mapper.latlon2merc(strack.bb1,13)
                maxx,maxy=mapper.latlon2merc(strack.bb2,13)
                pos=(int(0.5*(maxx+minx)),int(0.5*(maxy+miny)))                    
                latlon=mapper.merc2latlon(pos,13)
                print "AutoZooming  to pos",latlon
                size=max(maxx-minx,maxy-miny,1)
                nominal_size=400
                while zoom>=0 and size>nominal_size:
                    zoom-=1
                    size/=2.0                            
                self.set_pos_zoom(latlon,zoom)
            else:
                #mapper.parse_lfv_area()
                self.set_pos_zoom((59,18),6)
            print "Autozoom zooming to level %d at %s"%(session['zoom'],session['last_pos'])
        else:
            zoomlevel=float(request.params['zoom'])
            if zoomlevel<0: zoomlevel=0
            if zoomlevel>13: zoomlevel=13
            print "Zoomlevel: %s"%(zoomlevel,)
    
            pos=mapper.merc2latlon(tuple([int(x) for x in request.params['center'].split(",")]),zoomlevel)
            self.set_pos_zoom(pos,zoomlevel)

        redirect_to(h.url_for(controller='mapview',action="index"))
    
    def upload_track(self):
        print "In upload",request.params.get("gpstrack",None)
        t=request.params.get("gpstrack",None)
        if t!=None:
            if len(t.value)>30000000:
                redirect_to(h.url_for(controller='error',action="document",message="GPX file is too large."))
            session['showtrack']=parse_gpx(t.value,request.params.get('start'),request.params.get('end'))
            session['showarea']=''
            session['showarea_id']=''
            session.save()
        redirect_to(h.url_for(controller='mapview',action="zoom",zoom='auto'))
            
    def trip_actions(self):
        print "trip actions:",request.params
        if request.params.get('addtripname',None):
            tripname=self.get_free_tripname(request.params['addtripname'])
            trip = Trip(session['user'], tripname)
            acs=meta.Session.query(Aircraft).filter(sa.and_(
                Aircraft.user==session['user'])).all()
            if len(acs):
                trip.aircraft=acs[0].aircraft
            
            print "Adding trip:",trip
            meta.Session.add(trip)
            session['current_trip']=tripname
            session.save()       
        if request.params.get('opentripname',None):
            tripname=request.params['opentripname']
            if meta.Session.query(Trip).filter(sa.and_(Trip.user==session['user'],
                Trip.trip==tripname)).count():
                session['current_trip']=tripname
                session.save()
            
        if request.params.get('deletetripname',None):
            meta.Session.query(Trip).filter(sa.and_(Trip.user==session['user'],
                Trip.trip==request.params['deletetripname'])).delete()
            del session['current_trip']
            
        meta.Session.flush()
        meta.Session.commit();
        redirect_to(h.url_for(controller='mapview',action="index"))
        
        
    def index(self):
        #print "index called",request.params
        user=meta.Session.query(User).filter(
                User.user==session['user']).one()
        
        c.all_trips=list(meta.Session.query(Trip).filter(Trip.user==session['user']).all())
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


        self.set_pos_zoom()
        zoomlevel=session['zoom']
        c.merc_x,c.merc_y=session['last_pos']
        
        c.merc_limx1,c.merc_limy1,c.merc_limx2,c.merc_limy2=merc_limits(zoomlevel,conservative=False)

        
                                        
        c.waypoints=list(meta.Session.query(Waypoint).filter(sa.and_(
             Waypoint.user==session['user'],Waypoint.trip==session['current_trip'])).order_by(Waypoint.ordinal).all())
        c.tripname=session['current_trip']
        c.showarea=session.get('showarea','')
        c.showtrack=session.get('showtrack',None)!=None
        c.show_airspaces=session.get('showairspaces',True)
        c.fastmap=user.fastmap;
        #print "Zoomlevel active: ",zoomlevel
        c.zoomlevel=zoomlevel
        c.dynamic_id=''
        if session.get('showarea',''):
            c.dynamic_id=session.get('showarea_id','')
        if session.get('showtrack',''):
            if hasattr(session['showtrack'],'dynamic_id'):
                c.dynamic_id=session['showtrack'].dynamic_id
        return render('/mapview.mako')
        
