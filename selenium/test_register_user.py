#encoding=utf8
import  time, re
from helpers import *
from fplan.lib.db_env_loader import ensure_loaded
from fplan.model import meta,User
    
def test_register_user():
    ensure_loaded()
    
    meta.Session.query(User).filter(User.user=="selenium_new").delete()
    meta.Session.flush()
    meta.Session.commit()
    
    with selconn() as sel:
        sel.click("link=Start using immediately!")
        sel.wait_for_page_to_load("10000")        
        sel.click("link=Create User")
        sel.wait_for_page_to_load("10000")
        sel.type("username", "selenium_new")
        sel.type("password1", "1234")
        sel.type("password2", "5678")
        sel.click("save")
        sel.wait_for_page_to_load("10000")
        assert sel.get_body_text().count("Passwords do not match! Enter the same password twice.") 
        sel.type("password1", "1234")
        sel.type("password2", "1234")
        sel.click("save")
        sel.wait_for_page_to_load("10000")
        print "user:",sel.get_value("username")
        assert "selenium_new"==sel.get_value("username")
        assert not sel.get_body_text().count("That username is already taken") 
         
        
        
        