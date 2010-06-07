from fplan.tests import *

class TestSplashController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='splash', action='index'))
        # Test response...
