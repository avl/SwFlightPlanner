import sqlalchemy as sa
from fplan.model import *
from pyshapemerge2d import Polygon,vvector,Vertex
import fplan.lib.mapper as mapper
import re

def get_notam_objs():    
    notamupdates=meta.Session.query(NotamUpdate).filter(
              NotamUpdate.disappearnotam==sa.null()).all()
    obstacles=[]
    others=[]
    spaces=[]
    for u in notamupdates:
        text=u.text
        coords=list(mapper.parse_lfv_area(text,False))
        if len(coords)==0: continue
        if text.startswith("OBST"):
            elevs=re.findall(r"ELEV\s*\d+\s*FT",text)
            elevs=[int(x) for x in elevs if x.isdigit()]
            if len(elevs)!=0:                
                elev=max(elevs)
                for coord in coords:
                    obstacles.append(dict(
                        pos=coord,
                        elev=elev,
                        kind='obstacle',
                        name="Notam Obstacle elev %d ft"%(elev,),
                        notam=text))
                continue
        if len(coords)<=2:
            for coord in coords:
                others.append(dict(
                    pos=coord,
                    kind='notam',
                    name="Notam Item",
                    notam=text))
        else:
            pass
            #polyc=[]
            #for coord in coords:
            #    polyc.append(Vertex(*mapper.latlon2merc(mapper.from_str(coord),13)))
            #poly=Polygon(vvector(polyc))
            #spaces.append(dict(
            #    poly=poly,
            #    name='Notam Area',
            #    notam=text))
    return obstacles+others#dict(obstacles=obstacles,others=others,spaces=spaces)
 
 
