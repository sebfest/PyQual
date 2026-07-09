from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping


def _parse_qualtrics_datetime(value: datetime | str) -> datetime:
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str):
        raise TypeError(f"Expected datetime or ISO datetime string, got {type(value).__name__}")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _get_first_present(mapping: Mapping[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in mapping:
            return mapping[key]
    raise KeyError(keys[0])


@dataclass
class QualtricsSurvey:
    survey_id: str
    name: str
    owner_id: str
    last_modified: datetime
    creation_date: datetime
    active: bool

    @classmethod
    def from_dict(cls, survey_dict: Mapping[str, Any]) -> QualtricsSurvey:
        last_modified = _get_first_present(survey_dict, ("lastModified", "lastModifiedDate"))

        return cls(
            survey_id=survey_dict['id'],
            name=survey_dict['name'],
            owner_id=survey_dict['ownerId'],
            last_modified=_parse_qualtrics_datetime(last_modified),
            creation_date=_parse_qualtrics_datetime(survey_dict['creationDate']),
            active=survey_dict['isActive'],
        )
