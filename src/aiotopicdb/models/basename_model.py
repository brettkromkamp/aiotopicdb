from pydantic import BaseModel

from aiotopicdb.models.language import Language

_UNIVERSAL_SCOPE = "*"


class BaseNameModel(BaseModel):
    name: str
    scope: str = _UNIVERSAL_SCOPE
    language: Language = Language.ENG

    class Config:
        from_attributes = True
