from pydantic import BaseModel

from aiotopicdb.models.datatype import DataType
from aiotopicdb.models.language import Language

_UNIVERSAL_SCOPE = "*"


class AttributeModel(BaseModel):
    name: str
    value: str
    entity_identifier: str
    identifier: str = ""
    data_type: DataType = DataType.STRING
    scope: str = _UNIVERSAL_SCOPE
    language: Language = Language.ENG

    class Config:
        from_attributes = True
