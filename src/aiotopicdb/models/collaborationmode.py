"""
Part of the Contextualise AI (https://contextualise.dev) project

Brett Alistair Kromkamp - brettkromkamp@gmail.com
December 8, 2024
"""

from enum import Enum


class CollaborationMode(Enum):
    VIEW = 1  # Read-only
    COMMENT = 2
    EDIT = 3  # Read/write

    def __str__(self) -> str:
        return self.name
