import extract_airfields
from fplan.model import meta
from fplan.model import *


def update_airfields():
    for ad in extract_airfields.extract_airfields():
        matches=meta.Session.query(Airport).filter(
                Airport.icao==ad['icao']).all()
        if len(matches):
            match,=matches
            match.airport=ad['name']
            match.pos=ad['pos']
            match.elev=ad['elev']
        else:
            ap=Airport(
                airport=ad['name'],
                icao=ad['icao'],
                pos=ad['pos'],
                elev=ad['elev']
                )
            meta.Session.add(ap)
    meta.Session.flush()
    meta.Session.commit()
    
    