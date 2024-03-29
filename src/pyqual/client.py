import io
import os
import zipfile
from typing import List, Dict, Any
from urllib.parse import urlparse, parse_qs

import requests
from requests import HTTPError, Timeout
from requests.adapters import HTTPAdapter

from pyqual.constants import (
    BASE_URL,
    ENDPOINTS,
    DATA_CENTERS,
    FILE_EXTENSION,
    PAGE_SIZE
)
from pyqual.exceptions import (
    ExportFailureError,
    MissingApiTokenError,
    InvalidDataCenterError, MinimumSurveyCountError,
)


class BaseClient:
    """Base class.
    Parameters
    ----------
        token: str
            Qualtrics API token.
        data_center:
            Qualtrics data center (e.g. fra1, ca1, ...)

    Attributes
    ----------
    token
    data_center
    """

    def __init__(
            self,
            token: str = '',
            data_center: str = '',
            retry: int = 3,
            timeout: int = 10,
            stream: bool = True,
    ):
        """Create instance of BaseClient.
        Parameters
        ----------
        token: str
             The secret Qualtrics access token.
        data_center: str
             The Qualtrics data center to connect to.
        retry : int
            Number of request retry attempts.
        timeout : int
            Number of seconds before connection timeouts.

        Returns
        -------
        None
        """

        if data_center not in DATA_CENTERS:
            raise InvalidDataCenterError(f'{data_center} not a valid datacenter')

        if not token:
            try:
                token = os.environ['QUALTRICS_TOKEN']
            except KeyError:
                raise MissingApiTokenError("No qualtrics token provided.")

        self.token = token
        self.data_center = data_center
        self.retry = retry
        self.timeout = timeout
        self.stream = stream
        self.session = self._get_session()

    @property
    def base_url(self) -> str:
        """Return URL endpoint client is connected to.
        Returns
        -------
            str
                URL for the endpoint.

        """
        return BASE_URL.format(self.data_center)

    def __enter__(self):
        """Returns class object for context manager.
        Returns
        -------
        class:`Client`
            A client.

        """
        return self

    def __exit__(self, *args):
        """Closes the session adapters.
        Returns
        -------
            None

        """
        self.session.__exit__(*args)
        self.session = None

    def __str__(self):
        """Return name of Client() class for users.
        Returns
        -------
            str
                Naming of the API class.

        """
        return f'Qualtrics client {self.base_url}'

    def __repr__(self):
        """Return printable representation of Client().
        Returns
        -------
        str
            String that would yield an object with the same value when passed to eval().

        """
        return f'{self.__class__.__name__}()'

    def _get_session(self) -> requests.Session:
        """Return session that client uses for connecting to endpoint.
        Returns
        -------
        class:`requests.Response`
            Response object of requests library.

        """
        session = requests.Session()

        headers = {
            "x-api-token": self.token,
            "content-type": None,  # "application/json"
        }

        if self.token:
            session.headers.update(headers)

        if self.retry > 1:
            adapter = HTTPAdapter(max_retries=self.retry)
            session.mount(self.base_url, adapter)

        if self.stream:
            session.stream = True

        return session

    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make a generic request.
        Parameters
        ----------
        method: str
             The HTTP verb for the request.
        url : str
            Full URL.
        Returns
        -------
        class:`requests.Response`
            Response object of requests library.

        """
        try:
            response = self.session.request(method, url, timeout=self.timeout, **kwargs)
            response.raise_for_status()
        except HTTPError as http_error:
            error_msg = http_error.response.json()['meta']['error']['errorMessage']
            raise HTTPError(f'HTTP error occurred. {error_msg}') from http_error
        except ConnectionError as connection_error:
            raise ConnectionError(f'Could not establish connection to {url}. Reason {connection_error}')
        except Timeout as timeout_error:
            raise Timeout(f'Failed to receive response from {url}. Reason {timeout_error}')
        except Exception as error:
            print(f'An unknown error occurred: {error}')
            raise
        else:
            return response


class QualtricsResponseExportClient(BaseClient):

    def get_available_filters(self, survey_id: str) -> requests.Response:
        """Get all filters for survey.
        Parameters
        ----------
        survey_id: str
             The id for the survey.
        Returns
        -------
        class:`requests.Response`
            Response object of requests library.

        """
        service_url = ENDPOINTS.get('filters').format(survey_id)
        full_url = self.base_url + service_url
        return self._make_request(method='GET', url=full_url)

    def start_response_export(self, survey_id: str, file_format: str, filter_id: str = None,
                              body: Dict = None) -> requests.Response:
        """Starts an export of a survey's responses.
        Parameters
        ----------
        survey_id: str
             The id for the survey.
        file_format: str
            The file format for data export.
        filter_id: str
            The survey filter id.
        body: dict
            Optional fields to modify the export.
        Returns
        -------
        class:`requests.Response`
            Response object of requests library.

        """
        service_url = ENDPOINTS.get('export').format(survey_id)
        full_url = self.base_url + service_url

        if file_format not in FILE_EXTENSION:
            raise ValueError('Unsupported file format')

        data = {'format': file_format}
        if filter_id is not None:
            data['filterId'] = filter_id

        if body is not None:
            data.update((key, value) for key, value in body.items() if key not in data)

        return self._make_request('POST', url=full_url, json=data)

    def get_response_export_progress(self):
        pass

    def get_response_export_file(self):
        pass

    def export_survey(self, survey_id: str, file_format: str, filter_id: str = None, *args, **kwargs):

        export_response = self.start_response_export(survey_id, file_format, filter_id)
        progress_id = export_response.json()["result"]["progressId"]

        # Get Response Export Progress
        service_url = ENDPOINTS.get('export').format(survey_id)
        full_url = self.base_url + service_url

        check_response = None
        progress_status = "inProgress"
        while progress_status != "complete" and progress_status != "failed":
            check_url = full_url + progress_id
            check_response = self._make_request('GET', url=check_url)
            request_progress = check_response.json()["result"]["percentComplete"]
            print("Download is " + str(request_progress) + "% complete")
            progress_status = check_response.json()["result"]["status"]

            if "failed" in progress_status:
                raise ExportFailureError("Export failed")

        # Get Response Export File
        if check_response:
            file_id = check_response.json()["result"]["fileId"]
            download_url = full_url + file_id + '/file'
            download_response = self._make_request('GET', url=download_url)

            zipfile.ZipFile(io.BytesIO(download_response.content)).extractall("MyQualtricsDownload")
            print('Download complete')


class QualtricsManageSurveyClient(BaseClient):

    def get_all_surveys(self, limit: int = 500) -> List[Dict[str, Any]]:
        if limit < 100:
            raise MinimumSurveyCountError('Limit must be no less than 100')

        service_url = ENDPOINTS.get('surveys')
        full_url = self.base_url + service_url

        print(f'Downloading page 1.')
        response = self._make_request(method='GET', url=full_url)
        json_response = response.json()

        survey_list = []
        surveys = [survey for survey in json_response['result']['elements']]
        survey_list.extend(surveys)

        if limit <= 100:
            return survey_list

        while next_page := json_response['result']['nextPage']:
            parsed_url = urlparse(next_page)
            query_strings = parse_qs(parsed_url.query)

            offset = int(query_strings.get('offset').pop())
            if offset > limit:
                break

            page = (offset // PAGE_SIZE) + 1
            print(f'Downloading page {page}.')

            response = self._make_request(method='GET', url=full_url, params={'offset': offset})
            json_response = response.json()

            surveys = [survey for survey in json_response['result']['elements']]
            survey_list.extend(surveys)

        return survey_list

    def get_survey(self, survey_id: str) -> requests.Response:
        service_url = ENDPOINTS.get('get_survey').format(survey_id)
        full_url = self.base_url + service_url
        return self._make_request(method='GET', url=full_url)

    def deactivate_survey(self, survey_id: str) -> requests.Response:
        service_url = ENDPOINTS.get('get_survey').format(survey_id)
        full_url = self.base_url + service_url
        data = {"isActive": False}

        print(f'Deactivating survey {survey_id}')
        response = self._make_request('PUT', url=full_url, json=data)

        if response.status_code == requests.codes.ok:
            print('Survey deactivated.')

        return response

    def get_dir(self) -> requests.Response:
        service_url = ENDPOINTS.get('directories')
        full_url = self.base_url + service_url
        return self._make_request(method='GET', url=full_url)

    def delete_survey(self, survey_id: str) -> requests.Response:
        service_url = ENDPOINTS.get('get_survey').format(survey_id)
        full_url = self.base_url + service_url

        print(f'Deleting survey {survey_id}')
        response = self._make_request('DELETE', url=full_url)

        if response.status_code == requests.codes.ok:
            print('Survey deactivated.')

        return response
