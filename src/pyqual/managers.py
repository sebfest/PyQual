import os
from typing import List

from pyqual.client import QualtricsManageSurveyClient
from pyqual.models import QualtricsSurvey


class BaseManager:
    """Base class.
        Parameters
        ----------
            data_center: str
                Qualtrics data center (e.g. fra1, ca1, ...)

        Attributes
        ----------
            _data_center
    """

    def __init__(self, data_center: str = 'fra1') -> None:
        """Create instance of BaseClient.
            Parameters
            ----------
            data_center: str
                 The Qualtrics data center to connect to.
            Returns
            -------
            None
            """
        self._data_center = data_center
        self._client = QualtricsManageSurveyClient(
            token=os.environ.get('QUALTRICS_TOKEN'),
            data_center=self._data_center
        )

    def __repr__(self) -> str:
        """Return printable representation of Client().
        Returns
        -------
        str
            String that would yield an object with the same value when passed to eval().

        """
        return f'{type(self).__name__}(datacenter={self._data_center!r})'


class QualtricsManager(BaseManager):

    def list_surveys(self, limit: int = 300) -> List[QualtricsSurvey]:
        """List all reviewable HITs from MTurk."""
        with self._client as client:
            print("Retrieving all Surveys")
            survey_list = client.get_all_surveys(limit=limit)
            surveys = [QualtricsSurvey.from_dict(survey) for survey in survey_list]
            return surveys

    def retrieve_survey(self, survey_id: str) -> QualtricsSurvey:
        """Retrieve a single survey."""
        with self._client as client:
            print(f"Retrieving Survey with id {survey_id}")
            response = client.get_survey(survey_id=survey_id)
            data = response.json()['result']

            survey = QualtricsSurvey(
                survey_id=data['id'],
                name=data['name'],
                owner_id=data['ownerId'],
                last_modified=data['lastModifiedDate'],
                creation_date=data['creationDate'],
                active=data['isActive'],
            )

            return survey
