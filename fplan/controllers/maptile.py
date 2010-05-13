import logging
import re
from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
import fplan.lib.mapper as mapper
import StringIO

from fplan.lib.base import BaseController, render
import Image,ImageDraw
log = logging.getLogger(__name__)

class MaptileController(BaseController):
    no_login_required=True #But we don't show personal data without login
    
    def get(self):
        # Return a rendered template
        #return render('/maptile.mako')
        # or, return a response
        my=int(request.params.get('mercy'))
        mx=int(request.params.get('mercx'))
        path="/home/anders/saker/avl_fplan_world/tiles/%d/%d/%d.png"%(
            int(request.params.get('zoom')),
            my,mx)

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
        
        #print "Corners:",get_map_corners(pixelsize=(width,height),center=pos,lolat=lower,hilat=upper)
        response.headers['Content-Type'] = 'image/png'
        return png
