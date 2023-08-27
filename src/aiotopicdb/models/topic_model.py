from typing import List

from pydantic import BaseModel

from aiotopicdb.models.attribute_model import AttributeModel
from aiotopicdb.models.basename_model import BaseNameModel
from aiotopicdb.models.language import Language
from aiotopicdb.models.occurrence_model import OccurrenceModel

_UNIVERSAL_SCOPE = "*"


class TopicModel(BaseModel):
    identifier: str = ""
    instance_of: str = "topic"
    base_names: List[BaseNameModel] = []
    occurrences: List[OccurrenceModel] = []
    attributes: List[AttributeModel] = []

    @property
    def first_base_name(self) -> BaseNameModel:
        if len(self.base_names) > 0:
            result = self.base_names[0]
        else:
            result = BaseNameModel(
                name="Undefined", scope=_UNIVERSAL_SCOPE, language=Language.ENG
            )
        return result

    class Config:
        from_attributes = True
