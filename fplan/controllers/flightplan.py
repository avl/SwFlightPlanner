#encoding=UTF8
import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from fplan.model import meta,User,Trip,Waypoint,Route,Aircraft,Stay 
from fplan.lib.base import BaseController, render
import sqlalchemy as sa
log = logging.getLogger(__name__)
import fplan.lib.mapper as mapper
import routes.util as h
from fplan.extract.extracted_cache import get_airfields,get_sig_points,get_obstacles
from fplan.lib.airspace import get_airspaces_on_line,get_notam_areas_on_line,get_notampoints_on_line
import json
import re
import fplan.lib.weather as weather
from fplan.lib.calc_route_info import get_route
import fplan.lib.geo as geo
import fplan.lib.notam_geo_search as notam_geo_search
from itertools import chain
from fplan.lib import get_terrain_elev
import fplan.lib.tripsharing as tripsharing
from fplan.lib.tripsharing import tripuser
import fplan.lib.airspace as airspace
from fplan.lib.helpers import lfvclockfmt
from fplan.lib.helpers import parse_clock

import unicodedata
def strip_accents(s):
   return ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))

class AtsException(Exception): pass

class FlightplanController(BaseController):
    def search(self):
        searchstr=request.params.get('search','')

        latlon_match=re.match(r"(\d+)\.(\d+)([NS])(\d+)\.(\d+)([EW])",searchstr)
        if latlon_match:
            latdeg,latdec,ns,londeg,londec,ew=latlon_match.groups()
            lat=float(latdeg)+float("0."+latdec)
            lon=float(londeg)+float("0."+londec)
            if ns in ['S','s']:
                lat=-lat
            if ew in ['W','w']:
                lon=-lon
            return json.dumps([['Unknown Waypoint',[lat,lon]]])                


        #print "Searching for ",searchstr
        searchstr=searchstr.lower()
        points=[]
        for airp in get_airfields():
            if airp['name'].lower().count(searchstr) or \
                airp['icao'].lower().count(searchstr):
                points.append(airp)  
                
        for sigpoint in get_sig_points():
            if sigpoint['name'].lower().count(searchstr):
                points.append(sigpoint)
        if len(points)==0:
            return ""
        points.sort(key=lambda x:x['name'])
        ret=json.dumps([[x['name'],mapper.from_str(x['pos'])] for x in points[:15]])
        #print "returning json:",ret
        return ret
    def save(self):
        #print "Saving tripname:",request.params['tripname']
        trip=meta.Session.query(Trip).filter(sa.and_(Trip.user==tripuser(),
            Trip.trip==request.params['tripname'])).one()
        waypoints=meta.Session.query(Waypoint).filter(sa.and_(
             Waypoint.user==tripuser(),
             Waypoint.trip==request.params['tripname'])).order_by(Waypoint.ordering).all()
            
        #print "Save:",request.params
        if 'startfuel' in request.params:
            try: 
                pass#trip.startfuel=float(request.params['startfuel'])
                #TODO: Add fuel-management again
            except:
                pass
                            
        #print request.params
        for idx,way in enumerate(waypoints):
            dof_s="date_of_flight_%d"%(way.id,)
            dep_s="departure_time_%d"%(way.id,)
            fuel_s="fuel_%d"%(way.id,)
            persons_s="persons_%d"%(way.id,)
            if dof_s in request.params:
                #possibly add new stay
                if not way.stay:
                    print "Adding stay: ord/id",way.ordering,way.id
                    way.stay=Stay(tripuser(),trip.trip,way.id)
                if re.match(ur"\d{2,4}-?\d{2}\-?\d{2}",request.params.get(dof_s,'')):
                    way.stay.date_of_flight=request.params.get(dof_s,'')
                    
                if re.match(ur"\d{2}:?\d{2}",request.params.get(dep_s,'')):
                    way.stay.departure_time=request.params.get(dep_s,'')
                    
                try:
                    way.stay.nr_persons=int(request.params[persons_s])
                except:
                    way.stay.nr_persons=None
                way.stay.fuel=None
                try:
                    way.stay.fuel=float(request.params.get(fuel_s,''))
                except:
                    pass
                way.altitude=str(int(get_terrain_elev.get_terrain_elev(mapper.from_str(way.pos))))
            else:
                #remove any stay
                meta.Session.query(Stay).filter(sa.and_(
                    Stay.user==way.user,Stay.trip==way.trip,Stay.waypoint_id==way.id)).delete()
                way.altitude=''

        for idx,way in enumerate(waypoints[:-1]):
            #print "Found waypoint #%d"%(idx,)    
            route=meta.Session.query(Route).filter(sa.and_(
                Route.user==tripuser(),
                Route.trip==request.params['tripname'],
                Route.waypoint1==way.id,
                )).one()
            for col,att in [
                ('W','winddir'),
                ('V','windvel'),
                ('TAS','tas'),
                ('Alt','altitude'),
                ('Var','variation'),
                ('Dev','deviation')
                ]:
                                                
                key="%s_%d"%(col,way.id)
                val=request.params[key]
                #print "Value of key %s: %s"%(key,val)
                if col=="Alt":
                    setattr(route,att,val[0:6])
                else:
                    try:
                        setattr(route,att,int(val))
                    except:
                        setattr(route,att,0)
                #print "Setting attrib '%s' of object %s to '%s'"%(att,route,val)
        
        if not tripsharing.sharing_active():
            acname=request.params.get('aircraft','').strip()
            if acname!="":
                trip.aircraft=acname
            
        meta.Session.flush()
        meta.Session.commit()
        return "ok"
        
    def weather(self):
        waypoints=meta.Session.query(Waypoint).filter(sa.and_(
             Waypoint.user==tripuser(),
             Waypoint.trip==request.params['tripname'])).order_by(Waypoint.ordering).all()
             
        ret=[]
        alts=request.params.get('alts','')
        if alts==None:
            altvec=[]
        else:
            altvec=alts.split(",")
        for way,altitude in zip(waypoints[:-1],altvec):
             print("Looking for waypoint: %s"%(way.pos,))
             try:
                mapper.parse_elev(altitude)
             except mapper.NotAnAltitude,cause:
                 ret.append(['',''])                 
                 continue #skip this alt
             #N+1 selects....
             route=meta.Session.query(Route).filter(sa.and_(
                  Route.user==tripuser(),
                  Route.trip==request.params['tripname'],
                  Route.waypoint1==way.id,
                  )).one()
             way2=meta.Session.query(Waypoint).filter(sa.and_(
                  Waypoint.user==tripuser(),
                  Waypoint.trip==request.params['tripname'],
                  Waypoint.id==route.waypoint2,
                  )).one()
             merc1=mapper.latlon2merc(mapper.from_str(way.pos),14)
             merc2=mapper.latlon2merc(mapper.from_str(way2.pos),14)
             center=(0.5*(merc1[0]+merc2[0]),0.5*(merc1[1]+merc2[1]))
             lat,lon=mapper.merc2latlon(center,14)
             print "Fetching weather for %s,%s, %s"%(lat,lon,route.altitude)
             we=weather.get_weather(lat,lon)
             if we==None:
                 ret.append(['',''])                 
             else:
                 wi=we.get_wind(altitude)
                 print "Got winds:",wi
                 ret.append([wi['direction'],wi['knots']])
        jsonstr=json.dumps(ret)
        print "returning json:",jsonstr
        return jsonstr
        
        
        

    def gpx(self):
        # Return a rendered template
        #return render('/flightplan.mako')
        # or, return a response
        tripname=session.get('current_trip',None)
        if 'trip' in request.params:
            tripname=request.params['trip']
        if not tripname:
            return u"Internal error. Missing trip-name."
            
        waypoints=list(meta.Session.query(Waypoint).filter(sa.and_(
             Waypoint.user==tripuser(),Waypoint.trip==tripname)).order_by(Waypoint.ordering).all())
        if len(waypoints)==0:
            return redirect_to(h.url_for(controller='flightplan',action="index",flash=u"Must have at least two waypoints in trip!"))
        c.waypoints=[]
        c.trip=tripname
        for wp in waypoints:                    
            lat,lon=mapper.from_str(wp.pos)
            c.waypoints.append(dict(
                lat=lat,
                lon=lon,
                name=wp.waypoint
                ))
        #response.headers['Content-Type'] = 'application/xml'               
        response.content_type = 'application/octet-stream'               
        response.charset="utf8"
        return render('/gpx.mako')

    def ats(self):
        try:
            #waypoints=meta.Session.query(Waypoint).filter(sa.and_(
            #     Waypoint.user==tripuser(),Waypoint.trip==session['current_trip'])).order_by(Waypoint.ordering).all()
            #c.waypoints=[]
            self.standard_prep(c)
            print "Routes:",c.route
            
            def break_subtrips(routes):
                out=[]
                T=0.0
                for i,rt in enumerate(routes):
                    out.append(rt)
                    T+=rt.time_hours
                    if rt.b.stay or i==len(routes)-1:
                        if len(out):
                            yield dict(T=T),out
                        T=0.0
                        out=[]                
                        
                        
            c.atstrips=[]
            last_landing_time=None
            last_fuel_left=None
            nr_persons=None
            for meta,routes in break_subtrips(c.route):
                print "broke ruote",meta
                if len(routes)==0: continue
                at=dict()
                at['T']=meta['T']
                waypoints=[routes[0].a]
                for rt in routes: 
                    waypoints.append(rt.b)
                wps=[]
                stay=routes[0].a.stay
                dep_ad="ZZZZ"
                dep_ad_name=waypoints[0].waypoint
                dep_ad_coords=mapper.format_lfv_ats(*mapper.from_str(waypoints[0].pos))
                dest_ad="ZZZZ"
                dest_ad_name=waypoints[-1].waypoint
                dest_ad_coords=mapper.format_lfv_ats(*mapper.from_str(waypoints[-1].pos))
                extra_remarks=[]
                for i,wp in enumerate(waypoints):
                    at['T']=meta['T']
                    lat,lon=mapper.from_str(wp.pos)         
                    symbolicpos=None
                    airport=None
                    if i==0 or i==len(waypoints)-1:
                        for ad in airspace.get_airfields(lat,lon,11):
                            if not ad['icao'].upper() in ['ZZZZ','ESVF']:
                                airport=ad
                                symbolicpos=ad['icao'].upper()
                                if i==0:
                                    dep_ad=ad['icao'].upper()
                                if i==len(waypoints)-1:
                                    dest_ad=ad['icao'].upper()
                                break
                    else:
                        for sigp in airspace.get_sigpoints(lat,lon,11):
                            if sigp['kind']=="sig. point":
                                if len(sigp['name'])==5:
                                    sigfound=sigp
                                    symbolicpos=sigp['name']
                                    break                
                    
                    if symbolicpos==None:
                        symbolicpos=mapper.format_lfv_ats(lat,lon)
                    wps.append(dict(
                        name=wp.waypoint,
                        airport=airport,
                        symbolicpos=symbolicpos,                
                        exactpos=mapper.format_lfv(lat,lon)
                        ))
                if dep_ad=="ZZZZ":
                    extra_remarks.append(u"DEP/%s %s"%(dep_ad_coords,strip_accents(dep_ad_name.upper())))
                if dest_ad=="ZZZZ":
                    extra_remarks.append(u"DEST/%s %s"%(dest_ad_coords,strip_accents(dest_ad_name.upper())))
                if stay.date_of_flight.strip():
                    dof=stay.date_of_flight.replace("-","").strip()
                    if len(dof)==8 and dof.startswith("20"):
                        dof=dof[2:]                        
                if len(dof)!=6:
                    raise AtsException(u"You need to enter the Date of Flight (DOF)!")
                else:                    
                    extra_remarks.append(u"DOF/%s"%(dof,))            
                if stay.departure_time:
                    try:
                        departure_time=parse_clock(stay.departure_time)
                    except:
                        AtsException(u"Departure time must be in format HH:MM (for instance, 10:30 for half-past ten, 23:00 for one hour before midnight!)")
                else:
                    departure_time=last_landing_time
                    if not departure_time:
                        raise AtsException(u"You need to enter a departure time! Remember to use UTC (Zulu-time)!")
                if stay and stay.nr_persons:
                    nr_persons=stay.nr_persons
                else:
                    if nr_persons==None:
                        raise AtsException(u"You must enter the the number of persons who will be flying!")
                tas=routes[0].tas
                altitude=routes[0].altitude
                at['wps']=wps
                enroute_time=sum(rt.time_hours for rt in routes)

                fuel=last_fuel_left
                if stay and stay.fuel:
                    fuel=stay.fuel
                    
                if c.ac.cruise_burn>1e-3 and fuel:
                    endurance=float(fuel)/float(c.ac.cruise_burn)
                else:
                    endurance=0.0
                
                if endurance<=0.0:
                    if fuel<1e-3:
                        raise AtsException("Enter a value for 'Fuel at takeoff'!")
                    else:
                        raise AtsException("You do not have enough fuel for the entire journey! Add a fuel stop, shorten the journey, or bring more fuel!")
                if not c.user.realname:
                    raise AtsException("You should enter your name under profile settings, for use as the name of the commander in the flight plan")
                phonenr=""
                if c.user.phonenr:            
                    phonenr=c.user.phonenr
                def format_cruise(tas):
                    if tas>999: tas=999
                    if tas<0: tas=0
                    return "N%04d"%(tas,)
                def format_alt(alt):
                    try:
                        alt=alt.upper().strip()
                        if alt.startswith("FL"):
                            ialt=int(float(alt[2:].strip()))
                            return "F%03d"%(ialt,)
                        ialt=int(float(alt))/100
                        return "A%03d"%(ialt,)
                    except:
                        raise AtsException("Bad altitude specification for some leg: <%s>"%(alt))
                dummy=u"""
    FPL-SEVLI-VG
    -ULAC/L-V/C
    -EFKG1330
    -N0075F065 DCT 5959N02016E DCT 5949N01936E DCT 5929N01818E DCT 5927N01742E
    -ZZZZ0130 
    -DEST/5927N01742E FRÖLUNDA RMK/BORDER CROSSING 40MIN AFTER TAKEOFF DOF/101002 ORGN/ESSAZPZX
    -E/0300 P/2
    A/R W
    C/ANDERS MUSIKKA +4670123123"""
            
                atsfplan=u"""
(FPL-%(acreg)s-%(flight_rules)s%(type_of_flight)s
-%(actype)s/%(turbulence_category)s-%(equipment)s/%(transponder)s
-%(dep_ad)s%(eobt)s
-%(cruise_speed)s%(level)s %(route)sDCT
-%(dest_ad)s%(ete)s 
-%(extra_remarks)s
-E/%(endurance)s P/%(nr_passengers)s
A/%(markings)s
C/%(commander)s %(phonenr)s)"""%(dict(
                acreg=c.ac.aircraft.replace("-",""),
                actype=c.ac.atstype,
                turbulence_category='L',
                flight_rules='V',
                type_of_flight='G',
                equipment='V',
                transponder='C',
                dep_ad=dep_ad,
                eobt=lfvclockfmt(departure_time),
                cruise_speed=format_cruise(tas),
                level=format_alt(altitude),
                route=("".join("DCT %s "%(w['symbolicpos'],) for w in wps[1:-1])),
                dest_ad=dest_ad,
                ete=lfvclockfmt(enroute_time),
                extra_remarks=" ".join(extra_remarks),
                endurance=lfvclockfmt(endurance),
                nr_passengers=nr_persons,
                markings=c.ac.markings,
                commander=strip_accents(c.user.realname.replace(" ",".") if c.user.realname else u"UNKNOWN"),
                phonenr=c.user.phonenr if c.user.phonenr else ""))
                at['atsfplan']=atsfplan.strip()
                print "Adding atstrip:",atsfplan    
                
                last_landing_time=routes[-1].clock_hours
                last_fuel_left=routes[-1].accum_fuel_burn
                c.atstrips.append(at)    
            
            c.atstrips=[at for at in c.atstrips if len(at['wps'])]
            #response.headers['Content-Type'] = 'application/xml'               
            return render('/ats.mako')
        except AtsException,ats:
            redirect_to(h.url_for(controller='flightplan',action="index",flash=unicode(ats)))


    def index(self):
        # Return a rendered template
        #return render('/flightplan.mako')
        # or, return a response
        trips=meta.Session.query(Trip).filter(sa.and_(Trip.user==tripuser(),
            Trip.trip==session['current_trip'])).all()
        if len(trips)!=1:
            return redirect_to(h.url_for(controller='mapview',action="index"))            
        c.flash=request.params.get('flash',None)
        trip,=trips
        c.waypoints=list(meta.Session.query(Waypoint).filter(sa.and_(
             Waypoint.user==tripuser(),Waypoint.trip==session['current_trip'])).order_by(Waypoint.ordering).all())
        
        if len(c.waypoints):        
            wp0=c.waypoints[0]
            if wp0.stay!=None:
                c.stay=wp0.stay
            else:
                print "No 'Stay', adding"
                c.stay=Stay(trip.user,trip.trip,wp0.id)
                meta.Session.add(c.stay)
                meta.Session.flush()
                meta.Session.commit()
        else:
            c.stay=None
                
        
        
        c.totdist=0.0
        for a,b in zip(c.waypoints[:-1],c.waypoints[1:]):     
            bear,dist=mapper.bearing_and_distance(a.pos,b.pos)
            c.totdist+=dist
        def get(what,a,b):
            #print "A:<%s>"%(what,),a.pos,b.pos
            if what in ['TT','D']:
                bear,dist=mapper.bearing_and_distance(a.pos,b.pos)
                #print "Bear,dist:",bear,dist
                if what=='TT':
                    return "%03.0f"%(bear,)
                elif what=='D':
                    return "%.1f"%(dist,)
            if what in ['W','V','Var','Alt','TAS','Dev']:
                routes=list(meta.Session.query(Route).filter(sa.and_(
                    Route.user==tripuser(),Route.trip==session['current_trip'],
                    Route.waypoint1==a.id,Route.waypoint2==b.id)).all())
                if len(routes)==1:
                    route=routes[0]
                    if what=='W':
                        return "%.0f"%(route.winddir+0.5)
                    elif what=='V':
                        return "%.0f"%(route.windvel+0.5)
                    elif what=='Var':
                        return "%.0f"%(route.variation) if route.variation!=None else ''
                    elif what=='Alt':
                        return route.altitude                    
                    elif what=='Dev':
                        #print "Dev is:",repr(route.deviation)
                        return "%.0f"%(route.deviation) if route.deviation!=None else ''   
                    elif what=='TAS':
                        if not route.tas:
                            return 75                        
                        return "%.0f"%(route.tas)
                return ""            
                
            return ""
        c.get=get
        c.tripname=session['current_trip']
         
        c.cols=[
                dict(width=3,short='W',desc="Wind Direction (deg)",extra=""),
                dict(width=2,short='V',desc="Wind Velocity (kt)",extra=""),
                #dict(width=3,short='Temp',desc="Outside Air Temperature (C)",extra=""),
                dict(width=5,short='Alt',desc="Altitude/Flight Level for leg",extra="(Altitude above mean sea level/flight level, e.g 4500ft or FL045, to be held on the leg between two waypoints.)"),
                dict(width=3,short='TAS',desc="True Air Speed (kt)",extra="(the speed of the aircraft in relation to the air around it)"),
                dict(width=3,short='TT',desc="True Track (deg)",extra="(the true direction the aircraft is flying, relative to ground)"),
                dict(width=3,short='WCA',desc="Wind correction angle (deg)",extra=" (the compensation due to wind needed to stay on the True Track. Negative means you have to aim left, positive to aim right)"),
                dict(width=2,short='Var',desc="Variation (deg)",extra="(How much to the right of the true north pole, the compass is pointing. Negative numbers means the compass points to the left of the true north pole)"),
                dict(width=2,short='Dev',desc="Deviation (deg)",extra="(How much to the right of the magnetic north, the aircraft compass will be pointing, while travelling in the direction of the true track)"),
                dict(width=3,short='CH',desc="Compass Heading (deg)",extra="(The heading that should be flown on the airplane compass to end up at the right place)"),
                dict(width=3,short='D',desc="Distance (NM)",extra=""),
                dict(width=3,short='GS',desc="Ground Speed (kt)",extra=""),
                dict(width=5,short='Time',desc="Time (hours, minutes)",extra=""),
                dict(width=5,short='Clock',desc="Time of Day (hours, minutes)",extra="The approximate time in UTC you will have finished the leg.")
                ]
       
        c.acname=trip.trip
        c.all_aircraft=meta.Session.query(Aircraft).filter(sa.and_(
                 Aircraft.user==session['user'])).all()

        if trip.acobj==None:
            c.ac=None
        else:        
            c.ac=trip.acobj
            
        c.sharing=tripsharing.sharing_active()
        return render('/flightplan.mako')
    def select_aircraft(self):
        if not tripsharing.sharing_active():  
            tripobj=meta.Session.query(Trip).filter(sa.and_(
                Trip.user==tripuser(),Trip.trip==session['current_trip'])).one()
            
            tripobj.aircraft=request.params['change_aircraft']
            if tripobj.aircraft.strip()=="--------":
                tripobj.aircraft=None
            else:
                for route in meta.Session.query(Route).filter(sa.and_(
                                Route.user==tripuser(),Route.trip==session['current_trip'])).order_by(Route.waypoint1).all():
                    acobj,=meta.Session.query(Aircraft).filter(sa.and_(
                        Aircraft.aircraft==tripobj.aircraft,Aircraft.user==session['user'])).all()
                    route.tas=acobj.cruise_speed
                
            meta.Session.flush()
            meta.Session.commit()
        
        
        redirect_to(h.url_for(controller='flightplan',action=request.params.get('prevaction','fuel')))

    def get_obstacles(self,routes,vertdist=1000.0,interval=10):        
        byid=dict()
        items=chain(notam_geo_search.get_notam_objs_cached()['obstacles'],
                    get_obstacles())
        for closeitem in chain(geo.get_stuff_near_route(routes,items,3.0,vertdist),
                        geo.get_terrain_near_route(routes,vertdist,interval=interval)):
            byid.setdefault(closeitem['id'],[]).append(closeitem)

        for v in byid.values():
            v.sort(key=lambda x:x['dist_from_a'])                        
        #print byid
        return byid
    
    def obstacles(self):    
        routes,dummy=get_route(tripuser(),session['current_trip'])
        
        tripobj=meta.Session.query(Trip).filter(sa.and_(
            Trip.user==tripuser(),Trip.trip==session['current_trip'])).one()
        c.trip=tripobj.trip
        byidsorted=sorted(self.get_obstacles(routes).items())
        out=[]
        def classify(item):
            print item
            vertlimit=1000
            if item.get('kind',None)=='terrain':
                vertlimit=500                
            try:
                margin=item['closestalt']-mapper.parse_elev(item['elev'])
            except:
                return "#0000ff" #Unknown margin, unknown height
            if item['dist']>0.6/1.852:
                return None #Not really too close anyway
            if margin<0:
                return "#ff3030"
            if margin<vertlimit:
                return "#ffb0b0"
            return None    
            
        dupecheck=dict()
        for idx,items in byidsorted:
            for item in items:
                ident=(item['name'],item['pos'],item.get('elev',None))
                dupecheck.setdefault(ident,[]).append(item)
        bestdupe=dict()
        for ident,dupes in dupecheck.items():
            best=min(dupes,key=lambda x:x['dist'])
            bestdupe[ident]=best
            
        for idx,items in byidsorted:
            cur=[]
            for item in items:
                along_nm=item['dist_from_a']
                fromwhat=item['a'].waypoint                
                ident=(item['name'],item['pos'],item.get('elev',None))
                best=bestdupe[ident]
                if not (best is item): continue
                #if ident in seen: continue
                #seen.add(ident)
                cur.append(dict(
                    along_nm=along_nm,
                    dir_from_a=item['dir_from_a'],
                    fromwhat=fromwhat,
                    kind=item.get('kind',None),
                    bearing=item.get('bearing',None),
                    dist=item['dist'],
                    name=item['name'],
                    closestalt=item['closestalt'],
                    elev=item.get('elev',None)))
                cur[-1]['color']=classify(cur[-1])
            out.append((items[0]['a'].waypoint,sorted(cur,key=lambda x:x['along_nm'])))
        
        c.items=out
        return render('/obstacles.mako')
        
        
    def standard_prep(self,c):
        c.techroute,c.route=get_route(tripuser(),session['current_trip'])
        #c.route=list(meta.Session.query(Route).filter(sa.and_(
        #    Route.user==tripuser(),Route.trip==session['current_trip'])).order_by(Route.waypoint1).all())
        c.user=meta.Session.query(User).filter(
                User.user==session['user']).one()

        c.all_aircraft=list(meta.Session.query(Aircraft).filter(sa.and_(
            Aircraft.user==session['user'])).order_by(Aircraft.aircraft).all())
        c.tripobj=meta.Session.query(Trip).filter(sa.and_(
            Trip.user==tripuser(),Trip.trip==session['current_trip'])).one()
        if len(c.route)==0 or len(c.techroute)==0:
            redirect_to(h.url_for(controller='flightplan',action="index",flash=u"Must have at least two waypoints in trip!"))
            return
        c.startfuel=0
        if len(c.route)>0:
            try:
                c.startfuel=c.route[0].a.stay.fuel
            except:
                pass
            if c.startfuel==None:
                c.startfuel=0
        #c.tripobj.startfuel
        c.acobjs=meta.Session.query(Aircraft).filter(sa.and_(
                 Aircraft.user==tripuser(),Aircraft.aircraft==c.tripobj.aircraft)).order_by(Aircraft.aircraft).all()
        c.ac=None
        if len(c.acobjs)>0:
            c.ac=c.acobjs[0]
        
        if c.ac and c.ac.cruise_burn>1e-9:
            c.reserve_endurance_hours=min(t.accum_fuel_burn for t in c.techroute)/c.ac.cruise_burn
            mins=int(60.0*c.reserve_endurance_hours)
            if mins>=0:
                c.reserve_endurance="%dh%02dm"%(mins/60,mins%60)
            else: 
                c.reserve_endurance="Unknown"
        else:
            c.reserve_endurance="Unknown"
        if len(c.route) and c.route[0].a.stay:
            c.departure_time=c.route[0].a.stay.departure_time
        else:
            c.departure_time=None
        c.departure=c.route[0].a.waypoint
        c.arrival=c.route[-1].b.waypoint        
    def printable(self):
        self.standard_prep(c)

        c.obsts=self.get_obstacles(c.techroute,1e6,2)
        for rt in c.route:
            rt.notampoints=set()
            rt.notampoints.update(set([info['item']['notam'] for info in get_notampoints_on_line(mapper.from_str(rt.a.pos),mapper.from_str(rt.b.pos),5)]))
        for rt in c.route:
            if rt.waypoint1 in c.obsts:
                rt.maxobstelev=max([obst['elevf'] for obst in c.obsts[rt.waypoint1]])
            else:
                rt.maxobstelev=0#"unknown"
            rt.startelev=get_terrain_elev.get_terrain_elev(mapper.from_str(rt.a.pos))
            rt.endelev=get_terrain_elev.get_terrain_elev(mapper.from_str(rt.b.pos))
            #for obst in c.obsts:
            #    print "obst:",obst
            for space in get_notam_areas_on_line(mapper.from_str(rt.a.pos),mapper.from_str(rt.b.pos)):
                rt.notampoints.add(space['name'])

        return render('/printable.mako')

    def enroutenotams(self):
        c.techroute,c.route=get_route(tripuser(),session['current_trip'])
        c.tripobj=meta.Session.query(Trip).filter(sa.and_(
            Trip.user==tripuser(),Trip.trip==session['current_trip'])).one()
        if len(c.route)==0 or len(c.techroute)==0:
            redirect_to(h.url_for(controller='flightplan',action="index",flash=u"Must have at least two waypoints in trip!"))
            return
        
        for rt in c.route:
            rt.notampoints=dict()
            rt.notampoints.update(dict([(info['item']['notam'],info['item']) for info in get_notampoints_on_line(mapper.from_str(rt.a.pos),mapper.from_str(rt.b.pos),5)]))

        for rt in c.route:
            for space in get_notam_areas_on_line(mapper.from_str(rt.a.pos),mapper.from_str(rt.b.pos)):
                rt.notampoints[space['name']]=space
        c.thislink=h.url_for(controller='flightplan',action="enroutenotams")
        return render('/enroutenotams.mako')

        
    def fuel(self):
        
        #routes=list(meta.Session.query(Route).filter(sa.and_(
        #    Route.user==tripuser(),Route.trip==session['current_trip'])).order_by(Route.waypoint1).all())
        #tripobj=meta.Session.query(Trip).filter(sa.and_(
        #    Trip.user==tripuser(),Trip.trip==session['current_trip'])).one()
        # 
        #c.trip=tripobj.trip
        #c.all_aircraft=list(meta.Session.query(Aircraft).filter(sa.and_(
        #    Aircraft.user==session['user'])).order_by(Aircraft.aircraft).all())
        #c.startfuel=0#tripobj.startfuel
        self.standard_prep(c)
        
        if c.tripobj.acobj==None:
            c.routes=[]
            c.acwarn=True
            c.ac=None
            c.endfuel=c.tripobj.startfuel
        else:        
            c.routes,dummy=get_route(tripuser(),session['current_trip'])
            c.acwarn=False
            c.ac=c.tripobj.acobj
            if len(c.routes)>0:
                c.endfuel=c.routes[-1].accum_fuel_burn
            else:
                c.endfuel=c.startfuel
        c.performance="ok"
        c.sharing=tripsharing.sharing_active()
        for rt in c.routes:
            if rt.performance!="ok":
                c.performance="notok"
        return render('/fuel.mako')
        
