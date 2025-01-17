"""
Part of the Contextualise AI (https://contextualise.dev) project

Brett Alistair Kromkamp - brettkromkamp@gmail.com
December 8, 2024
"""

import uuid

from slugify import slugify  # type: ignore

from aiotopicdb.constants import UNIVERSAL_SCOPE
from aiotopicdb.models.language import Language
from aiotopicdb.topicdberror import TopicDbError


class BaseName:
    def __init__(
        self,
        name: str,
        scope: str = UNIVERSAL_SCOPE,
        language: Language = Language.ENG,
        identifier: str = "",
    ) -> None:
        self.__identifier = str(uuid.uuid4()) if identifier == "" else slugify(str(identifier))

        self.name = name
        self.__scope = scope if scope == UNIVERSAL_SCOPE else slugify(str(scope))
        self.language = language

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
