import io
import os
import time
import zipfile
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlparse, parse_qs

import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import HTTPError, Timeout

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
    InvalidDataCenterError,
    MinimumSurveyCountError,
)


def _extract_error_message(response: requests.Response | None) -> str:
    if response is None:
        return "Unknown HTTP error"

    try:
        payload = response.json()
    except ValueError:
        payload = {}

    try:
        return payload["meta"]["error"]["errorMessage"]
    except (KeyError, TypeError):
        pass

    text = getattr(response, "text", "")
    if isinstance(text, str) and text:
        return text

    content = getattr(response, "content", "")
    if isinstance(content, bytes):
        return content.decode(errors="replace")
    if isinstance(content, str) and content:
        return content

    status_code = getattr(response, "status_code", "unknown")
    return f"HTTP status {status_code}"


def _next_page_offset(next_page: str | None) -> int | None:
    if not next_page or next_page == "null":
        return None

    parsed_url = urlparse(next_page)
    query_strings = parse_qs(parsed_url.query)
    offsets = query_strings.get("offset")
    if not offsets:
        return None

    try:
        return int(offsets[-1])
    except ValueError:
        return None


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
            data_center: str = 'fra1',
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
        if self.session is not None:
            self.session.close()
            self.session = None
        return False

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

        if self.token:
            session.headers.update({"X-API-TOKEN": self.token})

        if self.retry > 1:
            adapter = HTTPAdapter(max_retries=self.retry)
            session.mount(self.base_url, adapter)

        return session

    def _build_url(self, endpoint: str) -> str:
        """Return a URL under the Qualtrics API base path."""
        return f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"

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
            kwargs.setdefault("stream", self.stream)
            response = self.session.request(method, url, timeout=self.timeout, **kwargs)
            response.raise_for_status()
        except HTTPError as http_error:
            error_msg = _extract_error_message(http_error.response)
            raise HTTPError(f'HTTP error occurred. {error_msg}') from http_error
        except RequestsConnectionError as connection_error:
            raise RequestsConnectionError(f'Could not establish connection to {url}. Reason {connection_error}')
        except Timeout as timeout_error:
            raise Timeout(f'Failed to receive response from {url}. Reason {timeout_error}')
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
        full_url = self._build_url(service_url)
        return self._make_request(method='GET', url=full_url)

    def start_response_export(self, survey_id: str, file_format: str, filter_id: str = None,
                              body: Dict[str, Any] = None) -> requests.Response:
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
        full_url = self._build_url(service_url)

        if file_format not in FILE_EXTENSION:
            raise ValueError('Unsupported file format')

        data = {'format': file_format}
        if filter_id is not None:
            data['filterId'] = filter_id

        if body is not None:
            data.update((key, value) for key, value in body.items() if key not in data)

        return self._make_request('POST', url=full_url, json=data)

    def get_response_export_progress(self, survey_id: str, progress_id: str) -> requests.Response:
        """Get the progress for a response export job."""
        service_url = ENDPOINTS.get('export_progress').format(survey_id, progress_id)
        full_url = self._build_url(service_url)
        return self._make_request('GET', url=full_url)

    def get_response_export_file(self, survey_id: str, file_id: str) -> requests.Response:
        """Download the completed response export file."""
        service_url = ENDPOINTS.get('export_file').format(survey_id, file_id)
        full_url = self._build_url(service_url)
        return self._make_request('GET', url=full_url)

    def export_survey(
            self,
            survey_id: str,
            file_format: str,
            filter_id: str = None,
            body: Dict[str, Any] = None,
            output_dir: str | os.PathLike[str] = "MyQualtricsDownload",
            max_polls: int = 120,
            poll_interval: float = 1.0,
    ) -> Path:

        export_response = self.start_response_export(survey_id, file_format, filter_id, body=body)
        progress_id = export_response.json()["result"]["progressId"]

        for _ in range(max_polls):
            check_response = self.get_response_export_progress(survey_id, progress_id)
            result = check_response.json()["result"]
            progress_status = result["status"]
            request_progress = result.get("percentComplete")

            if request_progress is not None:
                print("Download is " + str(request_progress) + "% complete")

            if progress_status == "failed":
                raise ExportFailureError("Export failed")

            if progress_status == "complete":
                file_id = result["fileId"]
                download_response = self.get_response_export_file(survey_id, file_id)
                output_path = self._extract_export(download_response.content, output_dir)
                print('Download complete')
                return output_path

            time.sleep(poll_interval)

        raise ExportFailureError(f"Export did not complete after {max_polls} checks")

    @staticmethod
    def _extract_export(content: bytes, output_dir: str | os.PathLike[str]) -> Path:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        root = output_path.resolve()

        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            for member in archive.infolist():
                target = (root / member.filename).resolve()
                if target != root and root not in target.parents:
                    raise ExportFailureError(f"Unsafe path in export archive: {member.filename}")

            archive.extractall(root)

        return output_path


class QualtricsManageSurveyClient(BaseClient):

    def get_all_surveys(self, limit: int = 500) -> List[Dict[str, Any]]:
        if limit < 100:
            raise MinimumSurveyCountError('Limit must be no less than 100')

        service_url = ENDPOINTS.get('surveys')
        full_url = self._build_url(service_url)

        print(f'Downloading page 1.')
        response = self._make_request(method='GET', url=full_url)
        json_response = response.json()

        survey_list = []
        survey_list.extend(json_response['result']['elements'])

        if len(survey_list) >= limit:
            return survey_list[:limit]

        while True:
            offset = _next_page_offset(json_response['result'].get('nextPage'))
            if offset is None or offset >= limit:
                break

            page = (offset // PAGE_SIZE) + 1
            print(f'Downloading page {page}.')

            response = self._make_request(method='GET', url=full_url, params={'offset': offset})
            json_response = response.json()

            survey_list.extend(json_response['result']['elements'])

            if len(survey_list) >= limit:
                return survey_list[:limit]

        return survey_list

    def get_survey(self, survey_id: str) -> requests.Response:
        service_url = ENDPOINTS.get('get_survey').format(survey_id)
        full_url = self._build_url(service_url)
        return self._make_request(method='GET', url=full_url)

    def deactivate_survey(self, survey_id: str) -> requests.Response:
        service_url = ENDPOINTS.get('get_survey').format(survey_id)
        full_url = self._build_url(service_url)
        data = {"isActive": False}

        print(f'Deactivating survey {survey_id}')
        response = self._make_request('PUT', url=full_url, json=data)

        if response.status_code == requests.codes.ok:
            print('Survey deactivated.')

        return response

    def get_dir(self) -> requests.Response:
        service_url = ENDPOINTS.get('directories')
        full_url = self._build_url(service_url)
        return self._make_request(method='GET', url=full_url)

    def delete_survey(self, survey_id: str) -> requests.Response:
        service_url = ENDPOINTS.get('get_survey').format(survey_id)
        full_url = self._build_url(service_url)

        print(f'Deleting survey {survey_id}')
        response = self._make_request('DELETE', url=full_url)

        if response.status_code == requests.codes.ok:
            print('Survey deactivated.')

        return response
