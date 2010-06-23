from fplan.extract.parse_notam import diff_notam,parse_notam
import fplan.extract.parse_notam as pn
from fplan.model import *
from fplan.extract.fetch_notams import get_latest_notam
from datetime import datetime
import sqlalchemy as sa
import sys,os
from fplan.config.environment import load_environment
from pylons import config



def notam_db_update():
    return notam_db_update_impl(get_latest_notam())
def notam_db_update_impl(html):
    prevobjs=meta.Session.query(Notam).order_by(sa.desc(Notam.ordinal)).limit(1).all()
    
    #print "Prevobjs:",prevobjs
    
    if len(prevobjs)!=0:
        prevobj,=prevobjs
        #prev=parse_notam(prevobj.notamtext)
        prevdbitems=list(meta.Session.query(NotamUpdate).filter(
                NotamUpdate.disappearnotam==sa.null()
                ).order_by([NotamUpdate.appearnotam,NotamUpdate.appearline]).all())
        #print "PREV:",prevdbitems
    else:
        prevobj=None
        prevdbitems=None
    latest=parse_notam(html)
    
    if not prevobj or prevobj.issued!=latest.issued or prevobj.notamtext!=latest.notamtext:
        #print "diff1",not prevobj
        #if prevobj:
        #    print "diff2",prevobj.issued!=latest.issued
        #    print "diffing===\n%s\n====\n%s"%(prevobj.notamtext,latest.notamtext)
        ordinal=None
        if prevobj:
            previtems=[]
            for prev in prevdbitems:
                previtems.append(pn.NotamItem(prev.appearline,prev.category))
                previtems[-1].text=prev.text
                previtems[-1].appearnotam=prev.appearnotam
            prev=pn.Notam(prevobj.issued,prevobj.downloaded,previtems,prevobj.notamtext)
            ordinal=prevobj.ordinal+1
            prev_ordinal=prevobj.ordinal
        else:
            prev_ordinal=None
            prev=None
            ordinal=1
     
        #print "Time to update, ordinal = %d"%(ordinal,)
        if prevobj:
            assert not (prev is None)
            #print "diffing: %s and %s"%(prev,latest)
            changed=diff_notam(prev,latest)
            modified=changed['modified']
            new=changed['new']
            cancelled=changed['cancelled']
        else:
            assert prev==None
            new=latest.items
            cancelled=[]
            modified=[]
        #print "Latest issued:%s"%(latest.issued,)
        notam=Notam(ordinal,latest.issued,datetime.utcnow(),latest.notamtext)
        meta.Session.add(notam)
        
        for cancobj in cancelled:
            #print "Cancelled NotamItem: %s (appearnotam: %d)"%(cancobj,cancobj.appearnotam)
            origobjs=meta.Session.query(NotamUpdate).filter(sa.and_(
                NotamUpdate.appearnotam==cancobj.appearnotam,
                NotamUpdate.appearline==cancobj.appearline)).all()
            #print "Objects selected for cancellation",origobjs
            assert(len(origobjs)==1)
            origobjs[0].disappearnotam=ordinal
        for newitem in new:
            ni=NotamUpdate(appearnotam=ordinal,
                            appearline=newitem.appearline,
                            category=newitem.category,
                            text=newitem.text)
            meta.Session.add(ni)
        for previtem,newitem in modified:
            #old,new
            origobj,=meta.Session.query(NotamUpdate).filter(sa.and_(
                NotamUpdate.appearnotam==previtem.appearnotam,
                NotamUpdate.appearline==previtem.appearline)).all()
            origobj.disappearnotam=ordinal
            ni=NotamUpdate(appearnotam=ordinal,
                            appearline=newitem.appearline,
                            category=newitem.category,
                            text=newitem.text)
            ni.prevnotam=origobj.appearnotam
            ni.prevline=origobj.appearline
            
            meta.Session.add(ni)
            
        meta.Session.flush()

if __name__=='__main__':            
    run_update()
def run_update():
    notam_db_update_impl(unicode(open(os.getenv("DL_NOTAM_PATH")).read(),'latin1'))
    meta.Session.commit()
    
    
