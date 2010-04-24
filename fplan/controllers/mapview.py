import logging
import math
from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from fplan.model import meta,User,Trip,Waypoint
import fplan.lib.mapper as mapper
import fplan.lib.gen_tile as gen_tile
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
                print "\n\n====DELETING!=====\n%s\n\n"%(rem,)
                    
            for add in added:                
                wp=wps[add]
                waypoint=Waypoint(user.user,trip.trip,wp['pos'],wp['ordinal'],wp['name'])
                print "\n\n====ADDING!=====\n%s %s %s\n\n"%(waypoint.ordinal,waypoint.pos,waypoint.waypoint)
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
                    print "\n\n====UPDATING!=====\n%s %s %s\n\n"%(u.ordinal,u.pos,u.waypoint)
            meta.Session.flush()
            meta.Session.commit();
            
            return "ok"
        except Exception,cause:                    
            raise
            return "notok"        
        
        
    def zoom(self):
        user=meta.Session.query(User).filter(
                User.user==session['user']).one()
        #user.last_map_pos='59,18'
        lat,lon=session['last_map_pos']    
            
        if request.params['zoom']!='':
            zoom=float(request.params['zoom'])
            print "zoom: ",zoom
            
            if zoom<0:
                session['last_map_size']=session['last_map_size']*0.5
            else:
                session['last_map_size']=session['last_map_size']*2.0                                
            if session['last_map_size']<1.0/120.0:
                session['last_map_size']=1.0/120.0            
            if session['last_map_size']>90.0:
                session['last_map_size']=90.0
        if request.params['center']!='':
            lats,lons=request.params['center'].split(",")
            lat=float(lats)
            lon=float(lons)%360.0
        
            
        if lat+session['last_map_size']>85.0:
            lat=85.0-session['last_map_size']
        if lat-session['last_map_size']<-85.0:
            lat=-85.0+session['last_map_size']
        session['last_map_pos']=(lat,lon)
        session.save()        
        meta.Session.flush()
        meta.Session.commit()

        
        redirect_to(h.url_for(controller='mapview',action="index"))

    
    def index(self):
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
            trip=None
            
        if not 'last_map_pos' in session:
            session['last_map_pos']=(59,15)
        if not 'last_map_size' in session:
            session['last_map_size']=5.0
        session.save()        
        
        coords=session['last_map_pos']
        c.pos=mapper.to_aviation_format(coords)
        c.size=session['last_map_size']
        c.lat=coords[0]
        c.lon=coords[1]
        c.waypoints=list(meta.Session.query(Waypoint).filter(sa.and_(
             Waypoint.user==session['user'],Waypoint.trip==session['current_trip'])).all())
        c.tripname=session['current_trip']
        lat1,lon1,lat2,lon2=gen_tile.get_map_corners((100,100),coords,session['last_map_size'])
        print "lat1/lon1: %f/%f, lat2/lon2: %f/%f"%(lat1,lon1,lat2,lon2) 
        assert (abs(lat1-lat2)-session['last_map_size'])<1e-6
        c.lonwidth=abs(lon2-lon1)
        
        return render('/mapview.mako')
