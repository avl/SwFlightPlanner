#encoding=UTF8
import logging
import traceback
import time
from copy import copy
from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import redirect
from fplan.model import meta,User,Trip,Waypoint,Route,Aircraft,Stay 
from fplan.lib.base import BaseController, render
import sqlalchemy as sa
log = logging.getLogger(__name__)
import fplan.lib.mapper as mapper
import routes.util as h
from fplan.extract.extracted_cache import get_airfields,get_sig_points,get_obstacles
from fplan.lib.airspace import get_notam_areas_on_line,get_notampoints_on_line,get_any_space_on_line
import json
import re
import fplan.extract.gfs_weather as gfs_weather
from fplan.lib.calc_route_info import get_route
import fplan.lib.geo as geo
import fplan.lib.notam_geo_search as notam_geo_search
from itertools import chain
from fplan.lib import get_terrain_elev, calc_route_info
import fplan.lib.tripsharing as tripsharing
from fplan.lib.tripsharing import tripuser
import fplan.lib.airspace as airspace
from fplan.lib.helpers import lfvclockfmt,fmt_freq,timefmt,clockfmt
from fplan.lib.helpers import parse_clock
import fplan.lib.sunrise as sunrise
import unicodedata
import time
from datetime import timedelta,datetime
import fplan.lib.obstacle_free as obstacle_free

def strip_accents(s):
    if type(s)==str:
        s=unicode(s,'utf8',"ignore")
    def alnum(x):
        try:            
            if x[0] in ['-','/','.','_']:
                return " "
            cat=unicodedata.category(x)
            if cat[0] in ['L','N']:
                return x.upper()
            if cat[0]=='Z':
                return " "
            return ""
        except Exception:
            return "" 
    t=''.join((alnum(c) for c in unicodedata.normalize('NFKD', s))).encode('ASCII','ignore')
    ts=t.split()
    return " ".join(ts)

class AtsException(Exception): pass
import random

class FlightplanController(BaseController):
    def search(self):
        searchstr=request.params.get('search','')
        ordi=int(request.params.get('ordinal',0))
        #print "searching:",searchstr,ordi
        #time.sleep(1.5*f.random())
        latlon_match=re.match(r"(\d+)\.(\d+)([NS])(\d+)\.(\d+)([EW])",searchstr)
        if latlon_match:
            latdeg,latdec,ns,londeg,londec,ew=latlon_match.groups()
            lat=float(latdeg)+float("0."+latdec)
            lon=float(londeg)+float("0."+londec)
            if ns in ['S','s']:
                lat=-lat
            if ew in ['W','w']:
                lon=-lon
            return json.dumps(dict(ordinal=ordi,hits=[['Unknown Waypoint',[lat,lon],'Unknown Waypoint']]))                

        dec_match=re.match(r"\s*(\d+\.\d+)\s*,\s*(\d+\.\d+)\s*",searchstr)
        if dec_match:
            latdec,londec=dec_match.groups()
            lat=float(latdec)
            lon=float(londec)
            return json.dumps(dict(ordinal=ordi,hits=[['Unknown Waypoint',[lat,lon],'Unknown Waypoint']]))                

        #print "Searching for ",searchstr
        searchstr=strip_accents(searchstr).lower()
        apoints=[]
        for airp in get_airfields():
            if strip_accents(airp['name']).lower().count(searchstr) or \
                airp['icao'].lower().count(searchstr):
                d=dict(airp)
                d['kind']='airport'
                apoints.append(d)  
        spoints=[]        
        for sigpoint in get_sig_points():
            if strip_accents(sigpoint['name']).lower().count(searchstr):
                spoints.append(sigpoint)
        def namekey(x):
            return x['name']
        points=list(sorted(apoints,key=namekey))
        points.extend(sorted(spoints,key=namekey))
        if len(points)==0:
            return ""
        #points.sort(key=lambda x:x['name'])
        def extract_name(x):
            if 'kind' in x:
                return "%s (%s)"%(x['name'],x['kind'])
            return x.get('name','unknown item')
        
        hits=[[extract_name(x),mapper.from_str(x['pos']),x.get('name','unknown item')] for x in points[:15]]
        ret=json.dumps(dict(ordinal=ordi,hits=hits))
        #print "returning json:",ret
        return ret
    
    def validate(self,exception=True,tripname=None):
        try:
            if tripname==None:
                tripname=session['current_trip']
            c.trip=meta.Session.query(Trip).filter(sa.and_(Trip.user==tripuser(),
                Trip.trip==tripname)).one()
            c.userobj=meta.Session.query(User).filter(User.user==session['user']).one()
        except Exception,cause:
            log.warning("Access flightplan without session or trip: %s"%(cause,))
            if not exception:
                return False
            else:
                raise
        return True
            
    def save(self):
        #print "Saving tripname:",request.params
        if not self.validate(exception=False,tripname=request.params.get('tripname',False)):
            return ""
        try:
            waypoints=meta.Session.query(Waypoint).filter(sa.and_(
                 Waypoint.user==tripuser(),
                 Waypoint.trip==c.trip.trip)).order_by(Waypoint.ordering).all()
            #print "REquest:",request.params
            c.userobj.realname=request.params.get('realname',c.userobj.realname)
                                
            for idx,way in enumerate(waypoints):
                dof_s="date_of_flight_%d"%(way.id,)
                dep_s="departure_time_%d"%(way.id,)
                fuel_s="fuel_%d"%(way.id,)
                persons_s="persons_%d"%(way.id,)
                
                name_s="name%d"%(way.id,)
                way.waypoint=request.params.get(name_s,way.waypoint)
                
                if dof_s in request.params:
                    #possibly add new stay
                    if not way.stay:
                        #print "Adding stay: ord/id",way.ordering,way.id
                        way.stay=Stay(tripuser(),c.trip.trip,way.id)
                    if re.match(ur"\d{4}-?\d{2}\-?\d{2}",request.params.get(dof_s,'')):
                        way.stay.date_of_flight=request.params.get(dof_s,'')
                    else:
                        way.stay.date_of_flight=''
                        
                    if re.match(ur"\d{2}:?\d{2}",request.params.get(dep_s,'')):
                        way.stay.departure_time=request.params.get(dep_s,'')
                    else:
                        way.stay.departure_time=''
                        
                    try:
                        way.stay.nr_persons=int(request.params[persons_s])
                    except Exception:
                        way.stay.nr_persons=None
                    way.stay.fuel=None
                    way.stay.fueladjust=None
                    try:
                        fuelstr=request.params.get(fuel_s,'').strip()
                        if fuelstr.startswith("+") or fuelstr.startswith("-"):
                            way.stay.fueladjust=float(fuelstr)
                        else:
                            way.stay.fuel=float(fuelstr)
                    except Exception:
                        pass                
                    way.altitude=unicode(int(get_terrain_elev.get_terrain_elev(mapper.from_str(way.pos))))
                else:
                    #remove any stay
                    meta.Session.query(Stay).filter(sa.and_(
                        Stay.user==way.user,Stay.trip==way.trip,Stay.waypoint_id==way.id)).delete()
                    way.altitude=u''
    
            for idx,way in enumerate(waypoints[:-1]):
                #print "Found waypoint #%d"%(idx,)    
                route=meta.Session.query(Route).filter(sa.and_(
                    Route.user==tripuser(),
                    Route.trip==c.trip.trip,
                    Route.waypoint1==way.id,
                    )).one()
                for col,att in [
                    ('W','winddir'),
                    ('V','windvel'),
                    ('TAS','tas'),
                    ('Alt','altitude'),
                    ('Dev','deviation')
                    ]:
                                                                    
                    key="%s_%d"%(col,way.id)
                    if col=='TAS' and not key in request.params:
                        #TAS is not present if ac.advanced_model==false
                        continue                
                    val=request.params[key]
                    #print "Value of key %s: %s"%(key,val)
                    if col=="Alt":
                        setattr(route,att,val[0:6])
                    else:
                        try:
                            setattr(route,att,int(val))
                        except Exception:
                            setattr(route,att,0)
                    #print "Setting attrib '%s' of object %s to '%s'"%(att,route,val)
            
            if not tripsharing.sharing_active():
                acname=request.params.get('aircraft','').strip()
                if acname!="":
                    c.trip.aircraft=acname
                  
                
                
            meta.Session.flush()
            meta.Session.commit()
        except Exception,cause:
            log.error("Save flightplan failed! %s"%(cause,))
            return ''
        
        return self.get_json_routeinfo(get_route(tripuser(),c.trip.trip)[1])
    
    def optimize(self):
        if not self.validate(exception=False,tripname=request.params.get('tripname',False)):
            return ""
        
        #for rt in c.route:
        #    rt.maxobstelev=get_obstacle_free_height_on_line(
        ##            mapper.from_str(rt.a.pos),mapper.from_str(rt.b.pos))
        # #   print "Max obst elev",rt.maxobstelev
        strat=request.params.get('strategy','time')
        print "Strategy",strat
        resultcode,routes=calc_route_info.get_optimized(tripuser(),c.trip.trip,
                            strat)
        if resultcode==False:
            return ""
        out=[]
        for rt in routes:
            out.append([rt.winddir,rt.windvel,rt.altitude])
        s=json.dumps(out)
        print "Optimized output",s
        return s
            
    def get_json_routeinfo(self,routes):
        out=dict()
        rows=[]
        
        for rt in routes:
            d=dict()
            d['id']=rt.a.id
            d['wca']=rt.wca
            d['ch']="%03.0f"%(rt.ch,) if rt.ch else None
            d['gs']="%.1f"%(rt.gs,) if rt.gs>0 else None
            d['tas']="%.1f"%(rt.tas,) if rt.tas>0 else None
            d['timestr']=timefmt(rt.time_hours) if rt.time_hours else "--"            
            d['clockstr']=rt.arrive_dt.strftime("%H:%M") if rt.arrive_dt else "--:--"
            rows.append(d)
        if len(routes)>0:
            out['tottime']=timefmt(routes[-1].accum_time_hours) if routes[-1].accum_time_hours else "--"
            out['totfuel']="%.1f"%(routes[-1].accum_fuel_used,) if routes[-1].accum_fuel_used else "--"
        else:
            out['tottime']='-'
            out['totfuel']='-'
        out['rows']=rows
        return json.dumps(out)
        
    def weather(self):
        dummy,routes=get_route(tripuser(),request.params['tripname'])

        ret=[]
        alts=request.params.get('alts','')
        if alts==None:
            altvec=[]
        else:
            altvec=alts.split(",")
        for route,altitude in zip(routes,altvec):
             #print("Looking for waypoint: %s"%(way.pos,))
             try:
                mapper.parse_elev(altitude)
             except mapper.NotAnAltitude,cause:
                 ret.append(['',''])                 
                 continue #skip this alt
             #N+1 selects....
             merc1=mapper.latlon2merc(mapper.from_str(route.a.pos),14)
             merc2=mapper.latlon2merc(mapper.from_str(route.a.pos),14)
             center=(0.5*(merc1[0]+merc2[0]),0.5*(merc1[1]+merc2[1]))
             lat,lon=mapper.merc2latlon(center,14)
             #print "Fetching weather for %s,%s, %s"%(lat,lon,route.altitude)
             when=route.depart_dt+(route.arrive_dt-route.depart_dt)/2
             dummy1,dummy2,we=gfs_weather.get_prognosis(when)
             if we==None:
                 return ""; #Fail completely we don't have the weather here. We only succeed if we have weather for all parts of the journey.
             else:
                 try:
                     wi=we.get_wind(lat,lon,mapper.parse_elev(altitude))
                 except:
                     print traceback.format_exc()
                     return ""
                 #print "Got winds:",wi
                 ret.append([wi['direction'],wi['knots']])
        if len(ret)==0:
            return "" #Fail, no weather
        jsonstr=json.dumps(ret)
        #print "returning json:",jsonstr
        return jsonstr
        
    def excel(self):
        # Return a rendered template
        #return render('/flightplan.mako')
        # or, return a response
        if not self.validate(tripname=request.params.get('tripname',None),exception=False):
            return "Internal error. Missing trip-name or user-session."
        self.standard_prep(c)
        coding=request.params.get("encoding",'UTF8')
        allowed=set(["UTF16",'ISO8859-15','ISO8859-1','UTF8'])
        if not coding in allowed:
            coding='UTF8'
            
        c.waypoints=c.route
        response.content_type = 'application/octet-stream'               
        response.charset=coding
        def fixup(val):
            if type(val)==float:
                return str(val).replace(".",",")
            return val
        c.fixup=fixup
        return render('/excel.mako')
        
        

    def gpx(self):
        # Return a rendered template
        #return render('/flightplan.mako')
        # or, return a response
        if not self.validate(tripname=request.params.get('tripname',None),exception=False):
            return "Internal error. Missing trip-name or user-session."
                    
        waypoints=list(meta.Session.query(Waypoint).filter(sa.and_(
             Waypoint.user==tripuser(),Waypoint.trip==c.trip.trip)).order_by(Waypoint.ordering).all())
        if len(waypoints)==0:
            return redirect(h.url_for(controller='flightplan',action="index",flash=u"Must have at least two waypoints in trip!"))
        c.waypoints=[]
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
            #print "Routes:",c.route
            
            def break_subtrips(routes):
                out=[]
                T=0.0
                for i,rt in enumerate(routes):
                    out.append(rt)
                    if rt.time_hours:
                        T+=rt.time_hours
                    if rt.b.stay or i==len(routes)-1:
                        if len(out):
                            yield dict(T=T),out
                        T=0.0
                        out=[]                
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
                    print "parsed alt %s"%(repr(alt,)),"as",ialt
                    return "A%03d"%(ialt,)
                except Exception:
                    raise AtsException("Bad altitude specification for some leg: <%s>"%(alt))
                        
                        
            c.atstrips=[]
            last_fuel_left=None
            nr_persons=None
            for meta,routes in break_subtrips(c.route):
                print "===============New subtrip..............."
                spaces=set()                
                fir_whenposname=[]
                accum_time=0
                #print "broke ruote",meta
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
                lastwppos=None
                lastaltspeed=None
                for i,wp in enumerate(waypoints):
                    print "Subtrip:",i,wp.waypoint
                    at['T']=meta['T']
                    lat,lon=mapper.from_str(wp.pos)
                    if lastwppos:
                        assert i>=1
                        curpos=(lat,lon)
                        crossing1=airspace.get_fir_crossing(lastwppos,curpos)                        
                        for sub in routes[i-1].subs:
                            if crossing1:
                                posa,posb=mapper.merc2latlon(sub.subposa,13),\
                                            mapper.merc2latlon(sub.subposb,13)
                                crossing=airspace.get_fir_crossing(posa,posb)
                                if crossing:
                                    fir,enterpos=crossing
                                    bearing,along=mapper.bearing_and_distance(posa,enterpos)
                                    if sub.gs>1e-6:
                                        curtime=accum_time+along/sub.gs
                                        fir_whenposname.append((curtime,enterpos,fir['icao']))
                            if sub.time!=None:
                                accum_time+=sub.time
                            else:
                                accum_time=9999
                            
                        for space in get_any_space_on_line(lastwppos,curpos):
                            spaces.add((space['name'],space.get('floor',"<Unknown>"),space.get('ceiling',"<Unknown>")))
                    
                    lastwppos=(lat,lon)         
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
                        
                    if i<len(routes):
                        altspeed=(format_alt(routes[i].altitude),format_cruise(routes[i].tas))
                        if lastaltspeed!=None:
                            if lastaltspeed!=altspeed:
                                alt,speed=altspeed
                                symbolicpos+="/"+speed+alt
                        lastaltspeed=altspeed
                        
                    wps.append(dict(
                        name=wp.waypoint,
                        airport=airport,
                        symbolicpos="DCT "+symbolicpos,                
                        exactpos=mapper.format_lfv(lat,lon),
                        decimalpos="%.5f,%.5f"%(lat,lon)
                        ))
                for when,pos,fir in fir_whenposname:
                    hour,minute=divmod(int(60*when),60)
                    extra_remarks.append("EET/%s%02d%02d"%(fir,hour,minute))
                if dep_ad=="ZZZZ":
                    extra_remarks.append(u"DEP/%s %s"%(dep_ad_coords,strip_accents(dep_ad_name.upper())))
                if dest_ad=="ZZZZ":
                    extra_remarks.append(u"DEST/%s %s"%(dest_ad_coords,strip_accents(dest_ad_name.upper())))
                if stay.date_of_flight.strip():
                    dof=stay.date_of_flight.replace("-","").strip()
                    if len(dof)==8 and dof.startswith("20"):
                        dof=dof[2:]
                else:
                    dof=routes[0].depart_dt.strftime("%y%m%d")
                print "dof:",dof
                                        
                if len(dof)!=6:
                    raise AtsException(u"ATS flight plans need takeoff date for all takeoffs!")
                else:                    
                    extra_remarks.append(u"DOF/%s"%(dof,))            
                if stay and stay.nr_persons:
                    nr_persons=stay.nr_persons
                else:
                    if nr_persons==None:
                        raise AtsException(u"You must enter the the number of persons who will be flying!")
                tas=routes[0].tas
                altitude=routes[0].altitude
                at['wps']=wps
                if any(rt.time_hours==None for rt in routes):
                    raise AtsException("TAS is less than headwind for some part of trip.")
                enroute_time=sum(rt.time_hours for rt in routes)

                fuel=last_fuel_left
                if stay and stay.fuel:
                    fuel=stay.fuel
                    
                if not c.ac:
                    raise AtsException("You must choose an aircraft type for this journey to be able to create an ATS flight plan")
                if c.ac.cruise_burn>1e-3 and fuel:
                    endurance=float(fuel)/float(c.ac.cruise_burn)
                else:
                    endurance=0.0
                
                if endurance<=0.0:
                    if fuel==None:
                        raise AtsException("Enter a value for 'Fuel at takeoff'!")
                    else:
                        raise AtsException("You do not have enough fuel for the entire journey! This means your endurance would be 0 or negative for one or more legs. Add a fuel stop, shorten the journey, or bring more fuel!")
                        
                if not c.user.realname:
                    raise AtsException("You should enter your name under profile settings, for use as the name of the commander in the flight plan")
                phonenr=""
                if c.user.phonenr:            
                    phonenr=c.user.phonenr
                fir_whenposname.sort()
                def eqp(x,s):
                    x="".join(re.findall('[A-Z]',x.upper()))
                    if len(x)==0:
                        return s
                    return x
                    
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
-%(cruise_speed)s%(level)s %(route)s DCT
-%(dest_ad)s%(ete)s 
-%(extra_remarks)s
-E/%(endurance)s P/%(nr_passengers)s
A/%(markings)s%(extra_equipment)s
C/%(commander)s %(phonenr)s)"""%(dict(
                acreg=c.ac.aircraft.replace("-",""),
                actype=c.ac.atstype,
                turbulence_category='L',
                flight_rules='V',
                type_of_flight='G',
                equipment=eqp(c.ac.com_nav_equipment,'V'),
                transponder=eqp(c.ac.transponder_equipment,'C'),
                extra_equipment=u" %s"%(c.ac.extra_equipment,) if c.ac.extra_equipment else "",
                dep_ad=dep_ad,
                eobt=routes[0].depart_dt.strftime("%H%M"),
                cruise_speed=format_cruise(tas),
                level=format_alt(altitude),
                route=(" ".join("%s"%(w['symbolicpos'],) for w in wps[1:-1])),
                dest_ad=dest_ad,
                ete=lfvclockfmt(enroute_time),
                extra_remarks=" ".join(extra_remarks),
                endurance=lfvclockfmt(endurance),
                nr_passengers=nr_persons,
                markings=c.ac.markings,
                commander=strip_accents(c.user.realname if c.user.realname else u"UNKNOWN").replace(" ",""),
                phonenr=c.user.phonenr if c.user.phonenr else ""))
                at['atsfplan']=atsfplan.strip()
                #print "Adding atstrip:",atsfplan    
                at['spacesummary']=spaces
                last_fuel_left=routes[-1].accum_fuel_left
                c.atstrips.append(at)    
            
            c.atstrips=[at for at in c.atstrips if len(at['wps'])]
            #response.headers['Content-Type'] = 'application/xml'               
            return render('/ats.mako')
        except AtsException,ats:
            redirect(h.url_for(controller='flightplan',action="index",flash=unicode(ats)))


    def index(self):
        if not self.validate(exception=False):
            redirect(h.url_for(controller='mapview',action="index"))
        
        c.flash=request.params.get('flash',None)
        c.waypoints=list(meta.Session.query(Waypoint).filter(sa.and_(
             Waypoint.user==tripuser(),Waypoint.trip==c.trip.trip)).order_by(Waypoint.ordering).all())
        
        if len(c.waypoints):        
            wp0=c.waypoints[0]
            if wp0.stay!=None:
                c.stay=wp0.stay
            else:
                #print "No 'Stay', adding"
                c.stay=Stay(c.trip.user,c.trip.trip,wp0.id)
                meta.Session.add(c.stay)
                meta.Session.flush()
                meta.Session.commit()
        else:
            c.stay=None
                
        c.realname=c.userobj.realname
        
        dummy,routes=get_route(tripuser(),c.trip.trip)
        c.derived_data=self.get_json_routeinfo(routes)
         
        c.totdist=0.0
        if len(routes)>0:
            c.totdist=routes[-1].accum_dist
        
        wp2route=dict()
        for rt in routes:
            wp2route[(rt.waypoint1,rt.waypoint2)]=rt
        def get(what,a,b):
            #print "A:<%s>"%(what,),a.pos,b.pos
            route=wp2route.get((a.id,b.id),None)
            
            if route:                
                if what in ['TT','D','Var']:
                    bear,dist=route.tt,route.d #mapper.bearing_and_distance(a.pos,b.pos)
                    #print "Bear,dist:",bear,dist
                    if what=='TT':
                        return "%03.0f"%(bear,)
                    elif what=='D':
                        return "%.1f"%(dist,)
                    elif what=='Var':
                        var=route.variation
                        return "%+.0f"%(round(var),)
                if what in ['W','V','Alt','TAS','Dev']:
                    #routes=list(meta.Session.query(Route).filter(sa.and_(
                    #    Route.user==tripuser(),Route.trip==session['current_trip'],
                    #    Route.waypoint1==a.id,Route.waypoint2==b.id)).all())
                    if what=='W':
                        return "%03.0f"%(route.winddir)
                    elif what=='V':
                        return "%.0f"%(route.windvel)
                    elif what=='Alt':
                        try:
                            #print "Parsing elev:",route.altitude
                            mapper.parse_elev(route.altitude)
                        except Exception,cause:
                            #print "couldn't parse elev:",route.altitude
                            return "1500"
                        return route.altitude                    
                    elif what=='Dev':
                        #print "Dev is:",repr(route.deviation)
                        return "%.0f"%(route.deviation) if route.deviation!=None else ''   
                    elif what=='TAS':
                        #print "A:<%s>"%(what,),a.id,b.id,route.tas,id(route)
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
                dict(width=2,short='Var',desc="Variation (deg)",extra="(How much to the right of the true north pole, the compass is pointing. Negative numbers means the compass points to the left of the true north)"),
                dict(width=2,short='Dev',desc="Deviation (deg)",extra="(How much to the right of the magnetic north, the aircraft compass will be pointing, while travelling in the direction of the true track)"),
                dict(width=3,short='CH',desc="Compass Heading (deg)",extra="(The heading that should be flown on the airplane compass to end up at the right place)"),
                dict(width=3,short='D',desc="Distance (NM)",extra=""),
                dict(width=3,short='GS',desc="Ground Speed (kt)",extra="(Average on leg, taking into account different speeds during climb and descent)"),
                dict(width=5,short='Time',desc="Time (hours, minutes)",extra=""),
                ]
       
        c.all_aircraft=meta.Session.query(Aircraft).filter(sa.and_(
                 Aircraft.user==session['user'])).all()

        if c.trip.acobj==None:
            c.ac=None
            c.advanced_model=False
        else:        
            c.ac=c.trip.acobj
            if session.get('cur_aircraft',None)!=c.trip.acobj.aircraft:
                session['cur_aircraft']=c.trip.acobj.aircraft
                session.save()
            c.advanced_model=c.ac.advanced_model
        c.sharing=tripsharing.sharing_active()
        #print repr(c)
        return render('/flightplan.mako')
    def select_aircraft(self):
        if not self.validate(exception=False):
            redirect(h.url_for(controller='mapview',action="index"))
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
        
        
        redirect(h.url_for(controller='flightplan',action=request.params.get('prevaction','fuel')))

    def minutemarkings(self):
        self.standard_prep(c)
        scale=250000
        def total_seconds(td):
            return float(td.seconds)+td.days*86400.0+td.microseconds/1e6
        for r in c.route:
            try:
                subs=r.subs
                def get_d_at_time(dt):
                    for sub in subs:
                        if dt<=sub.arrive_dt:
                            sub_time=dt-sub.depart_dt
                            sub_seconds=total_seconds(sub_time)
                            sub_hours=sub_seconds/3600.0
                            return sub.relstartd+sub_hours*sub.gs
                    return r.d
                        
                curdt=copy(r.depart_dt)
                curdt=curdt.replace(second=60*(curdt.second//60),microsecond=0)
                if curdt<r.depart_dt:
                    curdt+=timedelta(0,60)
                    
                                    
                #gs_ms=(r.gs*1.8520)/3.6
                #if gs_ms<1e-3: return "-"
                #meter_per_min=gs_ms*60.0
                #map_meter_per_min=meter_per_min/scale
                #cm_per_min=100*map_meter_per_min
                    #d=get_d_at_time(curdt)
                    #get_
                    #marks.append("%.1f"%cur)
                    #cur+=cm_per_min                                    
                marks=[]
                while curdt<r.arrive_dt:
                    d=get_d_at_time(curdt)
                    meter=d*1852.0
                    cm=meter*100.0
                    mapcm=cm/scale
                    marks.append("%.1f"%mapcm)
                    curdt+=timedelta(0,60)
                r.marks=", ".join(marks)+" cm"
            except Exception:
                r.marks="-"
            
        return render("/minutemarkings.mako")
        
    def get_obstacles(self,routes,vertdist=1000.0,interval=10):        
        byid=dict()
        items=chain(notam_geo_search.get_notam_objs_cached()['obstacles'],
                    get_obstacles())
        print "Get terrain"
        for closeitem in chain(geo.get_stuff_near_route(routes,items,3.0,vertdist),
                        geo.get_terrain_near_route(routes,vertdist,interval=interval),
                        geo.get_low_sun_near_route(routes)
                        ):
            byid.setdefault(closeitem['id'],[]).append(closeitem)

        for v in byid.values():
            v.sort(key=lambda x:x['dist_from_a'])                        
        #print byid
        return byid
    
    def obstacles(self):    
        routes,baseroute=get_route(tripuser(),session['current_trip'])
        
        tripobj=meta.Session.query(Trip).filter(sa.and_(
            Trip.user==tripuser(),Trip.trip==session['current_trip'])).one()
        c.trip=tripobj.trip
        id2order=dict([(rt.a.id,rt.a.ordering) for rt in baseroute])
        byidsorted=sorted(self.get_obstacles(routes).items(),key=lambda x:id2order.get(x[0],0))
        out=[]
        def classify(item):
            #print item
            vertlimit=1000
            if item.get('kind',None)=='lowsun':
                return "#ffffb0"            
            if item.get('kind',None)=='terrain':
                vertlimit=500                
            try:
                margin=item['closestalt']-mapper.parse_elev(item['elev'])
            except Exception:
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
                dist_from_a=item['dist_from_a']
                dist_from_b=item['dist_from_b']

                if abs(dist_from_a)<0.5:
                    descr="Near %s"%(item['a'].waypoint,)
                elif abs(dist_from_b)<0.5:
                    descr="Near %s"%(item['b'].waypoint,)
                elif dist_from_a<dist_from_b:
                    descr="%.0fNM %s of %s"%(dist_from_a,item['dir_from_a'],item['a'].waypoint)
                else:
                    descr="%.0fNM %s of %s"%(dist_from_b,item['dir_from_b'],item['b'].waypoint)
                
                    
                ident=(item['name'],item['pos'],item.get('elev',None))
                best=bestdupe[ident]
                if not (best is item): continue
                
                
                #if ident in seen: continue
                #seen.add(ident)
                cur.append(dict(
                    routepointdescr=descr,
                    #dir_from_a=item['dir_from_a'],
                    #fromwhat=fromwhat,
                    kind=item.get('kind',None),
                    bearing=item.get('bearing',None),
                    along_nm=dist_from_a,                    
                    dist=item['dist'],
                    name=item['name'],
                    closestalt=item['closestalt'],
                    elev=item.get('elev',None)))
                cur[-1]['color']=classify(cur[-1])
            out.append((items[0]['a'].waypoint,sorted(cur,key=lambda x:x['along_nm'])))

        
        c.items=out
        return render('/obstacles.mako')
        
        
    def standard_prep(self,c):
        if not 'current_trip' in session:
            redirect(h.url_for(controller='mapview',action="index"))
        tripobjs=meta.Session.query(Trip).filter(sa.and_(
            Trip.user==tripuser(),Trip.trip==session['current_trip'])).all()
        if len(tripobjs)!=1:
            redirect(h.url_for(controller='mapview',action="index"))
        c.tripobj,=tripobjs
        c.trip=c.tripobj.trip
        c.techroute,c.route=get_route(tripuser(),session['current_trip'])
        #c.route=list(meta.Session.query(Route).filter(sa.and_(
        #    Route.user==tripuser(),Route.trip==session['current_trip'])).order_by(Route.waypoint1).all())
        c.user=meta.Session.query(User).filter(
                User.user==session['user']).one()

        c.all_aircraft=list(meta.Session.query(Aircraft).filter(sa.and_(
            Aircraft.user==session['user'])).order_by(Aircraft.aircraft).all())
        
            
        if len(c.route)==0 or len(c.techroute)==0:
            redirect(h.url_for(controller='flightplan',action="index",flash=u"Must have at least two waypoints in trip!"))
            return
        c.startfuel=0
        if len(c.route)>0:
            try:
                c.startfuel=c.route[0].a.stay.fuel
            except Exception:
                pass
            if c.startfuel==None:
                c.startfuel=0
        #c.tripobj.startfuel
        c.acobjs=meta.Session.query(Aircraft).filter(sa.and_(
                 Aircraft.user==tripuser(),Aircraft.aircraft==c.tripobj.aircraft)).order_by(Aircraft.aircraft).all()
        c.ac=None
        if len(c.acobjs)>0:
            c.ac=c.acobjs[0]
        
        c.reserve_endurance="Unknown"
        if c.ac and c.ac.cruise_burn>1e-9 and len(c.techroute):
            minfuelintrip=min(t.accum_fuel_left for t in c.techroute)
            if minfuelintrip!=None:
                c.reserve_endurance_hours=minfuelintrip/c.ac.cruise_burn
                mins=int(60.0*c.reserve_endurance_hours)
                if mins>=0:
                    c.reserve_endurance="%dh%02dm"%(mins/60,mins%60)
        c.departure=c.route[0].a.waypoint
        c.arrival=c.route[-1].b.waypoint
        c.fillable=c.user.fillable        

    def get_freqs(self,route):
        for rt in route:
            rt.freqset=dict()
            for air in airspace.get_airspaces_on_line(mapper.from_str(rt.a.pos),mapper.from_str(rt.b.pos)):
                for freq in air['freqs']:
                    try:
                        currs=rt.freqset.setdefault(freq[0],[])
                        new=fmt_freq(freq[1])
                        if not new in currs:
                            currs.append(new)
                    except Exception,cause:
                        pass #print "Couldn't add freq %s: %s"%(freq,cause)
                #print "Airspace:",air
            #print "Inspecting leg",rt
    def printable(self):
        extended=False
        if request.params.get('extended',False):
            extended=True
        self.standard_prep(c)
        self.get_freqs(c.route)
        if extended:
            c.origroute=c.route
            c.route=c.techroute
            for rt in c.origroute:
                for sub in rt.subs:
                    sub.freqset=rt.freqset
                    sub.is_start=False
                    sub.is_end=False
                rt.subs[-1].is_end=True
                rt.subs[0].is_start=True
        else:
            for rt in c.route:
                rt.is_end=True
                rt.is_start=True
                rt.what=''
        
        for rt in c.route:
            rt.notampoints=set()
            rt.notampoints.update(set([info['item']['notam'] for info in get_notampoints_on_line(mapper.from_str(rt.a.pos),mapper.from_str(rt.b.pos),5)]))
        for rt in c.route:
            rt.maxobstelev=obstacle_free.get_obstacle_free_height_on_line(
                    mapper.from_str(rt.a.pos),
                    mapper.from_str(rt.b.pos))
            try:
                rt.startelev=float(airspace.get_pos_elev(mapper.from_str(rt.a.pos)))
            except:
                rt.startelev=float(9999)
            try:
                rt.endelev=float(airspace.get_pos_elev(mapper.from_str(rt.b.pos)))
            except:
                rt.endelev=float(9999)
            #for obst in obsts:
            #    print "obst:",obst
            for space in get_notam_areas_on_line(mapper.from_str(rt.a.pos),mapper.from_str(rt.b.pos)):
                rt.notampoints.add(space['name'])
        
        if len(c.route)>0:
            poss=[mapper.from_str(c.route[0].a.pos)]
            poss+=[mapper.from_str(r.b.pos) for r in c.route]
            dta,dtb=[c.route[0].a.dt,c.route[-1].b.dt]
            
            if dtb==None:
                c.sunset="unknown"
            else:
                print "sunrise:",dta,dtb
                fall,what=sunrise.earliestsunset([dta,dtb],poss)
                if what!=None:
                    c.sunset=what
                elif fall!=None:
                    c.sunset=fall.strftime("%H:%MZ")
                else:
                    c.sunset="unknown"
            lat,lon=mapper.from_str(c.route[0].a.pos)
            c.sunrise=sunrise.sunrise_str(dta,lat,lon)
        return render('/printable.mako')

    def enroutenotams(self):
        c.techroute,c.route=get_route(tripuser(),session['current_trip'])
        c.tripobj=meta.Session.query(Trip).filter(sa.and_(
            Trip.user==tripuser(),Trip.trip==session['current_trip'])).one()
        if len(c.route)==0 or len(c.techroute)==0:
            redirect(h.url_for(controller='flightplan',action="index",flash=u"Must have at least two waypoints in trip!"))
            return
        
        c.trip=c.tripobj.trip
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
            c.endfuel=0
        else:        
            c.routes=c.techroute
            c.acwarn=False
            c.ac=c.tripobj.acobj
            if len(c.routes)>0:
                c.endfuel=c.routes[-1].accum_fuel_left
            else:
                c.endfuel=0
        c.performance="ok"
        c.sharing=tripsharing.sharing_active()
        for rt in c.routes:
            if rt.performance!="ok":
                c.performance="notok"
        meta.Session.flush();
        meta.Session.commit()   
        return render('/fuel.mako')
        
