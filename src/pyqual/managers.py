from typing import List

from pyqual.client import QualtricsManageSurveyClient
from pyqual.models import QualtricsSurvey


class BaseManager:

    def __init__(self, data_center: str = 'fra') -> None:
        self._data_center = data_center
        self._client = QualtricsManageSurveyClient(data_center=data_center)

    def __repr__(self) -> str:
        return f'{type(self).__name__}(datacenter={self._data_center!r})'


class QualtricsManager(BaseManager):

    def list_surveys(self, limit: int = 300) -> List[QualtricsSurvey]:
        """List all reviewable HITs from MTurk."""
        with self._client as client:
            print("Retrieving all Surveys")
            survey_list = client.get_all_surveys(limit=limit)
            surveys = [QualtricsSurvey.from_dict(survey) for survey in survey_list]
            return surveys
