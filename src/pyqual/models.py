from dataclasses import dataclass
from datetime import datetime


@dataclass
class QualtricsSurvey:
    survey_id: str
    name: str
    owner_id: str
    last_modified: datetime
    creation_date: datetime
    active: bool
