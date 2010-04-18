from fplan.tests import *

class TestMaptileController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='maptile', action='index'))
        # Test response...
