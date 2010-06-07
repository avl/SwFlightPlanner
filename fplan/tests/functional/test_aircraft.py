from fplan.tests import *

class TestAircraftController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='aircraft', action='index'))
        # Test response...
