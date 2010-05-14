from fplan.tests import *

class TestFlightplanController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='flightplan', action='index'))
        # Test response...
