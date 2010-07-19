import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from fplan.model import *
from fplan.lib.base import BaseController, render
import sqlalchemy as sa
log = logging.getLogger(__name__)
import json
import routes.util as h

class NotamController(BaseController):

    def index(self):
        
        ack_cnt = meta.Session.query(NotamAck.appearnotam,NotamAck.appearline,sa.func.count('*').label('acks')).filter(NotamAck.user==session.get('user',None)).group_by([NotamAck.appearnotam,NotamAck.appearline]).subquery()
    
        c.items=meta.Session.query(NotamUpdate,ack_cnt.c.acks,Notam.downloaded).outerjoin(
                (ack_cnt,sa.and_(                    
                    NotamUpdate.appearnotam==ack_cnt.c.appearnotam,
                    NotamUpdate.appearline==ack_cnt.c.appearline))).outerjoin(
                (Notam,Notam.ordinal==NotamUpdate.appearnotam)
                 ).order_by(sa.desc(Notam.downloaded)).filter(
                        NotamUpdate.disappearnotam==sa.null()).all()
        
        
        print "Start rendering mako"
        return render('/notam.mako')
    def show_ctx(self):
        notam=meta.Session.query(Notam).filter(
             Notam.ordinal==int(request.params['notam'])).one()
        
        all_lines=list(notam.notamtext.splitlines())
        startline=int(request.params['line'])
        endline=startline
        cnt=len(all_lines)
        while True:
            if endline>=cnt:
                break
            if all_lines[endline].strip()=="":
                break
            endline+=1
        c.startlines=all_lines[:startline]
        c.midlines=all_lines[startline:endline]
        c.endlines=all_lines[endline:]
            
        return render('/notam_ctx.mako')
    def markall(self):
        #TODO: This could be done in a way smarter way! TODO: Checkout subqueries in sqlalchemy
        notamupdates=\
            list(meta.Session.query(NotamUpdate).filter(
                NotamUpdate.disappearnotam==sa.null()).order_by([sa.desc(NotamUpdate.appearnotam),sa.asc(NotamUpdate.appearline)]).all())
        
        acks=set([(ack.appearnotam,ack.appearline) for ack in meta.Session.query(NotamAck).filter(sa.and_(
                NotamAck.user==session['user'],
                NotamUpdate.disappearnotam==sa.null(),
                NotamAck.appearnotam==NotamUpdate.appearnotam,
                NotamAck.appearline==NotamUpdate.appearline)).all()])
        for u in notamupdates:
            if not ((u.appearnotam,u.appearline) in acks):
                print "Acking ",(u.appearnotam,u.appearline,u.text)
                ack=NotamAck(session['user'],u.appearnotam,u.appearline)
                meta.Session.add(ack)
        meta.Session.flush()
        meta.Session.commit()
        return redirect_to(h.url_for(controller='notam',action="index"))

    def mark(self):
        out=[]
        for notam,line,marked in json.loads(request.params['toggle']):
            acks=meta.Session.query(NotamAck).filter(
                sa.and_(
                    NotamAck.user==session['user'],
                    NotamAck.appearnotam==notam,
                    NotamAck.appearline==line)).all()
            if marked and len(acks)==0:
                ack=NotamAck(session['user'],notam,line)
                meta.Session.add(ack)
            if not marked and len(acks):
                for ack in acks:
                    meta.Session.delete(ack)
            out.append([notam,line,marked])
        meta.Session.flush()
        meta.Session.commit()
        return json.dumps(out)
        
        
