from typing import List

from pydantic import BaseModel

from aiotopicdb.models.attribute_model import AttributeModel
from aiotopicdb.models.basename_model import BaseNameModel
from aiotopicdb.models.member_model import MemberModel
from aiotopicdb.models.occurrence_model import OccurrenceModel

_UNIVERSAL_SCOPE = "*"


class AssociationModel(BaseModel):
    identifier: str = ""
    instance_of: str = "association"
    scope: str = _UNIVERSAL_SCOPE
    base_names: List[BaseNameModel] = []
    occurrences: List[OccurrenceModel] = []
    attributes: List[AttributeModel] = []
    member: MemberModel

    class Config:
        from_attributes = True
