from datetime import datetime, timezone
from unittest import TestCase

from pyqual.models import QualtricsSurvey


class QualtricsSurveyTestCase(TestCase):

    def test_from_dict_accepts_last_modified(self):
        survey = QualtricsSurvey.from_dict({
            "id": "SV_123",
            "name": "Test Survey",
            "ownerId": "owner",
            "lastModified": "2010-01-01T09:37:31Z",
            "creationDate": "2010-01-01T09:37:31Z",
            "isActive": True,
        })

        self.assertEqual(survey.survey_id, "SV_123")
        self.assertEqual(survey.last_modified, datetime(2010, 1, 1, 9, 37, 31, tzinfo=timezone.utc))

    def test_from_dict_accepts_last_modified_date(self):
        survey = QualtricsSurvey.from_dict({
            "id": "SV_123",
            "name": "Test Survey",
            "ownerId": "owner",
            "lastModifiedDate": "2010-01-01T09:37:31Z",
            "creationDate": datetime(2010, 1, 1, 9, 37, 31, tzinfo=timezone.utc),
            "isActive": True,
        })

        self.assertEqual(survey.creation_date, datetime(2010, 1, 1, 9, 37, 31, tzinfo=timezone.utc))
