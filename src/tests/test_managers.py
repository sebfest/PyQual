import os
from unittest import TestCase, mock

from pyqual.managers import BaseManager


@mock.patch.dict(os.environ, {"QUALTRICS_TOKEN": "ABCDEFG"})
class BaseClientTestCase(TestCase):

    def setUp(self):
        self.manager = BaseManager()

    def test_init(self):
        self.assertIsInstance(self.manager, BaseManager)

    def test_valid_data_center(self):
        pass

    def test_invalid_data_center(self):
        pass

    def test_valid_token(self):
        pass
