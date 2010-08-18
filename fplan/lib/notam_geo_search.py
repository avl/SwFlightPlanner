import sqlalchemy as sa
from fplan.model import *
from pyshapemerge2d import Polygon,vvector,Vertex
import fplan.lib.mapper as mapper
import re




def get_notam_objs(kind=None):    
    notamupdates=meta.Session.query(NotamUpdate).filter(
              NotamUpdate.disappearnotam==sa.null()).all()
    obstacles=[]
    others=[]
    spaces=[]
    areas=[]
    for u in notamupdates:
        text=u.text.strip()
        coords=list(mapper.parse_lfv_area(text,False))
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
                        kind='Notam',
                        notam_ordinal=u.appearnotam,
                        notam_line=u.appearline,
                        name=text.split("\n")[0],
                        notam=text))
                continue
        else:
            if len(coords)<=2 and (kind==None):
                for coord in coords:
                    others.append(dict(
                        pos=coord,
                        kind='notam',
                        name=text,
                        notam_ordinal=u.appearnotam,
                        notam_line=u.appearline,
                        notam=text))
            else:
                if len(coords)>2:
                    areas.append(dict(
                        points=coords,
                        kind="notamarea",
                        name=text,
                        type="notamarea",
                        notam_ordinal=u.appearnotam,
                        notam_line=u.appearline,
                        notam=text))
                    print "Found a notam area:",text
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
        print "Reparsing notams"
        notam_geo_cache=dict()
        notam_geo_cache['data']=get_notam_objs()
        notam_geo_cache['ord']=cur_notam_ordinal
    return notam_geo_cache['data']
    
    
    
