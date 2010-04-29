import logging
import re
from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from fplan.lib.gen_tile import generate_tile,get_map_corners
import fplan.lib.mapper as mapper

from fplan.lib.base import BaseController, render

log = logging.getLogger(__name__)

class MaptileController(BaseController):
    no_login_required=True #But we don't show personal data without login
    
    def get(self):
        # Return a rendered template
        #return render('/maptile.mako')
        # or, return a response
        #png=open("fplan/public/boilerplate.jpg").read()
        #png=open("fplan/public/bg.png").read()
        
        pos=mapper.from_aviation_format(request.params["pos"]);
        zoomlevel=float(request.params['zoomlevel'])
        width=int(request.params['width'])
        height=int(request.params['height'])
        #png=open("fplan/public/bg.png").read()
        #request.params.get('layout','para')
        
        merc_x,merc_y=mapper.latlon2merc(pos,zoomlevel)
        upper=mapper.merc2latlon((merc_x,merc_y-height/2.0),zoomlevel)[0]
        lower=mapper.merc2latlon((merc_x,merc_y+height/2.0),zoomlevel)[0]

        print "generating, zoom level: %f"%(zoomlevel,)
        print "Rendered lat interval: %f - %f"%(upper,lower)
        png=generate_tile(pixelsize=(width,height),center=pos,lolat=lower,hilat=upper)
        print "Corners:",get_map_corners(pixelsize=(width,height),center=pos,lolat=lower,hilat=upper)
        response.headers['Content-Type'] = 'image/png'
        return png
