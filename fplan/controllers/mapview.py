import logging
import math
from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect
from fplan.model import meta,User,Trip,Waypoint,Route,Aircraft,SharedTrip,Stay
import fplan.lib.mapper as mapper
#import fplan.lib.gen_tile as gen_tile
from fplan.lib.base import BaseController, render
from fplan.lib.parse_gpx import parse_gpx
from fplan.lib.parse_gpx import parse_gpx_fplan

from fplan.lib.maptilereader import merc_limits
import sqlalchemy as sa
import routes.util as h
import socket
import json
from md5 import md5
from fplan.lib.airspace import get_airfields,get_sigpoints
import fplan.lib.userdata as userdata
from itertools import izip,chain
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
            if session.get('mapvariant',None)=='elev':
                if zoomlevel>8: zoomlevel=8
            else:            
                if zoomlevel>13: zoomlevel=13
            merc_x,merc_y=mapper.latlon2merc(latlon,zoomlevel)
            
        merc_limx1,merc_limy1,merc_limx2,merc_limy2=merc_limits(zoomlevel,conservative=False,hd=True)
        if merc_x>merc_limx2: merc_x=merc_limx2
        if merc_y>merc_limy2: merc_y=merc_limy2
        if merc_x<merc_limx1: merc_x=merc_limx1
        if merc_y<merc_limy1: merc_y=merc_limy1
    
        session['last_pos']=(merc_x,merc_y)
        session['zoom']=zoomlevel
        
        print "Setting pos to %s, zoom = %d"%(mapper.merc2latlon(session['last_pos'],zoomlevel),zoomlevel)
        session.save()

    def get_waypoints(self,parms):
        wpst=dict()
        print "Parms:",parms
        for key,val in parms.items():
            if not key.count('_')==2: continue
            row,ordering,key=key.split("_")
            assert row=='row'            
            wpst.setdefault(int(ordering),dict())[key]=val
        wps=dict()
        for ordering,wp in wpst.items():
            wp['ordering']=ordering
            d=wps.setdefault(int(wp['id']),dict())
            d.update(wp)            
        return wps

    def get_free_tripname(self,tripname):            
        desiredname=tripname
        attemptnr=2
        while meta.Session.query(Trip).filter(sa.and_(Trip.user==session['user'],Trip.trip==tripname)).count():
            tripname=desiredname+"(%d)"%(attemptnr,)
            attemptnr+=1
        return tripname
    def querywpname(self):
        pos=mapper.from_str(request.params['pos'])
        lat,lon=pos
        print "Getwpname:",pos
        zoomlevel=int(request.params['zoomlevel'])
        sigps=get_sigpoints(lat,lon,zoomlevel)
        print "Getwpname sigps:",sigps
        if len(sigps):
            return json.dumps([sigps[0]['name'],mapper.from_str(sigps[0]['pos'])])        
        return "notok"
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
            
            session['mapvariant']=request.params.get('mapvariant','airspace')
                
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
            
            oldwps=set([(wp.id) for wp in meta.Session.query(Waypoint).filter(sa.and_(
                    Waypoint.user==tripuser(),Waypoint.trip==trip.trip)).all()])
            
            newwps=set(wps.keys())
            #print "NEW WPS",wps
            removed=oldwps.difference(newwps)
            added=newwps.difference(oldwps)
            updated=newwps.intersection(oldwps)
            
            print "Removed: ",removed
            
            addedwps=added
            removedwps=removed
            updatedwps=updated
            ordering2wpid=dict()
            for remord in removed:
                meta.Session.query(Waypoint).filter(
                    sa.and_(Waypoint.user==tripuser(),Waypoint.trip==trip.trip,
                            Waypoint.id==remord)).delete()
                #print "\n\n====DELETING!=====\n%s\n\n"%(rem,)
            resultant_by_order=dict()
            resultant_id2order=dict()
            waypointlink=dict()
            for add in added:                
                wp=wps[add]
                waypoint=Waypoint(tripuser(),trip.trip,wp['pos'],int(wp['id']),int(wp['ordering']),wp['name'],wp['altitude'])
                resultant_by_order[int(wp['ordering'])]=waypoint
                resultant_id2order[int(wp['id'])]=wp['ordering']
                #print "\n\n====ADDING!=====\n%s %s %s\n\n"%(waypoint.id,waypoint.pos,waypoint.waypoint)
                meta.Session.add(waypoint)
            for upd in updated:
                wp=wps[upd]
                us=meta.Session.query(Waypoint).filter(
                    sa.and_(Waypoint.user==tripuser(),Waypoint.trip==trip.trip,
                            Waypoint.id==upd)).all()
                if len(us)>0:
                    u=us[0]
                    prevpos=mapper.from_str(u.pos)
                    newpos=mapper.from_str(wp['pos'])
                    approxdist=(prevpos[0]-newpos[0])**2+(prevpos[1]-newpos[1])**2
                    if approxdist>(1.0/36000.0)**2: #if moved more than 0.1 arc-second, otherwise leave be.                                        
                        u.pos=wp['pos']
                        print "Waypoint %d moved! (%f deg)"%(u.id,math.sqrt(approxdist))
                    else:
                        print "Waypoint %d has only moved a little (%f deg)"%(u.id,math.sqrt(approxdist))
                        
                    u.waypoint=wp['name']
                    assert u.id==int(wp['id'])
                    u.ordering=wp['ordering']
                    u.altitude=wp['altitude']
                    resultant_by_order[int(wp['ordering'])]=u
                    resultant_id2order[int(wp['id'])]=wp['ordering']
                    #print "\n\n====UPDATING!=====\n%s %s %s\n\n"%(u.id,u.pos,u.waypoint)
            
            #print "Resultant by ordering: %s"%(resultant_by_order,)
            seq=list(sorted(resultant_by_order.items()))
            newroutes=set()
            for (ord1,waypoint1),(ord2,waypoint2) in zip(seq[:-1],seq[1:]):
                if not int(ord1)+1==int(ord2):
                    print "Waypoints %s and %s not consecutive (#%d, #%d)"%(waypoint1,waypoint2,int(ord1),int(ord2))
                assert int(ord1)+1==int(ord2)
                newroutes.add((waypoint1.id,waypoint2.id))

            oldrouteobjs=list(meta.Session.query(Route).filter(sa.and_(
                    Route.user==tripuser(),Route.trip==trip.trip)).all())
            oldroutes=set([(route.waypoint1,route.waypoint2) for route in oldrouteobjs])
            prevalts=dict()
            for rt in oldrouteobjs:
                prevalts[(rt.a.id,+1)]=rt.altitude
                prevalts[(rt.b.id,-1)]=rt.altitude
            
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
                cruisealt=""
                a=None
                if a1 in addedwps:                    
                    startord=resultant_id2order.get(int(a1),0)
                elif a2 in addedwps:
                    startord=resultant_id2order.get(int(a2),0)
                else:
                    startord=resultant_id2order.get(int(a1),0)
                    
                print "Ordering of new wp: %d is %d"%(a1,startord)
                num_waypoints=len(resultant_by_order)
                def searchpattern(begin,num):
                    assert begin>=0 and begin<num
                    down=begin-1
                    up=begin+1
                    while True:
                        work=False
                        if down>=0:
                            yield down
                            down-=1
                            work=True
                        if up<num:
                            yield up
                            up+=1
                            work=True
                        if not work: break
                            
                for wpord in searchpattern(startord,num_waypoints):
                    wp=resultant_by_order.get(wpord,None)
                    print "Searchpattern visiting order: %d"%(wpord,)
                    if wp:
                        if wpord<startord:
                            cruisealt=prevalts.get((wp.id,+1),'')
                            print "Looking for alt previously after wp %d, got: %s"%(wp.id,cruisealt)
                        else:
                            cruisealt=prevalts.get((wp.id,-1),'')
                            print "Looking for alt previously before wp %d, got: %s"%(wp.id,cruisealt)
                        if cruisealt!="": break
                if cruisealt=="":
                    cruisealt="1500"
                r=Route(tripuser(),trip.trip,
                        a1,a2,0,0,tas,None,cruisealt)
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
            #TODO: ONLY FOR TESTING!!!!
            raise
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
            return redirect(h.url_for(controller='mapview',action="index"))
        tripsharing.cancel()
        return redirect(h.url_for(controller='mapview',action="index"))
    def updsharing(self):
        if 'stop' in request.params:
            meta.Session.query(SharedTrip).filter(sa.and_(SharedTrip.user==session['user'],SharedTrip.trip==session.get('current_trip',None))).delete()
            meta.Session.flush()
            meta.Session.commit()
            redirect(h.url_for(controller='mapview',action="share"))

        if 'share' in request.params:
            secret=""
            for c in open("/dev/urandom").read(16):
                secret+=chr(65+(ord(c)%25))
            share=SharedTrip(session['user'],session['current_trip'],secret)
            meta.Session.add(share)
            meta.Session.commit()
            redirect(h.url_for(controller='mapview',action="share"))
        redirect(h.url_for(controller='mapview',action="index"))


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
            pos=mapper.merc2latlon(tuple([int(x) for x in request.params['center'].split(",")]),zoomlevel)
            if session.get('mapvariant',None)=='elev':
                if zoomlevel>8: zoomlevel=8
            else:                
                if zoomlevel>13: zoomlevel=13
            print "Zoomlevel: %s"%(zoomlevel,)    
            print "Pos:",pos
            self.set_pos_zoom(pos,zoomlevel)

        redirect(h.url_for(controller='mapview',action="index"))
    
    def upload_track(self):
        print "In upload",request.params.get("gpstrack",None)
        if 'asplan' in request.params:
            t=request.params.get("gpstrack",None)
            orderint=0
            curid=100
            tripsharing.cancel()
            tripname,waypoints=parse_gpx_fplan(t.value)
            tripname=self.get_free_tripname(tripname)
            trip=Trip(tripuser(), tripname)
            meta.Session.add(trip)
            meta.Session.flush()
            for waypoint in waypoints:
                name=waypoint['name']
                pos=waypoint['pos']
                alt=waypoint['alt']
                waypoint=Waypoint(tripuser(),trip.trip,pos,curid,orderint,name,alt)
                meta.Session.add(waypoint)
                orderint+=1
                curid+=1

            acs=meta.Session.query(Aircraft).filter(sa.and_(
                Aircraft.user==tripuser())).all()
            if len(acs):
                trip.aircraft=acs[0].aircraft

            session['current_trip']=tripname
            session.save()       
            meta.Session.commit()
            redirect(h.url_for(controller='mapview',action="zoom",zoom='auto'))
            return
        t=request.params.get("gpstrack",None)
        if t!=None:
            if len(t.value)>30000000:
                redirect(h.url_for(controller='error',action="document",message="GPX file is too large."))
            session['showtrack']=parse_gpx(t.value,request.params.get('start'),request.params.get('end'))
            session['showarea']=''
            session['showarea_id']=''
            session.save()
        redirect(h.url_for(controller='mapview',action="zoom",zoom='auto'))
            
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
        if request.params.get('reversetripname',None):
            tripsharing.cancel()
            username=tripuser()
            print "Reversing"
            tripname=request.params['reversetripname']
            wps=list(meta.Session.query(Waypoint).filter(sa.and_(Waypoint.user==username,Waypoint.trip==tripname)).order_by(Waypoint.ordering).all())
            if len(wps):
                maxord=max([wp.ordering for wp in wps])
                for wp in wps:
                    wp.ordering=maxord+1-wp.ordering
                    print "Reversed order of",wp.waypoint," = ",wp.ordering
                    meta.Session.add(wp)
                firststays=meta.Session.query(Stay).filter(sa.and_(Stay.user==username,Stay.trip==tripname,Stay.waypoint_id==wps[0].id)).all()
                if len(firststays)==1:
                    stay,=firststays
                    stay.waypoint_id=wps[-1].id
            
        if request.params.get('copytripname',None):
            tripsharing.cancel()
            tripobj=meta.Session.query(Trip).filter(sa.and_(Trip.user==tripuser(),
                Trip.trip==request.params['copytripname'])).first()
            newtripname=self.get_free_tripname(tripobj.trip+"(copy)")            
            trip = Trip(tripuser(), newtripname)
            meta.Session.add(trip)
            acs=meta.Session.query(Aircraft).filter(sa.and_(
                Aircraft.user==tripuser(),Aircraft.aircraft==tripobj.aircraft)).all()
            if len(acs):
                trip.aircraft=acs[0].aircraft
            
            for origwp in meta.Session.query(Waypoint).filter(sa.and_(Waypoint.user==tripuser(),Waypoint.trip==tripobj.trip)).all():
                wp=Waypoint(user=origwp.user,trip=newtripname,pos=origwp.pos,id_=origwp.id,
                            ordering=origwp.ordering,waypoint=origwp.waypoint,altitude=origwp.altitude)
                meta.Session.add(wp)
            for origrt in meta.Session.query(Route).filter(sa.and_(Route.user==tripuser(),Route.trip==tripobj.trip)).all():
                rt=Route(user=origrt.user,trip=newtripname,waypoint1=origrt.waypoint1,waypoint2=origrt.waypoint2,tas=origrt.tas,
                         winddir=origrt.winddir,windvel=origrt.windvel,variation=origrt.variation)
                meta.Session.add(rt)
            for origstay in meta.Session.query(Stay).filter(sa.and_(Stay.user==tripuser(),Stay.trip==tripobj.trip)).all():
                stay=Stay(user=origstay.user,trip=newtripname,waypoint_id=origstay.waypoint_id,
                          fuel=origstay.fuel,date_of_flight=origstay.date_of_flight,
                          departure_time=origstay.departure_time,
                          nr_persons=origstay.nr_persons,fueladjust=origstay.fueladjust)
                meta.Session.add(stay)
            print "Adding trip:",trip
            session['current_trip']=newtripname
            session.save()       
            
        if request.params.get('deletetripname',None) and not tripsharing.sharing_active():
            meta.Session.query(Trip).filter(sa.and_(Trip.user==tripuser(),
                Trip.trip==request.params['deletetripname'])).delete()
            del session['current_trip']
            session.save()
            
        meta.Session.flush()
        meta.Session.commit();
        redirect(h.url_for(controller='mapview',action="index"))
        
        
    def index(self):
        print "Index called", session.get('zoom',-1)
        #print "index called",request.params
        #user=meta.Session.query(User).filter(
        #        User.user==tripuser()).one()
        user=meta.Session.query(User).filter(
                User.user==session['user']).one()
                
        ua=request.headers.get('User-Agent','').lower()
        c.ie=False    
        if ua.count("msie") and not (ua.count("firefox") or ua.count("chrom") or ua.count("safari")):
            c.ie=True
        #print "IE mode:",c.ie
        
        c.all_trips=list(meta.Session.query(Trip).filter(Trip.user==session['user']).all())
        print "current trip:",session.get('current_trip',None)
        if not ('current_trip' in session) or session['current_trip']==None:            
            if user.lasttrip!=None:
                print "Reusing lasttrip:",user.lasttrip
                session['current_trip']=user.lasttrip        
        
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
                trip=min(trips,key=lambda x:x.trip) #Select first trip, alphabetically - we have no better idea.
            session['current_trip']=trip.trip
            session.save()
            trip=None
        if session.get('current_trip',None)!=user.lasttrip:
            user.lasttrip=session.get('current_trip',None)
            print "Storing lasttrip=",user.lasttrip
            meta.Session.flush()
            meta.Session.commit()
            
        c.mapvariant=session.get('mapvariant',"airspace")

        self.set_pos_zoom()
        zoomlevel=session['zoom']
        if c.mapvariant=="elev":
            if zoomlevel>8:
                session['zoom']=8
                session.save()
                try:
                    session['last_pos']=mapper.latlon2merc(mapper.merc2latlon(session['last_pos'],zoomlevel),8)
                except Exception:
                    session['last_pos']=mapper.latlon2merc((59,18),8)
                    print "Setting session last pos to 59,18",session['last_pos']
                zoomlevel=8
                
        print "Last pos is:",mapper.merc2latlon(session['last_pos'],zoomlevel)
        c.merc_x,c.merc_y=session['last_pos']
        
        c.merc5_limx1,c.merc5_limy1,c.merc5_limx2,c.merc5_limy2=merc_limits(5,conservative=False,hd=True)

        
                                        
        c.waypoints=list(meta.Session.query(Waypoint).filter(sa.and_(
             Waypoint.user==tripuser(),Waypoint.trip==session['current_trip'])).order_by(Waypoint.ordering).all())
        c.tripname=session['current_trip']
        c.showarea=session.get('showarea','')
        c.showtrack=session.get('showtrack',None)!=None
        c.fastmap=user.fastmap;
        #print "Zoomlevel active: ",zoomlevel
        c.zoomlevel=zoomlevel
        c.dynamic_id=''
        c.sharing=tripsharing.sharing_active()
        c.mtime=maptilereader.get_mtime()
        for way in c.waypoints:
            print "Name:",way.waypoint
        if len(c.waypoints):
            c.next_waypoint_id=max([way.id for way in c.waypoints])+1
        else:
            c.next_waypoint_id=100
        assert type(c.next_waypoint_id)==int
        if c.sharing:
            c.shared_by=tripuser()
        if session.get('showarea',''):
            c.dynamic_id=session.get('showarea_id','')
        if session.get('showtrack',''):
            if hasattr(session['showtrack'],'dynamic_id'):
                c.dynamic_id=session['showtrack'].dynamic_id
        return render('/mapview.mako')
        

    def coordparse(self):
        val=request.params['val']
        try:
            s=mapper.anyparse(val)
            c.pos=s
            c.deg,c.degmin,c.degminsec=mapper.to_all_formats(mapper.from_str(s))
            print "Rendering mako coordpres"            
            return render("/coordpres.mako")        
        except Exception:        
            print "returning empty string , coordpres"
            return ""
        
        
        
