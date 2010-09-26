import logging
import math
from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from fplan.model import meta,User,Trip,Waypoint,Route,Aircraft,SharedTrip
import fplan.lib.mapper as mapper
#import fplan.lib.gen_tile as gen_tile
from fplan.lib.base import BaseController, render
from fplan.lib.parse_gpx import parse_gpx
from fplan.lib.maptilereader import merc_limits
import sqlalchemy as sa
import routes.util as h
import socket
import json
from md5 import md5
from datetime import datetime
log = logging.getLogger(__name__)
import fplan.lib.tripsharing as tripsharing
from fplan.lib.tripsharing import tripuser
import fplan.lib.maptilereader as maptilereader

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
            
            oldname=request.params.get('oldtripname','')
            tripname=request.params.get('tripname','')
            if tripsharing.sharing_active():
                #Can't rename trips while tripsharing is active!                
                tripname=session['current_trip']
                if oldname!=session['current_trip']:
                    #In some strange way a non-tripsharing oldname appeared in the post. This
                    #means that something has gone awry. Don't save!
                    print "Bad trip oldname while tripsharing active!"
                    return "notok"
                    
            if 'showarea' in request.params and request.params['showarea']:
                sha=request.params['showarea']
                if (sha=='.'):
                    session['showarea']=''
                    session['showarea_id']=''
                    session['showtrack']=None
                else:
                    session['showarea']=sha
                    session['showarea_id']=md5(sha.encode('utf8')).hexdigest()
                    session['showtrack']=None
            
            if int(request.params.get('showairspaces',0)):
                session['showairspaces']=True
            else:
                session['showairspaces']=False
                
            #print "Req:",request.params
            oldtrip=None
            if not oldname.strip():
                oldname=tripname
            oldtrips=meta.Session.query(Trip).filter(sa.and_(Trip.user==tripuser(),Trip.trip==oldname)).all()
            if len(oldtrips)==1:
                oldtrip=oldtrips[0]
            if oldtrip:
                trip=oldtrip
                if trip.trip!=tripname:
                    if tripsharing.sharing_active():
                        #attempt to rename someone elses trip! Can't be allowed! set tripname to old name
                        print "Attempt to rename trip while viewing shared trip (tripsharing)"
                        return "notok"
                    else:
                        trip.trip=self.get_free_tripname(tripname)
                if session['current_trip']!=trip.trip and tripsharing.sharing_active():
                    #internal error if we get here - the earlier test for current_trip not changing failed.
                    print "Unexpected tripsharing error #2"
                    return "notok"
                    
                session['current_trip']=trip.trip
            else:
                if tripsharing.sharing_active():
                    #we use sharing, but the shared trip can't be found!
                    print "Tripsharing active, but named trip didn't exist (deleted, probably)"
                    return "notok"
                tripname=self.get_free_tripname(tripname)
                trip = Trip(tripuser(), tripname)
                acs=meta.Session.query(Aircraft).filter(sa.and_(
                    Aircraft.user==tripuser())).all()
                if len(acs):
                    trip.aircraft=acs[0].aircraft

                meta.Session.add(trip)
                session['current_trip']=tripname
            
            oldwps=set([(wp.ordinal) for wp in meta.Session.query(Waypoint).filter(sa.and_(
                    Waypoint.user==tripuser(),Waypoint.trip==trip.trip)).all()])
            
            newwps=set(wps.keys())
            #print "NEW WPS",wps
            removed=oldwps.difference(newwps)
            added=newwps.difference(oldwps)
            updated=newwps.intersection(oldwps)
            for remord in removed:
                meta.Session.query(Waypoint).filter(
                    sa.and_(Waypoint.user==tripuser(),Waypoint.trip==trip.trip,
                            Waypoint.ordinal==remord)).delete()
                #print "\n\n====DELETING!=====\n%s\n\n"%(rem,)
            resultant_by_ordinal=dict()
            for add in added:                
                wp=wps[add]
                waypoint=Waypoint(tripuser(),trip.trip,wp['pos'],wp['ordinal'],wp['name'],wp['altitude'])
                resultant_by_ordinal[wp['ordinal']]=waypoint
                #print "\n\n====ADDING!=====\n%s %s %s\n\n"%(waypoint.ordinal,waypoint.pos,waypoint.waypoint)
                meta.Session.add(waypoint)
            for upd in updated:
                wp=wps[upd]
                us=meta.Session.query(Waypoint).filter(
                    sa.and_(Waypoint.user==tripuser(),Waypoint.trip==trip.trip,
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
                    u.altitude=wp['altitude']
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
                    Route.user==tripuser(),Route.trip==trip.trip)).all()])
            
            #Routes:
            removed=oldroutes.difference(newroutes)
            added=newroutes.difference(oldroutes)
            updated=newroutes.intersection(oldroutes)
            print "Removed routes:",removed
            print "Added routes:",added
            print "Kept routes: ",updated
            for rem1,rem2 in removed:
                meta.Session.query(Route).filter(
                    sa.and_(Route.user==tripuser(),Route.trip==trip.trip,
                            Route.waypoint1==rem1,Route.waypoint2==rem2)).delete()
            sel_acs=meta.Session.query(Aircraft).filter(sa.and_(
                Aircraft.aircraft==trip.aircraft,Aircraft.user==tripuser())).all()
            if len(sel_acs):
                tas=sel_acs[0].cruise_speed
            else:
                tas=75
            for a1,a2 in added:
                r=Route(tripuser(),trip.trip,
                        a1,a2,0,0,tas,None,1000)
                meta.Session.add(r)
            
            session.save()

            meta.Session.flush()
            meta.Session.commit();
            
            ret=json.dumps([tripname])
            print "mapview returning json:",ret
            return ret
        except Exception,cause:                    
            #print line number and stuff as well
            print cause
            return "notok"        
        
    def share(self):
        if tripsharing.sharing_active():
            c.error=u"The current trip has been shared with you by its creator. You cannot create new URLs for sharing it further. You can, however, send the same link you got, to anyone."            
        else:
            if not 'current_trip' in session:
                c.error=u"There is no current trip that can be shared"
            else:
                c.trip=session['current_trip']
                shares=meta.Session.query(SharedTrip).filter(sa.and_(SharedTrip.user==session['user'],SharedTrip.trip==session.get('current_trip',None))).all()
                if len(shares)==0:
                    c.sharing=False
                else:
                    share,=shares
                    c.sharing=True
                    c.sharelink="http://"+socket.gethostname()+"/mapview/shared?secret="+share.secret
        return render("/share.mako")
        
    def shared(self):
        shares=meta.Session.query(SharedTrip).filter(SharedTrip.secret==request.params['secret']).all()
        if len(shares):
            myshare,=shares
            tripsharing.view_other(user=myshare.user,trip=myshare.trip)
            return redirect_to(h.url_for(controller='mapview',action="index"))
        tripsharing.cancel()
        return redirect_to(h.url_for(controller='mapview',action="index"))
    def updsharing(self):
        if 'stop' in request.params:
            meta.Session.query(SharedTrip).filter(sa.and_(SharedTrip.user==session['user'],SharedTrip.trip==session.get('current_trip',None))).delete()
            meta.Session.flush()
            meta.Session.commit()
            redirect_to(h.url_for(controller='mapview',action="share"))

        if 'share' in request.params:
            secret=""
            for c in open("/dev/urandom").read(16):
                secret+=chr(65+(ord(c)%25))
            share=SharedTrip(session['user'],session['current_trip'],secret)
            meta.Session.add(share)
            meta.Session.commit()
            redirect_to(h.url_for(controller='mapview',action="share"))
        redirect_to(h.url_for(controller='mapview',action="index"))


    def zoom(self):
        print "zoom called"
        #user=meta.Session.query(User).filter(
        #        User.user==tripuser()).one()
                
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
        #print "trip actions:",request.params
            
        if request.params.get('addtripname',None):
            tripsharing.cancel()
            tripname=self.get_free_tripname(request.params['addtripname'])
            trip = Trip(tripuser(), tripname)
            acs=meta.Session.query(Aircraft).filter(sa.and_(
                Aircraft.user==tripuser())).all()
            if len(acs):
                trip.aircraft=acs[0].aircraft
            
            print "Adding trip:",trip
            meta.Session.add(trip)
            session['current_trip']=tripname
            session.save()       
        if request.params.get('opentripname',None):
            tripsharing.cancel()
            tripname=request.params['opentripname']
            if meta.Session.query(Trip).filter(sa.and_(Trip.user==tripuser(),
                Trip.trip==tripname)).count():
                session['current_trip']=tripname
                session.save()
            
        if request.params.get('deletetripname',None) and not tripsharing.sharing_active():
            meta.Session.query(Trip).filter(sa.and_(Trip.user==tripuser(),
                Trip.trip==request.params['deletetripname'])).delete()
            del session['current_trip']
            session.save()
            
        meta.Session.flush()
        meta.Session.commit();
        redirect_to(h.url_for(controller='mapview',action="index"))
        
        
    def index(self):
        #print "index called",request.params
        #user=meta.Session.query(User).filter(
        #        User.user==tripuser()).one()
        
        c.all_trips=list(meta.Session.query(Trip).filter(Trip.user==session['user']).all())
        if 'current_trip' in session and meta.Session.query(Trip).filter(sa.and_(
                Trip.user==tripuser(),
                Trip.trip==session['current_trip']
                    )).count()==0:
            session['current_trip']=None
                        
        if not 'current_trip' in session or session['current_trip']==None:
            trips=meta.Session.query(Trip).filter(
                Trip.user==tripuser()).all()
            if len(trips)==0:
                trip = Trip(tripuser(), "Default Trip")
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
             Waypoint.user==tripuser(),Waypoint.trip==session['current_trip'])).order_by(Waypoint.ordinal).all())
        c.tripname=session['current_trip']
        c.showarea=session.get('showarea','')
        c.showtrack=session.get('showtrack',None)!=None
        c.show_airspaces=session.get('showairspaces',True)
        user=meta.Session.query(User).filter(
                User.user==session['user']).one()
        c.fastmap=user.fastmap;
        #print "Zoomlevel active: ",zoomlevel
        c.zoomlevel=zoomlevel
        c.dynamic_id=''
        c.sharing=tripsharing.sharing_active()
        c.mtime=maptilereader.get_mtime()
        if c.sharing:
            c.shared_by=tripuser()
        if session.get('showarea',''):
            c.dynamic_id=session.get('showarea_id','')
        if session.get('showtrack',''):
            if hasattr(session['showtrack'],'dynamic_id'):
                c.dynamic_id=session['showtrack'].dynamic_id
        return render('/mapview.mako')
        
