from dataclasses import dataclass
from datetime import datetime

from typing import Dict, Any


@dataclass
class QualtricsSurvey:
    name: str
    survey_id: str
    last_modified: datetime
    active: bool


def parse_survey(survey: Dict[str, Any]) -> QualtricsSurvey:
    return QualtricsSurvey(
        name=survey['name'],
        survey_id=survey['id'],
        last_modified=datetime.strptime(survey['lastModified'], '%Y-%m-%dT%H:%M:%SZ'),
        active=survey['isActive'],
    )
