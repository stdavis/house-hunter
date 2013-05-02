import unittest, os, sys
from mock import Mock

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../..')
import houseHunter

email = 'test@test.com'
password = 'password'


class initTests(unittest.TestCase):
    def tearDown(self):
        self.testObject = None

    def test_mixinParams(self):
        self.testObject = houseHunter.Hunter(email, password)

        assert self.testObject.email == email
        assert self.testObject.password == password


class startSearch(unittest.TestCase):
    def setUp(self):
        self.testObject = houseHunter.Hunter(email, password)

    def test_call_search(self):
        self.testObject.maxSearches = 2
        self.testObject.search = Mock()

        self.testObject.startSearch()
        self.testObject.keepSearching = False

        self.testObject.search.assert_called_once_with()