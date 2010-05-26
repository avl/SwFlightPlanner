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
from fplan.lib.airspace import get_airspaces
log = logging.getLogger(__name__)
from fplan.lib.parse_gpx import parse_gpx


class MaptileController(BaseController):
    no_login_required=True #But we don't show personal data without login
    
    def get_airspace(self):
        lat=float(request.params.get('lat'))
        lon=float(request.params.get('lon'))
        out=[]
        
        return "<ul>"+"".join("<li><b>%s</b>: %s - %s</li>"%(space['name'],space['floor'],space['ceiling']) for space in get_airspaces(lat,lon))+"</ul>"

    def get(self):
        # Return a rendered template
        #return render('/maptile.mako')
        # or, return a response
        my=int(request.params.get('mercy'))
        mx=int(request.params.get('mercx'))
        zoomlevel=int(request.params.get('zoom'))
        
        airspaces=True
        
        
        if airspaces:
            im=generate_big_tile((256,256),mx,my,zoomlevel,tma=True,return_format="cairo")
        else:        
            path="/home/anders/saker/avl_fplan_world/tiles/%d/%d/%d.png"%(
                zoomlevel,
                my,mx)
            im=cairo.ImageSurface.create_from_png(path)
            
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
            gpxcontents=session.get('showtrack')
            ctx.new_path()
            ctx.set_line_width(2.0)
            ctx.set_source(cairo.SolidPattern(0.0,0.0,1.0,1))
            #lastmecc
            for p in parse_gpx(gpxcontents):
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
        
