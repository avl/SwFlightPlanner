from datetime import datetime,timedelta
from fplan.model import *
import sqlalchemy as sa
import os

def run():
    q=meta.Session.query(User).filter(sa.and_(
        User.lastlogin<datetime.utcnow()-timedelta(7),User.isregistered==False))
    print "Removing %d old unregistered users"%(q.count())
    q.delete()
    meta.Session.commit()    

if __name__=='__main__':
    from sqlalchemy import engine_from_config
    from paste.deploy import appconfig
    from fplan.config.environment import load_environment
    conf = appconfig('config:%s'%(os.path.join(os.getcwd(),"development.ini"),))    
    load_environment(conf.global_conf, conf.local_conf)
    run()
    
