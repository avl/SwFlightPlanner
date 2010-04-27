import extract_airfields
from fplan.model import meta
from fplan.model import *


def update_airfields():
    for ad in extract_airfields.extract_airfields():
        meta.Session.query(User).all()
        user1 = User(u"anders.musikka", u"password")
        meta.Session.add(user1)
        meta.Session.flush()
    meta.Session.commit()
    
    