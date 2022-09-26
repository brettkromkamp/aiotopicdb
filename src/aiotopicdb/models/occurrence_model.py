from typing import List

from pydantic import BaseModel

from aiotopicdb.models.language import Language
from .attribute_model import AttributeModel

_UNIVERSAL_SCOPE = "*"


class OccurrenceModel(BaseModel):
    topic_identifier: str = ""
    identifier: str = ""
    instance_of: str = "occurrence"
    scope: str = _UNIVERSAL_SCOPE
    resource_ref: str = ""
    resource_data: str | bytes | None = None
    language: Language = Language.ENG
    attributes: List[AttributeModel] = []

    class Config:
        orm_mode = True
