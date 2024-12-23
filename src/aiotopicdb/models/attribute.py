"""
Part of the Contextualise AI (https://contextualise.dev) project

Brett Alistair Kromkamp - brettkromkamp@gmail.com
December 8, 2024
"""

import uuid

from slugify import slugify  # type: ignore

from aiotopicdb.constants import UNIVERSAL_SCOPE
from aiotopicdb.models.datatype import DataType
from aiotopicdb.models.language import Language
from aiotopicdb.topicdberror import TopicDbError


class Attribute:
    def __init__(
        self,
        name: str,
        value: str,
        entity_identifier: str,
        identifier: str = "",
        data_type: DataType = DataType.STRING,
        scope: str = UNIVERSAL_SCOPE,
        language: Language = Language.ENG,
    ) -> None:
        self.__entity_identifier = (
            entity_identifier if entity_identifier == UNIVERSAL_SCOPE else slugify(str(entity_identifier))
        )
        self.__identifier = str(uuid.uuid4()) if identifier == "" else slugify(str(identifier))
        self.__scope = scope if scope == UNIVERSAL_SCOPE else slugify(scope)

        self.name = name
        self.data_type = data_type
        self.language = language
        self.value = value

    def __repr__(self) -> str:
        return "Attribute('{0}', '{1}', '{2}', '{3}', {4}, '{5}', {6})".format(
            self.name,
            self.value,
            self.__entity_identifier,
            self.__identifier,
            str(self.data_type),
            self.__scope,
            str(self.language),
        )

    @property
    def entity_identifier(self) -> str:
        return self.__entity_identifier

    @entity_identifier.setter
    def entity_identifier(self, value: str) -> None:
        if value == "":
            raise TopicDbError("Empty 'value' parameter")
        self.__entity_identifier = value if value == UNIVERSAL_SCOPE else slugify(str(value))

    @property
    def identifier(self) -> str:
        return self.__identifier

    @property
    def scope(self) -> str:
        return self.__scope

    @scope.setter
    def scope(self, value: str) -> None:
        if value == "":
            raise TopicDbError("Empty 'value' parameter")
        self.__scope = value if value == UNIVERSAL_SCOPE else slugify(str(value))
