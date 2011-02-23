#encoding=utf8
import  time, re
from helpers import *
    
def test_subzero_gs():
    with temporary_trip("test_headwind") as sel:
        assert not sel.is_element_present("name=row_0_name")
        sel.click("link=Flightplan")
        sel.wait_for_page_to_load("10000")
        bt=sel.get_body_text()    
      
        sel.click("link=Map")
        sel.wait_for_page_to_load("10000")
        
        add_named_wp(sel,u"frölunda")
        assert sel.is_element_present("name=row_0_name")
        add_named_wp(sel,u'stockholm/västerås')        

        sel.click("link=Flightplan")
        sel.wait_for_page_to_load("10000")
        
        sel.type_keys("fplanrow100W", "270")
        sel.type_keys("fplanrow100V", "80")
        sel.type("fuel_100", "70")
        sel.type("persons_100", "2")
        
        wait_not_visible(sel,"progmessage")
        sel.open("/flightplan/printable?trip=test_headwind")
        sel.wait_for_page_to_load("10000")
        bt=sel.get_body_text()    
        assert (re.search(ur"^[\s\S]*EXPECTED HEADWIND IS GREATER THAN TAS![\s\S]*$", bt))
        assert (re.search(ur"^[\s\S]*Frölunda[\s\S]*$", bt))
        assert (re.search(ur"^[\s\S]*Västerås[\s\S]*$", bt))
        
        sel.open("/flightplan/index")
        sel.wait_for_page_to_load("10000")
    
        sel.type("fplanrow100W", "")
        sel.type("fplanrow100V", "")
        sel.type_keys("fplanrow100W", "270")
        sel.type_keys("fplanrow100V", "10")
        wait_not_visible(sel,"progmessage")
        sel.open("/flightplan/printable?trip=test_headwind")
        sel.wait_for_page_to_load("10000")
        bt=sel.get_body_text()    
        assert None==re.search(ur"^[\s\S]*EXPECTED HEADWIND IS GREATER THAN TAS![\s\S]*$", bt)
        
        

    
