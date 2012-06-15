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
import traceback
log = logging.getLogger(__name__)

class SufperformanceController(BaseController):

    def index(self):
        when,valid,fct=gfs_weather.get_prognosis(datetime.utcnow())
        lat=59.45862
        lon=17.70680
        c.qnh=1013
        c.winddir=0
        c.windvel=0
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
