from fplan.model import meta,Notam,NotamUpdate
import sqlalchemy as sa
import os
from datetime import datetime,timedelta
import sys

def run():
    
    
    activecnt = meta.Session.query(
                NotamUpdate.appearnotam).filter(
                    NotamUpdate.disappearnotam==None).distinct().subquery()
    
    now=datetime.utcnow()
    cutoff=now-timedelta(days=14)
    
    
    ncnt=meta.Session.query(Notam).filter(
                    sa.and_(
                        sa.not_(sa.exists().where(sa.and_(
                            Notam.ordinal==NotamUpdate.appearnotam,
                            NotamUpdate.disappearnotam==None))),
                        Notam.downloaded<cutoff
                    )).delete(False)

    ucnt=meta.Session.query(NotamUpdate).filter(
                    sa.and_(
                        sa.exists().where(
                            sa.and_(
                                Notam.downloaded<cutoff,
                                Notam.ordinal==NotamUpdate.disappearnotam)),
                        NotamUpdate.disappearnotam!=None
                    )).delete(False)
    print "Deleted %d notams, and %d notamupdates"%(ncnt,ucnt)
    meta.Session.flush()
    meta.Session.commit()


if __name__=='__main__':
    from paste.deploy import appconfig
    from fplan.config.environment import load_environment
    conf = appconfig('config:%s'%(os.path.join(os.getcwd(),"development.ini"),))    
    load_environment(conf.global_conf, conf.local_conf)
    run()
    