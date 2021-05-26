import unittest
import random
from src.client import BaseClient
from constants import DATA_CENTERS, BASE_URL


class BaseClientTestCase(unittest.TestCase):

    def setUp(self):
        self.test_data_center = random.choice(DATA_CENTERS)
        self.invalid_test_data_center = self.test_data_center[:-1]
        self.client = BaseClient(data_center=self.test_data_center)

    def test_init(self):

        self.assertIsInstance(self.client, BaseClient)
        self.assertIsNotNone(self.client.token)

        with self.assertRaises(ValueError) as context:
            BaseClient(data_center=self.invalid_test_data_center)
            self.assertTrue(f'{self.test_data_center} not a valid datacenter.' in context.exception)

    def test_client_connect(self):
        self.assertEqual(self.client.base_url, BASE_URL.format(self.test_data_center))


if __name__ == '__main__':
    unittest.main()
