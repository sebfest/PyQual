from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Self


@dataclass
class QualtricsSurvey:
    survey_id: str
    name: str
    owner_id: str
    last_modified: datetime
    creation_date: datetime
    active: bool

    @classmethod
    def from_dict(cls, survey_dict: Dict[str, str | int | datetime | bool]) -> Self:
        return cls(
            survey_id=survey_dict['id'],
            name=survey_dict['name'],
            owner_id=survey_dict['ownerId'],
            last_modified=datetime.strptime(survey_dict['lastModified'], '%Y-%m-%dT%H:%M:%SZ'),
            creation_date=datetime.strptime(survey_dict['creationDate'], '%Y-%m-%dT%H:%M:%SZ'),
            active=survey_dict['isActive'],
        )
