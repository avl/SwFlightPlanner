#encoding=utf8
import logging
import re
from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect
from fplan.model import *
from fplan.lib.base import BaseController, render
import sqlalchemy as sa
log = logging.getLogger(__name__)
import json
import routes.util as h
from fplan.extract.extracted_cache import get_airfields
class NotamController(BaseController):

    def index(self):
        
        ack_cnt = meta.Session.query(NotamAck.appearnotam,NotamAck.appearline,sa.func.count('*').label('acks')).filter(NotamAck.user==session.get('user',None)).group_by(NotamAck.appearnotam,NotamAck.appearline).subquery()
    
        c.items=meta.Session.query(NotamUpdate,ack_cnt.c.acks,Notam.downloaded).outerjoin(
                (ack_cnt,sa.and_(                    
                    NotamUpdate.appearnotam==ack_cnt.c.appearnotam,
                    NotamUpdate.appearline==ack_cnt.c.appearline))).outerjoin(
                (Notam,Notam.ordinal==NotamUpdate.appearnotam)
                 ).order_by(sa.desc(Notam.downloaded)).filter(
                        NotamUpdate.disappearnotam==sa.null()).all()
        c.categories=set([notamupdate.category for notamupdate,acks,downloaded in c.items])
        user=meta.Session.query(User).filter(User.user==session['user']).one()
        c.showobst=user.showobst
        
        
        
        def vandalize(x):
            x=x.replace(u"Å",u"A")
            x=x.replace(u"Ä",u"A")
            x=x.replace(u"Ö",u"O")
            return x
        for air in get_airfields():
            c.categories.add(vandalize(u"%s/%s"%(air['icao'].upper(),air['name'].upper())))
        c.sel_cat=set(x.category for x in meta.Session.query(NotamCategoryFilter).filter(NotamCategoryFilter.user==session['user']))
        c.shown=[]
        c.show_cnt=0
        c.hide_cnt=0
        c.countries=[
           dict(name="Sweden",sel=False,short="ES"),
           dict(name="Finland",sel=False,short="EF"),
        ]
        if 1:
            for ct in meta.Session.query(NotamCountryFilter).filter(
                    NotamCountryFilter.user==session['user']).all():
                for countrydict in c.countries:
                    if countrydict['name']==ct.country:
                        countrydict['sel']=True
        selcountries=set()
        for ct in c.countries:
            if ct['sel']:
                selcountries.add(ct['short'])
        if len(selcountries)==0:
            selcountries=None
        ms=[]
        ms.append(re.compile(r".*\bOBST\s+ERECTED\b.*"))
        ms.append(re.compile(r".*TURBINE?S?\s+ERECTED\b.*"))
        ms.append(re.compile(r".*\bMASTS?\s+ERECTED\b.*"))
        ms.append(re.compile(r".*\bCRANES?\s+ERECTED\b.*"))
        ms.append(re.compile(r".*LIGHTS?.*OUT\s+OF\s+SERVICE.*",re.DOTALL))
        for notamupdate,acks,downloaded in c.items:
            if not c.showobst:
                match=False
                for m in ms:
                    if m.match(notamupdate.text):
                        match=True
                        break
                if match:
                    c.hide_cnt+=1
                    continue
                
            if (len(c.sel_cat)==0 or notamupdate.category in c.sel_cat) and \
                (selcountries==None or notamupdate.category==None or notamupdate.category[:2] in selcountries):
                c.shown.append((notamupdate,acks,downloaded))
                c.show_cnt+=1
            else:
                c.hide_cnt+=1
        print "Start rendering mako"
        return render('/notam.mako')
    def show_ctx(self):
        notams=meta.Session.query(Notam).filter(
             Notam.ordinal==int(request.params['notam'])).all()
        if len(notams)==0:
            return redirect(h.url_for(controller='notam',action="index"))
        notam,=notams
        c.backlink=request.params.get('backlink',
            h.url_for(controller="notam",action="index"))
        
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
    def savefilter(self):
        meta.Session.query(NotamCategoryFilter).filter(NotamCategoryFilter.user==session['user']).delete()
        meta.Session.flush()
        meta.Session.commit()
        user=meta.Session.query(User).filter(User.user==session['user']).one()
        print "Number of items: ",meta.Session.query(NotamCategoryFilter).filter(NotamCategoryFilter.user==session['user']).count()
        cats=set()
        if 'showobst' in request.params:
            user.showobst=True
        else:
            user.showobst=False
        meta.Session.query(NotamCountryFilter).filter(NotamCountryFilter.user==session['user']).delete()
        for key,value in request.params.items():
            print "Processing ",key,value
            if key.startswith("category_"):
                cat=key.split("_")[1]
                if cat in cats: continue
                cats.add(cat)
                category=NotamCategoryFilter(session['user'],cat)
                print "Inserted ",cat
                meta.Session.add(category)
            if key.startswith("country_"):
                country=key.split("_")[1]
                countryf=NotamCountryFilter(session['user'],country)
                print "Added country obj",country
                meta.Session.add(countryf)
                
        meta.Session.flush()
        meta.Session.commit()
        return redirect(h.url_for(controller='notam',action="index"))
        
    def markall(self):
        #TODO: This could be done in a way smarter way! TODO: Checkout subqueries in sqlalchemy
        notamupdates=\
            list(meta.Session.query(NotamUpdate).filter(
                NotamUpdate.disappearnotam==sa.null()).order_by(sa.desc(NotamUpdate.appearnotam),sa.asc(NotamUpdate.appearline)).all())
        
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
        return redirect(h.url_for(controller='notam',action="index"))

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
        
        
