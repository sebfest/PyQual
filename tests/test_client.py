import io
import os
import random
import tempfile
import zipfile
from pathlib import Path
from unittest import TestCase, main, mock

from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import Timeout, HTTPError

from pyqual.client import BaseClient, QualtricsManageSurveyClient, QualtricsResponseExportClient
from pyqual.constants import DATA_CENTERS, BASE_URL
from pyqual.exceptions import ExportFailureError, InvalidDataCenterError, MinimumSurveyCountError


def _response(payload=None, content=b"", status_code=200):
    response = mock.Mock(status_code=status_code, content=content)
    if payload is not None:
        response.json.return_value = payload
    return response


def _survey(index):
    return {
        "id": f"SV_{index}",
        "name": f"Survey {index}",
        "ownerId": "owner",
        "lastModified": "2010-01-01T09:37:31Z",
        "creationDate": "2010-01-01T09:37:31Z",
        "isActive": True,
    }


class BaseClientTestCase(TestCase):

    def setUp(self):
        self.test_data_center = random.choice(DATA_CENTERS)
        self.invalid_test_data_center = self.test_data_center[:-1]
        self.test_token = 'ABCEDEFGH'
        self.client = BaseClient(token=self.test_token, data_center=self.test_data_center)

    def test_init(self):
        self.assertIsInstance(self.client, BaseClient)
        self.assertIsInstance(self.client.token, str)
        self.assertIsInstance(self.client.data_center, str)
        self.assertIsNotNone(self.client.retry)
        self.assertIsNotNone(self.client.timeout)
        self.assertIsNotNone(self.client.stream)

    def test_init_uses_default_data_center(self):
        client = BaseClient(token=self.test_token)

        self.assertEqual(client.data_center, 'fra1')

    @mock.patch.dict(os.environ, {"QUALTRICS_TOKEN": "ABCDEFG"})
    def test_init_from_environment(self):
        BaseClient(data_center=self.test_data_center)

    @mock.patch.dict(os.environ, {"QUALTRICS_TOKEN": "ABCDEFG"})
    def test_init_from_environment_with_invalid_data_center(self):
        with self.assertRaises(InvalidDataCenterError) as context:
            BaseClient(data_center=self.invalid_test_data_center)
            self.assertTrue(f'{self.test_data_center} not a valid datacenter.' in context.exception)

    def test_invalid_data_center(self):
        with self.assertRaises(InvalidDataCenterError) as context:
            BaseClient(self.test_token, data_center=self.invalid_test_data_center)
            self.assertTrue(f'{self.test_data_center} not a valid datacenter.' in context.exception)

    def test_client_url(self):
        self.assertEqual(self.client.base_url, BASE_URL.format(self.test_data_center))

    def test_build_url_normalizes_slashes(self):
        self.assertEqual(
            self.client._build_url('/surveys/SV_123/filters'),
            f'{self.client.base_url}surveys/SV_123/filters',
        )

    def test_session_sets_api_token_without_invalid_content_type(self):
        headers = {key.lower(): value for key, value in self.client.session.headers.items()}

        self.assertEqual(headers['x-api-token'], self.test_token)
        self.assertNotIn('content-type', headers)

    @mock.patch("pyqual.client.requests.Session.request")
    def test_request_uses_timeout_and_stream_default(self, mock_request):
        mock_response = _response()
        mock_request.return_value = mock_response

        response = self.client._make_request(method='GET', url='www.test.com')

        self.assertEqual(response, mock_response)
        mock_request.assert_called_once_with('GET', 'www.test.com', timeout=self.client.timeout, stream=True)
        mock_response.raise_for_status.assert_called_once()

    @mock.patch("pyqual.client.requests.Session.request")
    def test_request_timeout(self, mock_request):
        mock_request.side_effect = Timeout
        with self.assertRaises(Timeout):
            self.client._make_request(method='GET', url='www.test.com')
            mock_request.get.assert_called_once()

    @mock.patch("pyqual.client.requests.Session.request")
    def test_request_connection_error(self, mock_request):
        mock_request.side_effect = RequestsConnectionError

        with self.assertRaises(RequestsConnectionError):
            self.client._make_request(method='GET', url='www.test.com')

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

        with self.assertRaises(HTTPError) as context:
            self.client._make_request(method='GET', url='www.test.com')
            mock_request.get.assert_called_once()

        self.assertIn('Error', str(context.exception))

    @mock.patch("pyqual.client.requests.Session.request")
    def test_request_http_error_falls_back_to_response_content(self, mock_request):
        mock_response = mock.Mock(status_code=500, content='Server is down')
        mock_response.json.side_effect = ValueError
        mock_request.side_effect = HTTPError(response=mock_response)

        with self.assertRaises(HTTPError) as context:
            self.client._make_request(method='GET', url='www.test.com')

        self.assertIn('Server is down', str(context.exception))


class QualtricsResponseExportClientTestCase(TestCase):

    def setUp(self) -> None:
        self.test_token = 'ABCEDEFGH'
        self.client = QualtricsResponseExportClient(token=self.test_token, data_center=random.choice(DATA_CENTERS))

    @mock.patch("pyqual.client.requests.Session.request")
    def test_get_available_filters(self, mock_request):
        mock_response = _response({
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
        })
        mock_request.return_value = mock_response

        response = self.client.get_available_filters(survey_id='foobar')
        self.assertEqual(response.status_code, 200)
        mock_request.assert_called_once_with(
            'GET',
            f'{self.client.base_url}surveys/foobar/filters',
            timeout=self.client.timeout,
            stream=True,
        )

        filter_data = response.json()["result"]['elements']
        self.assertEqual(filter_data[0]["filterId"], "fecb8b08-a920-4e28-b5ce-d67a1ef67a39")

    @mock.patch.object(QualtricsResponseExportClient, "_make_request")
    def test_export_survey_downloads_and_extracts_zip(self, mock_make_request):
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, "w") as zip_archive:
            zip_archive.writestr("responses.csv", "id,value\n1,ok\n")

        mock_make_request.side_effect = [
            _response({"result": {"progressId": "progress-1"}}),
            _response({"result": {"status": "complete", "percentComplete": 100, "fileId": "file-1"}}),
            _response(content=archive.getvalue()),
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "download"

            result = self.client.export_survey(
                survey_id='SV_123',
                file_format='csv',
                output_dir=output_dir,
                poll_interval=0,
            )

            self.assertEqual(result, output_dir)
            self.assertEqual((output_dir / "responses.csv").read_text(), "id,value\n1,ok\n")

        mock_make_request.assert_has_calls([
            mock.call('POST', url=f'{self.client.base_url}surveys/SV_123/export-responses/', json={'format': 'csv'}),
            mock.call('GET', url=f'{self.client.base_url}surveys/SV_123/export-responses/progress-1'),
            mock.call('GET', url=f'{self.client.base_url}surveys/SV_123/export-responses/file-1/file'),
        ])

    def test_extract_export_rejects_unsafe_paths(self):
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, "w") as zip_archive:
            zip_archive.writestr("../escape.csv", "bad")

        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(ExportFailureError):
                self.client._extract_export(archive.getvalue(), temp_dir)


class QualtricsManageSurveyClientTestCase(TestCase):

    def setUp(self) -> None:
        self.test_token = 'ABCEDEFGH'
        self.client = QualtricsManageSurveyClient(token=self.test_token, data_center=random.choice(DATA_CENTERS))

    def test_get_all_surveys_rejects_limits_under_page_size(self):
        with self.assertRaises(MinimumSurveyCountError):
            self.client.get_all_surveys(limit=99)

    @mock.patch("pyqual.client.requests.Session.request")
    def test_get_all_surveys_caps_results_at_limit(self, mock_request):
        first_page = _response({
            "result": {
                "elements": [_survey(index) for index in range(100)],
                "nextPage": f"{self.client.base_url}surveys?offset=100",
            }
        })
        second_page = _response({
            "result": {
                "elements": [_survey(index) for index in range(100, 200)],
                "nextPage": "null",
            }
        })
        mock_request.side_effect = [first_page, second_page]

        surveys = self.client.get_all_surveys(limit=150)

        self.assertEqual(len(surveys), 150)
        self.assertEqual(surveys[-1]["id"], "SV_149")

    @mock.patch("pyqual.client.requests.Session.request")
    def test_get_all_surveys_handles_null_next_page(self, mock_request):
        mock_request.return_value = _response({
            "result": {
                "elements": [_survey(index) for index in range(100)],
                "nextPage": "null",
            }
        })

        surveys = self.client.get_all_surveys(limit=500)

        self.assertEqual(len(surveys), 100)


if __name__ == '__main__':
    main()
