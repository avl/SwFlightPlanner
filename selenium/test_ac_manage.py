#encoding=utf8
import  time, re
from helpers import *

def test_aircraftmanage():
    with temporary_trip("test_typical") as sel:
        sel.click("link=Aircraft")
        sel.wait_for_page_to_load("10000")
        if sel.is_element_present("name=change_aircraft"):
            for ac in list(sel.get_select_options("name=change_aircraft")):
                sel.select("change_aircraft",ac)
                sel.click("del_button")
                sel.wait_for_page_to_load("10000")
                    
        sel.click("add_button")
        sel.wait_for_page_to_load("10000")
        sel.type("aircraft", "SE-TST")
        sel.click("save_button")
        sel.wait_for_page_to_load("10000")        
        sel.select("change_aircraft","SE-TST")
        sel.click("del_button")
        sel.wait_for_page_to_load("10000")        
        assert 0==len(list(sel.get_select_options("change_aircraft")))
