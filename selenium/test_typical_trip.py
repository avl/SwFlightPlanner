#encoding=utf8
import  time, re
from helpers import *

def test_typical_trip():
    with temporary_trip("test_typical") as sel:
        
        
        
        assert not sel.is_element_present("name=row_0_name")
        add_named_wp(sel,u"stockholm/västerås")
        assert sel.is_element_present("name=row_0_name")
        add_named_wp(sel,u'gävle')        
        add_named_wp(sel,u'borlänge') 
               
        sel.click("link=Aircraft")
        sel.wait_for_page_to_load("10000")
        if not sel.is_element_present("name=change_aircraft"):
            sel.click("add_button")
            sel.wait_for_page_to_load("10000")
            sel.type("aircraft", "SE-TST")
            sel.click("save_button")
            sel.wait_for_page_to_load("10000")        

        sel.click("link=Flightplan")
        sel.wait_for_page_to_load("10000")
        sel.type("date_of_flight_100", "2011-02-22")
        sel.type("departure_time_100", "09:00")
        sel.type("fuel_100", "70")
        sel.type("persons_100", "2")
        wait_not_visible(sel,"progmessage")
        
        sel.open("/flightplan/printable?trip=test_typical")
        sel.wait_for_page_to_load("10000")
        text=sel.get_body_text()
        print text
        assert re.match(ur".*STOCKHOLM/Västerås Start:\s*09:00 Fuel:70.0L.*",text)
        arrive_hour,arrive_min,fuel=re.match(ur".*BORLÄNGE ETA:\s*(\d{2}):(\d{2})\s*Fuel left:\s*(\d+.?\d*).*",text).groups()
        assert int(arrive_hour)==10
        assert abs(int(arrive_min)-24)<=2
        fuel=float(fuel)
        expected_fuel=70-25.4
        assert abs(fuel-expected_fuel)<=0.5
        sel.open("/flightplan/index")
        sel.wait_for_page_to_load("10000")
        sel.click("link=ATS-flightplan")
        sel.wait_for_page_to_load("10000")
        
        