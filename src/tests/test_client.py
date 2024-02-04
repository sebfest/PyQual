import random
from unittest import TestCase, main, mock

from requests.exceptions import Timeout, HTTPError

from pyqual.client import BaseClient, QualtricsResponseExportClient
from pyqual.constants import DATA_CENTERS, BASE_URL


class BaseClientTestCase(TestCase):

    def setUp(self):
        self.test_data_center = random.choice(DATA_CENTERS)
        self.invalid_test_data_center = self.test_data_center[:-1]
        self.test_token = 'ABCEDEFGH'
        self.client = BaseClient(token=self.test_token, data_center=self.test_data_center)

    def test_init(self):
        self.assertIsInstance(self.client, BaseClient)
        self.assertIsNotNone(self.client.token)

        with self.assertRaises(ValueError) as context:
            BaseClient(self.test_token, data_center=self.invalid_test_data_center)
            self.assertTrue(f'{self.test_data_center} not a valid datacenter.' in context.exception)

    def test_client_url(self):
        self.assertEqual(self.client.base_url, BASE_URL.format(self.test_data_center))

    @mock.patch("pyqual.client.requests.Session.request")
    def test_request_timeout(self, mock_request):
        mock_request.side_effect = Timeout
        with self.assertRaises(Timeout):
            self.client._make_request(method='GET', url='www.test.com')
            mock_request.get.assert_called_once()

    @mock.patch("pyqual.client.requests.Session.request")
    def test_request_http_error(self, mock_request):
        mock_response = mock.Mock()
        mock_response.status_code = 404
        mock_response.content = 'Error Code 404'
        mock_response.json.return_value = {
            "meta": {
                "error": {
                    'errorMessage': 'Error',
                }
            }
        }
        error = HTTPError(response=mock_response)
        mock_request.side_effect = error

        with self.assertRaises(HTTPError):
            self.client._make_request(method='GET', url='www.test.com')
            mock_request.get.assert_called_once()


class QualtricsResponseExportClientTestCase(TestCase):

    def setUp(self) -> None:
        self.test_token = 'ABCEDEFGH'
        self.client = QualtricsResponseExportClient(token=self.test_token, data_center=random.choice(DATA_CENTERS))

    @mock.patch("pyqual.client.requests.Session.request")
    def test_get_available_filters(self, mock_request):
        mock_response = mock.Mock(status_code=200)
        mock_response.json.return_value = {
            "result": {
                "elements": [
                    {
                        "filterId": "fecb8b08-a920-4e28-b5ce-d67a1ef67a39",
                        "filterName": "Only survey responses from detractors",
                        "creationDate": "2010-01-05T03:37:31Z"
                    },
                    {
                        "filterId": "df946afa-2acd-4f48-b0df-34b290479819",
                        "filterName": "Only survey responses from promoters",
                        "creationDate": "2010-01-01T09:37:31Z"
                    }
                ],
                "nextPage": 'null'
            },
            "meta": {
                "requestId": "900df19-75fd-479d-b4c2-6fd1f4b7b3e0",
                "httpStatus": "200"
            }
        }
        mock_request.return_value = mock_response

        response = self.client.get_available_filters(survey_id='foobar')
        self.assertEqual(response.status_code, 200)

        filter_data = response.json()["result"]['elements']
        self.assertEqual(filter_data[0]["filterId"], "fecb8b08-a920-4e28-b5ce-d67a1ef67a39")


if __name__ == '__main__':
    main()
