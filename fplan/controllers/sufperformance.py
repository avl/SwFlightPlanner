#encoding=utf8
import logging
import sqlalchemy as sa
#from md5 import md5
from fplan.model import meta,User,Aircraft
from datetime import datetime
from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect
import routes.util as h
from fplan.lib.base import BaseController, render
import fplan.extract.gfs_weather as gfs_weather
import fplan.lib.tripsharing as tripsharing
import re
import os
import fplan.lib.metartaf as metartaf
import fplan.lib.mapper as mapper
import traceback
import json
import fplan.extract.extracted_cache as ec
log = logging.getLogger(__name__)
from fplan.controllers.flightplan import strip_accents

def filter(ad):
    if not 'runways' in ad: return False
    return True
class SufperformanceController(BaseController):

    def search(self):
        print "Search called:",request.params
        
        term=strip_accents(request.params['term']).lower()
        if len(term)<3:
            return json.dumps([])
        response.headers['Content-Type'] = 'application/json'
        
        hits=[]
        for ac in ec.get_airfields():
            if not filter(ac): continue
            if (strip_accents(ac['name']).lower().count(term)):
                hits.append(ac['name'])
        hits.sort()
        return json.dumps(hits[:10])
    def load(self):
        name=request.params['name']
        print "Loading",repr(name)
        for ac in ec.get_airfields():
            if not filter(ac): continue
            if ac['name']==name:
                print "Match:",name,ac
                out=[]
                
                if 'runways' in ac:
                    for rwy in ac['runways']:
                        for i,end in enumerate(rwy['ends']):
                            endb=rwy['ends'][(i+1)%2]
                            brg,dist=mapper.bearing_and_distance(mapper.from_str(end['pos']),mapper.from_str(endb['pos']))
                            out.append(dict(
                                name=end['thr'],
                                rwyhdg=brg,
                                available_landing=dist*1852.0,
                                available_takeoff=dist*1852.0                                
                                ))
                return json.dumps(dict(runways=out))

        response.headers['Content-Type'] = 'application/json'
        return json.dumps(dict(runways=[]))
    def index(self):
        when,valid,fct=gfs_weather.get_prognosis(datetime.utcnow())
        lat=59.45862
        lon=17.70680
        c.qnh=1013
        c.winddir=0
        c.windvel=0
        c.field=u"Frölunda"
        c.searchurl=h.url_for(controller='sufperformance',action='search')
        c.airport_load_url=h.url_for(controller='sufperformance',action='load')
        metar=metartaf.get_metar('ESSA')
        print "metar:",metar
        try:
            c.temp,dew=re.match(r".*\b(\d{2})/(\d{2})\b.*",metar.text).groups()
            print "c.temp:",c.temp
            if c.temp.startswith("M"):
                c.temp=-int(c.temp[1:])
            else:
                c.temp=int(c.temp)
        except:
            print traceback.format_exc()
            c.temp=15
        try:
            c.qnh=fct.get_qnh(lat,lon)        
            c.winddir,c.windvel=fct.get_surfacewind(lat,lon)
            c.winddir=int(c.winddir)
            c.windvel=int(c.windvel)
        except:
            print traceback.format_exc()
            pass
        
        return render('/sufperformance.mako')
