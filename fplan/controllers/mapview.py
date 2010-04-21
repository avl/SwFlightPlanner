import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from fplan.model import meta,User
import fplan.lib.mapper as mapper
import fplan.lib.gen_tile as gen_tile
from fplan.lib.base import BaseController, render
import routes.util as h
log = logging.getLogger(__name__)

class MapviewController(BaseController):      

    def zoom(self):
        user=meta.Session.query(User).filter(
                User.user==session['user']).one()

        lat,lon=mapper.from_str(user.last_map_pos)    
                
        if request.params['zoom']!='':
            zoom=float(request.params['zoom'])
            
            if zoom<0:
                user.last_map_size*=0.5
            else:
                user.last_map_size*=2.0                                
            if user.last_map_size<1.0/120.0:
                user.last_map_size=1.0/120.0            
            if user.last_map_size>10.0:
                user.last_map_size=10.0
        if request.params['center']!='':
            lats,lons=request.params['center'].split(",")
            lat=float(lats)
            lon=float(lons)%360.0
            
        if lat+user.last_map_size>85.0:
            lat=85.0-user.last_map_size
        if lat-user.last_map_size<-85.0:
            lat=-85.0+user.last_map_size
        user.last_map_pos=mapper.to_str((lat,lon))        
        meta.Session.flush()
        meta.Session.commit()

        
        redirect_to(h.url_for(controller='mapview',action="index"))

    
    def index(self):
        user=meta.Session.query(User).filter(
                User.user==session['user']).one()
        
        coords=mapper.from_str(user.last_map_pos)
        c.pos=mapper.to_aviation_format(coords)
        c.size=user.last_map_size
        c.lat=coords[0]
        c.lon=coords[1]
        
        lat1,lon1,lat2,lon2=gen_tile.get_map_corners((100,100),coords,user.last_map_size)
        print "lat1/lon1: %f/%f, lat2/lon2: %f/%f"%(lat1,lon1,lat2,lon2) 
        assert (abs(lat1-lat2)-user.last_map_size)<1e-6
        c.lonwidth=abs(lon2-lon1)
        
        return render('/mapview.mako')
