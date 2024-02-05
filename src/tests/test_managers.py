import os
from unittest import TestCase, mock

from pyqual.constants import DATA_CENTERS
from pyqual.exceptions import InvalidDataCenterError
from pyqual.managers import BaseManager


class BaseClientTestCase(TestCase):

    @mock.patch.dict(os.environ, {"QUALTRICS_TOKEN": "ABCDEFG"})
    def setUp(self):
        self.invalid_test_data_center = 'ABCD'
        self.manager = BaseManager()

    def test_init(self):
        self.assertIsInstance(self.manager, BaseManager)
        self.assertIsNotNone(self.manager._data_center)

    def test_valid_data_center(self):
        self.assertTrue(self.manager._data_center in DATA_CENTERS)

    def test_invalid_data_center(self):
        with self.assertRaises(InvalidDataCenterError) as context:
            BaseManager(data_center=self.invalid_test_data_center)
            self.assertTrue(f'{self.invalid_test_data_center} not a valid datacenter.' in context.exception)
