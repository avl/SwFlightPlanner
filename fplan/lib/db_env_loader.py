from sqlalchemy import engine_from_config
from paste.deploy import appconfig
from fplan.config.environment import load_environment
from fplan.model import meta,User,Trip,Waypoint,Route
import os

loaded=False
loading=False
def ensure_loaded():
    global loaded
    global loading
    if not loaded:
        assert not loading
        loading=True  
        try:
            conf = appconfig('config:%s'%(os.path.join(os.getenv("SWFP_ROOT"),"development.ini"),))    
            load_environment(conf.global_conf, conf.local_conf)
        except:
            loading=False
            raise
        loaded=True  
