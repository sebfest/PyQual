import unittest
import random
from src.client import BaseClient
from constants import DATA_CENTERS, BASE_URL

class BaseClientTestCase(unittest.TestCase):

    def setUp(self):
        self.test_data_center = random.choice(DATA_CENTERS)
        self.client = BaseClient(data_center=self.test_data_center)

    def test_client_connect(self):

        assert isinstance(self.client, BaseClient)
        assert self.client.token
        #assert self.client.api_version == "v1"
        assert self.client.base_url == BASE_URL.format(self.test_data_center)


if __name__ == '__main__':
    unittest.main()
