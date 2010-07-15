import logging
import re
from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
import fplan.lib.mapper as mapper
import StringIO
import math
import cairo
from fplan.lib.base import BaseController, render
from fplan.lib.tilegen_worker import generate_big_tile
from fplan.lib import maptilereader
from fplan.lib.airspace import get_airspaces,get_obstacles,get_airfields,get_sigpoints
log = logging.getLogger(__name__)
from fplan.lib.parse_gpx import parse_gpx
from fplan.lib.get_terrain_elev import get_terrain_elev

def format_freqs(freqitems):
    out=[]
    whodict=dict()
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
        zoomlevel=int(session.get('zoom',5))
        lat=float(request.params.get('lat'))
        lon=float(request.params.get('lon'))
        clickmerc=mapper.latlon2merc((lat,lon),zoomlevel)
        out=[]
        spaces="".join("<li><b>%s</b>: %s - %s%s</li>"%(space['name'],space['floor'],space['ceiling'],format_freqs(space['freqs'])) for space in sorted(
                get_airspaces(lat,lon),key=sort_airspace_key))
        if spaces=="":
            spaces="Uncontrolled below FL095"
        
        obstbytype=dict()
        for obst in get_obstacles(lat,lon,zoomlevel):
            obstbytype.setdefault(obst['kind'],[]).append(obst)
            print "processing",obst
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
            print "%d points"%(len(track.points))
            mindiff=1e30
            height=None
            for p,pheight in track.points: 
                print "Track lat/lon: ",p,"click lat/lon:",(lat,lon)
                merc=mapper.latlon2merc(p,zoomlevel)
                diff=math.sqrt((clickmerc[0]-merc[0])**2+(clickmerc[1]-merc[1])**2)
                print diff
                if diff<mindiff:
                    mindiff=diff
                    height=pheight
            print "Mindiff:",mindiff
            if mindiff<15:
                tracks.append(u"<b>GPS track altitude:</b><ul><li>%d ft</li></ul>"%(height/0.3048,))
                                              

        airports=[]
        fields=list(get_airfields(lat,lon,zoomlevel))
        if len(fields):
            airports.append("<b>Airfield:</b><ul>")
            for airp in fields:
                airports.append(u"<li><b>%s</b> - %s</li>"%(airp.get('icao','ZZZZ'),airp['name']))
            airports.append("</ul>")
        
        sigpoints=[]
        sigps=list(get_sigpoints(lat,lon,zoomlevel))
        if len(sigps):
            sigpoints.append("<b>Sig. points</b><ul>")
            for sigp in sigps:
                sigpoints.append(u"<li><b>%s</b></li>"%(sigp['name'],))
            sigpoints.append("</ul>")
       

        terrelev=get_terrain_elev((lat,lon))
        return "<b>Airspace:</b><ul>%s</ul>%s%s%s%s<br/><b>Terrain: %d ft</b>"%(spaces,"".join(obstacles),"".join(airports),"".join(tracks),"".join(sigpoints),terrelev)

    def get(self):
        # Return a rendered template
        #return render('/maptile.mako')
        # or, return a response
        my=int(request.params.get('mercy'))
        mx=int(request.params.get('mercx'))
        zoomlevel=int(request.params.get('zoom'))
        
        airspaces=True
        if 'showairspaces' in request.params:
            airspaces=int(request.params['showairspaces'])

        neededit=False
        if session.get('showarea','')!='':
            neededit=True                
        if session.get('showtrack',None)!=None:
            neededit=True                
        
        variant=None
        if airspaces:
            variant="airspace"
        else:
            variant="plain"
            
        
        generate_on_the_fly=False
        
        if generate_on_the_fly:
            im=generate_big_tile((256,256),mx,my,zoomlevel,tma=True,return_format="cairo")    
        else:
            rawtile=maptilereader.gettile(variant,zoomlevel,mx,my)
            if not neededit:
                response.headers['Content-Type'] = 'image/png'
                return rawtile
            io=StringIO.StringIO(rawtile)
            io.seek(0)
            im=cairo.ImageSurface.create_from_png(io)
            
        ctx=cairo.Context(im)
        
        
        if session.get('showarea','')!='':                
            print "Showarea rendering active"
            wp=[]
            print session.get('showarea','')
            for vert in mapper.parse_lfv_area(session.get('showarea')):
                mercx,mercy=mapper.latlon2merc(mapper.from_str(vert),int(session['zoom']))
                wp.append((mercx-mx,mercy-my))       
            print "wp:",wp
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
                    
        if session.get('showtrack',None)!=None:                
            print "Showtrack rendering active"
            track=session.get('showtrack')
            ctx.new_path()
            ctx.set_line_width(2.0)
            ctx.set_source(cairo.SolidPattern(0.0,0.0,1.0,1))
            #lastmecc
            print "%d points"%(len(track.points))
            for p,height in track.points:
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
                mercx,mercy=mapper.latlon2merc(mapper.from_str(vert),int(session['zoom']))
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
        response.headers['Content-Type'] = 'image/png'
        return png
        
