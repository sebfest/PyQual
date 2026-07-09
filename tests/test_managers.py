import os
from unittest import TestCase, mock

from pyqual.constants import DATA_CENTERS
from pyqual.exceptions import InvalidDataCenterError
from pyqual.managers import BaseManager, QualtricsManager


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


class QualtricsManagerTestCase(TestCase):

    @mock.patch.dict(os.environ, {"QUALTRICS_TOKEN": "ABCDEFG"})
    def setUp(self):
        self.manager = QualtricsManager()
        self.client = mock.Mock()
        self.context_client = mock.Mock()
        self.client.__enter__ = mock.Mock(return_value=self.context_client)
        self.client.__exit__ = mock.Mock(return_value=False)
        self.manager._client = self.client

    def test_deactivate_survey(self):
        response = mock.Mock(status_code=200)
        self.context_client.deactivate_survey.return_value = response

        result = self.manager.deactivate_survey("SV_123")

        self.assertEqual(result, response)
        self.context_client.deactivate_survey.assert_called_once_with(survey_id="SV_123")
        self.client.__exit__.assert_called_once()

    def test_activate_survey(self):
        response = mock.Mock(status_code=200)
        self.context_client.activate_survey.return_value = response

        result = self.manager.activate_survey("SV_123")

        self.assertEqual(result, response)
        self.context_client.activate_survey.assert_called_once_with(survey_id="SV_123")
        self.client.__exit__.assert_called_once()

    def test_delete_survey(self):
        response = mock.Mock(status_code=200)
        self.context_client.delete_survey.return_value = response

        result = self.manager.delete_survey("SV_123")

        self.assertEqual(result, response)
        self.context_client.delete_survey.assert_called_once_with(survey_id="SV_123")
        self.client.__exit__.assert_called_once()
