# coding=utf-8
import logging
import re
from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect
import fplan.lib.mapper as mapper
import fplan.lib.metartaf as metartaf
from fplan.model import meta
import fplan.lib.helpers as helpers
import fplan.extract.extracted_cache as extracted_cache
import StringIO
import math
import cairo
from fplan.lib.base import BaseController, render
from fplan.lib.tilegen_worker import generate_big_tile
from fplan.lib import maptilereader
from fplan.lib.airspace import get_firs,get_airspaces,get_obstacles,get_airfields,get_sigpoints,get_notam_areas,get_notampoints,get_aip_sup_areas
log = logging.getLogger(__name__)
from fplan.lib.parse_gpx import parse_gpx,get_stats
from fplan.lib.get_terrain_elev import get_terrain_elev
from pyshapemerge2d import Vector,Line,Vertex
from itertools import izip,chain
import routes.util as h
from datetime import datetime,timedelta
import fplan.lib.geomag as geomag


def format_freqs(freqitems):
    out=[]
    whodict=dict()
    print "Formatting:",freqitems
    for idx,freqitem in enumerate(freqitems):
        who,freq=freqitem
        #who=who.replace("CONTROL","CTL")
        whodict.setdefault(who,([],idx))[0].append(freq)
    for who,(freqs,idx) in sorted(whodict.items(),key=lambda x:x[1][1]):
        freqout=[]
        for freq in freqs:
            s="%.3f"%(freq,)
            if s.endswith("00"):
                s=s[:-2]
            freqout.append("<b>"+s+"</b>")
            
        out.append("%s - %s"%(who,
            " ".join(freqout)))
    
    return "".join(["<br/>&nbsp;&nbsp;%s"%(o,) for o in out])
def parse_elev_for_sort_purposes(elev):
    #print "elev",elev    
    elev=elev.lower()
    if elev=="gnd":
        return 0
    if elev.count("/"):
        elev,dummy=elev.split("/")
    if elev.endswith("gnd"):
        elev=elev[:-3]
        
    return mapper.parse_elev(elev)

def sort_airspace_key(space):
    floorelev=parse_elev_for_sort_purposes(space['floor'])    
    ceilingelev=parse_elev_for_sort_purposes(space['ceiling'])        
    return (-ceilingelev,floorelev,space['name'])

class MaptileController(BaseController):
    no_login_required=True #But we don't show personal data without login
    
    def get_airspace(self):
        utcnow=datetime.utcnow()
        try:
            zoomlevel=int(request.params['zoom'])
        except:
            zoomlevel=session.get('zoom',5)
        lat=float(request.params.get('lat'))
        lon=float(request.params.get('lon'))
        clickmerc=mapper.latlon2merc((lat,lon),zoomlevel)
        out=[]
        spaces=get_airspaces(lat,lon)
        print "Spaces:",spaces
        def anydate(s):
            if not 'date' in s: return ""
            d=s['date']
            age=utcnow-d            
            if age>timedelta(367):
                return "<span style=\"font-size:10px\">[%d]</span>"%(d.year,)
            if age>timedelta(2):                
                return "<span style=\"font-size:10px\">[%d%02d%02d]</span>"%(
                        d.year,d.month,d.day)
            return ""
        spaces=u"".join(u"<li><b>%s</b>%s: %s - %s%s</li>"%(space['name'],anydate(space),space['floor'],space['ceiling'],format_freqs(space['freqs'])) for space in sorted(
                spaces,key=sort_airspace_key))
        if spaces=="":
            spaces="No airspace found"
            
        mapviewurl=h.url_for(controller="mapview",action="index")

        
        notamlist=chain(get_notam_areas(lat,lon),get_notampoints(lat,lon,zoomlevel))
        notams=dict([(n['notam'].strip(),(n['notam_ordinal'],n['notam_line']) ) for n in notamlist])

        
        notamareas="".join("<li>%s <b><u><a href=\"javascript:navigate_to('%s#notam')\">Link</a></u></b></li>"%(
            text,h.url_for(controller="notam",action="show_ctx",backlink=mapviewurl,notam=notam,line=line)) for text,(notam,line) in notams.items())
        if notamareas!="":
            notamareas="<b>Area Notams:</b><ul>"+notamareas+"</ul>"

        aip_sup_strs="".join(["<li>%s <a href=\"%s\">link</a></li>"%(x['name'],x['url'].replace(" ","%20")) for x in get_aip_sup_areas(lat,lon)])
        if aip_sup_strs:
            aip_sup_strs="<b>AIP SUP:</b><ul>"+aip_sup_strs+"</ul>"
         
        obstbytype=dict()
        for obst in get_obstacles(lat,lon,zoomlevel):
            obstbytype.setdefault(obst['kind'],[]).append(obst)
            #print "processing",obst
        obstacles=[]
        if len(obstbytype):
            for kind,obsts in sorted(obstbytype.items()):
                obstacles.append("<b>"+kind+":</b>")
                obstacles.append(u"<ul>")
                for obst in obsts:
                    obstacles.append(u"<li><b>%s</b>: %s ft</li>"%(obst['name'],obst['elev'])) 
                obstacles.append(u"</ul>")

        tracks=[]
        if session.get('showtrack',None)!=None:                
            track=session.get('showtrack')
            #print "%d points"%(len(track.points))
            mindiff=1e30
            found=dict()
            hdg=0
            speed=0
            clickvec=Vertex(int(clickmerc[0]),int(clickmerc[1]))
            if len(track.points)>0 and len(track.points[0])==2:                
                pass #Old style track, not supported anymore
            else:
                for a,b in izip(track.points,track.points[1:]): 
                    merc=mapper.latlon2merc(a[0],zoomlevel)
                    nextmerc=mapper.latlon2merc(b[0],zoomlevel)
                    l=Line(Vertex(int(merc[0]),int(merc[1])),Vertex(int(nextmerc[0]),int(nextmerc[1])))
                    diff=l.approx_dist(clickvec)                

                    if diff<mindiff:
                        mindiff=diff
                        found=(a,b)

                if mindiff<10:
                    tracks.append(u"<b>GPS track:</b><ul><li>%(when)s - %(altitude)d ft hdg:%(heading)03d spd: %(speed)d kt</li></ul>"%(get_stats(*found)))
                                                  

        airports=[]
        fields=list(get_airfields(lat,lon,zoomlevel))
        if len(fields):
            airports.append("<b>Airfield:</b><ul>")
            for airp in fields:
                print "clicked on ",airp
                linksstr=""
                links=[]
                if 'flygkartan_id' in airp:
                    links.append(('http://www.flygkartan.se/0%s'%(airp['flygkartan_id'].strip(),),
                      'www.flygkartan.se'))
                if 'aiptexturl' in airp:
                    links.append((airp['aiptexturl'],
                      'AIP Text'))
                if 'aipvacurl' in airp:
                    links.append((airp['aipvacurl'],
                      'AIP Visual Approach Chart'))
                    
                if False and 'aipsup' in airp:
                    #Using AIP SUP for opening hours has stopped.
                    links.append((
                        extracted_cache.get_se_aip_sup_hours_url(),
                        "AIP SUP Opening Hours"))
                weather=""
                if airp.get('icao','ZZZZ').upper()!='ZZZZ':
                    icao=airp['icao']
                    metar=metartaf.get_metar(icao)
                    taf=metartaf.get_taf(icao)
                    weather="<table>"
                    
                    def colorize(item):
                        if item==None:
                            col="ffffff"
                            agestr=""
                        else:
                            age=metartaf.get_data_age(item)
                            if age==None:
                                col="ffffff"
                                agestr=""                                
                            elif age<timedelta(0,60*35):
                                col="c5c5c5"
                                agestr="%d minutes"%(int(age.seconds/60))
                            elif age<timedelta(0,60*60):
                                col="ffff30"
                                agestr="%d minutes"%(int(age.seconds/60))
                            else:
                                col="ff3030"
                                if age<timedelta(2):
                                    if age<timedelta(0,3600*1.5):
                                        agestr="%d minutes"%int(age.seconds/60)
                                    else:
                                        agestr="%d hours"%int(0.5+(age.seconds)/3600.0)
                                else:
                                    agestr="%d days"%(int(age.days))
                            
                        return "style=\"background:#"+col+"\" title=\""+agestr+" old.\""
                
                    if taf.text:
                        weather+="<tr valign=\"top\"><td>TAF:</td><td "+colorize(taf)+">"+taf.text+"</td></tr>"
                    if metar.text:
                        weather+="<tr valign=\"top\"><td>METAR:</td><td "+colorize(metar)+">"+metar.text+"</td></tr>"
                    weather+="</table>"
                    meta.Session.flush()
                    meta.Session.commit()
                    
                if len(links)>0:                    
                    linksstr=helpers.foldable_links(airp['icao']+"links",links)

                rwys=[]
                if 'runways' in airp:
                    for rwy in airp['runways']:
                        for end in rwy['ends']:
                            rwys.append(end['thr'])
                if len(rwys):                    
                    rwys=["<br/><b> Runways</b>: "]+rwys
                
                
                
                airports.append(u"<li><b>%s</b> - %s%s%s%s</li>"%(airp.get('icao','ZZZZ'),airp['name'],linksstr," ".join(rwys),weather))
            airports.append("</ul>")
        
        sigpoints=[]
        sigps=list(get_sigpoints(lat,lon,zoomlevel))
        if len(sigps):
            sigpoints.append("<b>Sig. points</b><ul>")
            for sigp in sigps:
                sigpoints.append(u"<li><b>%s</b>(%s)</li>"%(sigp['name'],sigp.get('kind','unknown point')))
            sigpoints.append("</ul>")
       

        firs=[]        
        for fir in get_firs((lat,lon)):
            firs.append("%s (%s)"%(fir['name'],fir['icao']))        
        if not firs:
            firs.append("Unknown")
            
        variation='?'
        terrelev=get_terrain_elev((lat,lon),zoomlevel)
        try:
            varf=geomag.calc_declination((lat,lon),utcnow,(terrelev+1000))
            variation=u"%+.1f°"%(varf,)
        except:
            pass
        return "<b>Airspace:</b><ul><li><b>FIR:</b> %s</li>%s</ul>%s%s%s%s%s%s<br/><b>Terrain: %s ft, Var: %s</b>"%(", ".join(firs),spaces,aip_sup_strs,"".join(obstacles),"".join(airports),"".join(tracks),"".join(sigpoints),notamareas,terrelev,variation)

    def get(self):
        # Return a rendered template
        #return render('/maptile.mako')
        # or, return a response
        my=int(request.params.get('mercy'))
        mx=int(request.params.get('mercx'))
        zoomlevel=int(request.params.get('zoom'))
        #print request.params
        #print "dynid: ",request.params.get('dynamic_id','None')
        if 'showairspaces' in request.params and request.params['showairspaces']:
            variant="airspace"
        else:
            variant="plain"
        variant=request.params.get('mapvariant',variant)
        

        neededit=False
        if session.get('showarea','')!='':
            neededit=True                
        if session.get('showtrack',None)!=None:
            neededit=True                
        
        mtime=request.params.get('mtime',None)
        generate_on_the_fly=False
        #print "get: %d,%d,%d (showair:%s, neededit: %s)"%(mx,my,zoomlevel,airspaces,neededit)
        
        if generate_on_the_fly:
            im=generate_big_tile((256,256),mx,my,zoomlevel,tma=True,return_format="cairo")    
            tilemeta=dict(status="ok")
        else:
            #print "Getting %s,%s,%s,%d,%d"%(mx,my,zoomlevel,mx%256,my%256)
            rawtile,tilemeta=maptilereader.gettile(variant,zoomlevel,mx,my,mtime)
            if not neededit:
                response.headers['Pragma'] = ''
                response.headers['Content-Type'] = 'image/png'
                if tilemeta['status']!="ok":
                    response.headers['Cache-Control'] = 'max-age=30'
                else:
                    response.headers['Cache-Control'] = 'max-age=3600'
                return rawtile
            io=StringIO.StringIO(rawtile)
            io.seek(0)
            im=cairo.ImageSurface.create_from_png(io)
            
        ctx=cairo.Context(im)
        
        
        if session.get('showarea','')!='':
            #print "Showarea rendering active",zoomlevel
            wp=[]
            #print session.get('showarea','')
            for vert in mapper.parse_lfv_area(session.get('showarea')):
                mercx,mercy=mapper.latlon2merc(mapper.from_str(vert),zoomlevel)
                wp.append((mercx-mx,mercy-my))       
            #print "wp:",wp
            if len(wp)>0:           
                ctx.new_path()
                ctx.set_line_width(2.0)
                if len(wp)==1:
                    w,=wp
                    ctx.arc(w[0],w[1],8,0,2*math.pi)
                    ctx.set_source(cairo.SolidPattern(0.0,0.0,1.0,0.25))
                    ctx.fill_preserve()
                    ctx.set_source(cairo.SolidPattern(0.0,0.0,1.0,1))
                    ctx.stroke()
                elif len(wp)==2:
                    ctx.set_source(cairo.SolidPattern(0.0,0.0,1.0,1))
                    ctx.new_path()
                    ctx.move_to(*wp[0])
                    ctx.line_to(*wp[1])
                    ctx.stroke()
                    ctx.arc(wp[0][0],wp[0][1],8,0,2*math.pi)
                    ctx.stroke()
                    ctx.new_path()
                    ctx.arc(wp[1][0],wp[1][1],8,0,2*math.pi)
                    ctx.stroke()                                        
                else:                    
                    for w in wp:                        
                        ctx.line_to(*w)
                    ctx.close_path()   
                    ctx.set_source(cairo.SolidPattern(0.0,0.0,1.0,0.25))             
                    ctx.fill_preserve()
                    ctx.set_source(cairo.SolidPattern(0.0,0.0,1.0,1))
                    ctx.stroke()
                    
                ctx.set_source(cairo.SolidPattern(0.0,0.0,0.0,1.0))                            
                for idx,w in enumerate(wp):
                    ctx.move_to(*w)
                    ctx.show_text("#%d"%(idx,))
                    
        if session.get('showtrack',None)!=None:                
            print "Showtrack rendering active"
            track=session.get('showtrack')
            ctx.new_path()
            ctx.set_line_width(2.0)
            ctx.set_source(cairo.SolidPattern(0.0,0.0,1.0,1))
            #lastmecc
            print "%d points"%(len(track.points))
            for p,height,dtim in track.points:
                merc=mapper.latlon2merc(p,zoomlevel)
                p=((merc[0]-mx,merc[1]-my))
                ctx.line_to(*p)
            ctx.stroke()                                        
                
            
    
        
        buf= StringIO.StringIO()
        im.write_to_png(buf)
        png=buf.getvalue()
        
        """
        im=Image.open(path)
        
        draw=ImageDraw.Draw(im)
        if session.get('showarea','')!='':                
            wp=[]
            print session.get('showarea','')
            for vert in mapper.parse_lfv_area(session.get('showarea')):
                mercx,mercy=mapper.latlon2merc(mapper.from_str(vert),zoomlevel)
                wp.append((mercx-mx,mercy-my))       
            print "wp:",wp
            if len(wp)>0:           
                if len(wp)==1:
                    draw.ellipse((wp[0][0]-5,wp[0][1]-5,wp[0][0]+5,wp[0][1]+5),fill="#ff0000")      
                elif len(wp)==2:
                    draw.line(wp,fill="#ff0000",)
                else:
                    draw.polygon(wp,fill="#ff0000",)
        
        
        buf= StringIO.StringIO()
        im.save(buf, format= 'PNG')
        png=buf.getvalue()
        """              
        
        #print "Corners:",get_map_corners(pixelsize=(width,height),center=pos,lolat=lower,hilat=upper)
        response.headers['Pragma'] = ''
        if tilemeta['status']!="ok":
            response.headers['Cache-Control'] = 'max-age=30'
        else:
            response.headers['Cache-Control'] = 'max-age=3600'
        response.headers['Content-Type'] = 'image/png'
        return png
        
