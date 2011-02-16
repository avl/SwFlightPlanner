#encoding=utf8
from selenium import selenium
import unittest, time, re

class test_subzero_gs(unittest.TestCase):
    def setUp(self):
        self.verificationErrors = []
        self.selenium = selenium("localhost", 4444, "*chrome", "http://localhost:5000/")
        self.selenium.start()
    
    def test_test_subzero_gs(self):
        sel = self.selenium
        sel.open("/")
        sel.type("username", "ank")
        sel.type("password", "ank")
        sel.click("login")
        sel.wait_for_page_to_load("30000")
        sel.click("//button[@onclick='more_trip_functions();return false;']")
        sel.click("//button[@onclick='open_trip();return false;']")
        sel.click("//button[@onclick='add_new_trip();return false;']")
        sel.type("addtripname", "test_headwind")
        sel.click("//button[@onclick='on_add_trip();return false;']")
        sel.wait_for_page_to_load("30000")
        sel.type("searchfield", u"frölund")
        sel.type_keys("searchfield", "a")
        for i in range(60):
            try:
                if sel.is_visible("searchpopup"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        for i in range(60):
            try:
                if not sel.is_visible("searchprogtext"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.click("//p[@onclick='search_select(0)']")
        sel.type("searchfield", u"Stockholm/Västerå")
        sel.type_keys("searchfield", "s")
        for i in range(60):
            try:
                if sel.is_visible("searchpopup"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        for i in range(60):
            try:
                if not sel.is_visible("searchprogtext"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.click("//p[@onclick='search_select(0)']")
        sel.click("link=Flightplan")
        sel.wait_for_page_to_load("30000")
        sel.type_keys("fplanrow100W", "270")
        sel.type_keys("fplanrow100V", "80")
        sel.type("fuel_100", "70")
        sel.type("persons_100", "2")
        for i in range(60):
            try:
                if not sel.is_visible("progmessage"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.open("/flightplan/printable?trip=test_headwind")
        bt=sel.get_body_text()
        self.failUnless(re.search(ur"^[\s\S]*EXPECTED HEADWIND IS GREATER THAN TAS![\s\S]*$", bt))
        self.failUnless(re.search(ur"^[\s\S]*Frölunda[\s\S]*$", bt))
        self.failUnless(re.search(ur"^[\s\S]*Västerås[\s\S]*$", bt))
        sel.open("/mapview/index")
        sel.click("//button[@onclick='more_trip_functions();return false;']")
        sel.click("//button[@onclick='open_trip();return false;']")
        sel.click("//button[@onclick='more_trip_functions();return false;']")
        sel.click("//button[@onclick='on_delete_trip();return false;']")
        sel.wait_for_page_to_load("30000")
    
    def tearDown(self):
        self.selenium.stop()
        self.assertEqual([], self.verificationErrors)

if __name__ == "__main__":
    unittest.main()
