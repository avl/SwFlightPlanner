from fplan.tests import *

class TestNotamController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='notam', action='index'))
        # Test response...
