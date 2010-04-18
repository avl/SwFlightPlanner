from fplan.tests import *

class TestMapviewController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='mapview', action='index'))
        # Test response...
