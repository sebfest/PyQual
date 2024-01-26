from datetime import datetime
from typing import Dict, Any

from pyqual.models import QualtricsSurvey


def parse_survey(survey: Dict[str, Any]) -> QualtricsSurvey:
    return QualtricsSurvey(
        survey_id=survey['id'],
        name=survey['name'],
        owner_id=survey['ownerId'],
        last_modified=datetime.strptime(survey['lastModified'], '%Y-%m-%dT%H:%M:%SZ'),
        creation_date=datetime.strptime(survey['creationDate'], '%Y-%m-%dT%H:%M:%SZ'),
        active=survey['isActive'],
    )
