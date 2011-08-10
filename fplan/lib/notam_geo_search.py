import sqlalchemy as sa
from fplan.model import *
from pyshapemerge2d import Polygon,vvector,Vertex
import fplan.lib.mapper as mapper
import re
from itertools import chain
import os


def get_notam_objs(kind=None):    
    notamupdates=meta.Session.query(NotamUpdate).filter(
              NotamUpdate.disappearnotam==sa.null()).all()
    obstacles=[]
    others=[]
    spaces=[]
    areas=[]
    for u in notamupdates:
        text=u.text.strip()

        if text.count("W52355N0234942E"):
            text=text.replace("W52355N0234942E","652355N0234942E")
        coordgroups=[]
        for line in text.split("\n"):
            dig=False
            for char in line:
                if char.isdigit():
                    dig=True
            if dig==False:
                if len(coordgroups) and coordgroups[-1]!="":
                    coordgroups.append("")
            else:
                if len(coordgroups)==0: coordgroups=[""]
                coordgroups[-1]+=line+"\n"

        if (kind==None or kind=="notamarea"):
            
            for radius,unit,lat,lon in chain(
                re.findall(r"RADIUS\s*(?:OF)?\s*(\d+)\s*(NM|M)\s*(?:CENT[ERD]+|FR?O?M)?\s*(?:ON)?\s*(?:AT)?\s*(\d+[NS])\s*(\d+[EW])",text),
                re.findall(r"(\d+)\s*(NM|M)\s*RADIUS\s*(?:CENT[ERD]+)?\s*(?:ON|AT|FROM)?\s*(\d+[NS])\s*(\d+[EW])",text),
                re.findall(r"(\d+)\s*(NM|M)\s*RADIUS.*?[^0-9](\d+[NS])\s*(\d+[EW])",text,re.DOTALL)
                ):
                try:
                    radius=float(radius)
                    if unit=="M":
                        radius=radius/1852.0
                    else:
                        assert unit=="NM"
                    centre=mapper.parse_coords(lat,lon)
                    coords=mapper.create_circle(centre,radius)
                    areas.append(dict(
                            points=coords,
                            kind="notamarea",
                            name=text,
                            type="notamarea",
                            notam_ordinal=u.appearnotam,
                            notam_line=u.appearline,
                            notam=text))
                except Exception,cause:
                    print "Invalid notam coords: %s,%s"%(lat,lon)
                    
                    
                    
                    
        for coordgroup in coordgroups:        
            try:
                coords=list(mapper.parse_lfv_area(coordgroup,False))
            except Exception,cause:
                print "Parsing,",coordgroup
                print "Exception parsing lfv area from notam:%s"%(cause,)
                coords=[]
            
            if len(coords)==0: continue
            if text.count("OBST") and (kind==None or kind=="obstacle"):
                elevs=re.findall(r"ELEV\s*(\d+)\s*FT",text)
                elevs=[int(x) for x in elevs if x.isdigit()]
                if len(elevs)!=0:                
                    elev=max(elevs)
                    for coord in coords:
                        obstacles.append(dict(
                            pos=coord,
                            elev=elev,
                            elevf=mapper.parse_elev(elev),
                            kind='notam',
                            notam_ordinal=u.appearnotam,
                            notam_line=u.appearline,
                            name=text.split("\n")[0],
                            notam=text))
                    continue
            couldbearea=True
            if len(coords)<=2:
                couldbearea=False
            if text.count("PSN")>=len(coords)-2:
                couldbearea=False
            if couldbearea==False and (kind==None or kind=="notam"):
                for coord in coords:
                    others.append(dict(
                        pos=coord,
                        kind='notam',
                        name=text,
                        notam_ordinal=u.appearnotam,
                        notam_line=u.appearline,
                        notam=text))
            if couldbearea==True and (kind==None or kind=="notamarea"):
                if len(coords)>2:
                    if text.startswith("AREA: "):
                        continue #These aren't real notams, they're area-specifications for all other notams... make this better some day.                        
                    areas.append(dict(
                        points=coords,
                        kind="notamarea",
                        name=text,
                        type="notamarea",
                        notam_ordinal=u.appearnotam,
                        notam_line=u.appearline,
                        notam=text))
                    #print "Found a notam area:",text
                #polyc=[]
                #for coord in coords:
                #    polyc.append(Vertex(*mapper.latlon2merc(mapper.from_str(coord),13)))
                #poly=Polygon(vvector(polyc))
                #spaces.append(dict(
                #    poly=poly,
                #    name='Notam Area',
                #    notam=text))
    return dict(obstacles=obstacles,others=others,areas=areas)#+others#dict(obstacles=obstacles,others=others,spaces=spaces)
 
notam_geo_cache=None
def get_notam_objs_cached():
    global notam_geo_cache
    cur_notam_ordinal,=meta.Session.query(sa.func.max(Notam.ordinal)).one()
    if notam_geo_cache==None or notam_geo_cache['ord']<cur_notam_ordinal:
        #print "Reparsing notams"
        objs=get_notam_objs()
        notam_geo_cache=dict()
        notam_geo_cache['data']=objs
        notam_geo_cache['ord']=cur_notam_ordinal
    return notam_geo_cache['data']
    
    
if __name__=='__main__':
    from sqlalchemy import engine_from_config
    from paste.deploy import appconfig
    from fplan.config.environment import load_environment
    conf = appconfig('config:%s'%(os.path.join(os.getcwd(),"development.ini"),))    
    load_environment(conf.global_conf, conf.local_conf)
    get_notam_objs_cached()
        
