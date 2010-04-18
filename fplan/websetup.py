"""Setup the fplan application"""
import logging

from fplan.config.environment import load_environment
from fplan.model import meta
from fplan.model import *
log = logging.getLogger(__name__)

def setup_app(command, conf, vars):
    """Place any commands to setup fplan here"""
    load_environment(conf.global_conf, conf.local_conf)

    # Create the tables if they don't already exist
    meta.metadata.create_all(bind=meta.engine)

    if len(meta.Session.query(User).all())==0:       
        user1 = User("anders.musikka", "password")
        meta.Session.add(user1)
        meta.Session.flush()
    meta.Session.commit()
        