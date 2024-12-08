"""
Part of the Contextualise AI (https://contextualise.dev) project

Brett Alistair Kromkamp - brettkromkamp@gmail.com
December 8, 2024
"""

from aiotopicdb.topics.models.collaborationmode import CollaborationMode


class Collaborator:
    def __init__(
        self,
        map_identifier: int,
        user_identifier: int,
        user_name: str,
        collaboration_mode: CollaborationMode,
    ):
        self.__map_identifier = map_identifier
        self.__user_identifier = user_identifier
        self.__user_name = user_name
        self.__collaboration_mode = collaboration_mode

    @property
    def map_identifier(self) -> int:
        return self.__map_identifier

    @property
    def user_identifier(self) -> int:
        return self.__user_identifier

    @property
    def user_name(self) -> str:
        return self.__user_name

    @property
    def collaboration_mode(self) -> CollaborationMode:
        return self.__collaboration_mode
