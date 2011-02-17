#encoding=utf8
from selenium import selenium
import  time, re
from helpers import *

    
def test_test_subzero_gs():
    sel = selenium("localhost", 4444, "*firefox", "http://localhost:5000/")
    sel.start()
    #sel.getEval("window.resizeTo(640, 480); window.moveTo(0,0);")
    sel.window_maximize()

    login(sel)
    if "test_headwind" in list_other_trips(sel):
        open_trip(sel,"test_headwind")
        delete_cur_trip(sel)    
        
    add_trip(sel,"test_headwind")
    #assert "test_headwind" in list_other_trips(sel)
    assert get_cur_trip(sel)=="test_headwind"
    add_named_wp(sel,u"frölunda")
    add_named_wp(sel,u'stockholm/västerås')        
    sel.click("link=Flightplan")
    sel.wait_for_page_to_load("30000")
    
    sel.type_keys("fplanrow100W", "270")
    sel.type_keys("fplanrow100V", "80")
    sel.type("fuel_100", "70")
    sel.type("persons_100", "2")
    
    wait_not_visible(sel,"progmessage")
    sel.open("/flightplan/printable?trip=test_headwind")
    bt=sel.get_body_text()    
    assert (re.search(ur"^[\s\S]*EXPECTED HEADWIND IS GREATER THAN TAS![\s\S]*$", bt))
    assert (re.search(ur"^[\s\S]*Frölunda[\s\S]*$", bt))
    assert (re.search(ur"^[\s\S]*Västerås[\s\S]*$", bt))
    
    sel.open("/flightplan/index")

    sel.type("fplanrow100W", "")
    sel.type("fplanrow100V", "")
    sel.type_keys("fplanrow100W", "270")
    sel.type_keys("fplanrow100V", "10")
    wait_not_visible(sel,"progmessage")
    sel.open("/flightplan/printable?trip=test_headwind")
    bt=sel.get_body_text()    
    assert None==re.search(ur"^[\s\S]*EXPECTED HEADWIND IS GREATER THAN TAS![\s\S]*$", bt)
    
    sel.open("/mapview/index")
    
    delete_cur_trip(sel)    
    assert not "test_headwind" in list_other_trips(sel)
    assert get_cur_trip(sel)!="test_headwind"

    sel.stop()

    
