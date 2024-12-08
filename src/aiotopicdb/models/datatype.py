"""
Part of the Contextualise AI (https://contextualise.dev) project

Brett Alistair Kromkamp - brettkromkamp@gmail.com
December 8, 2024
"""

from enum import Enum


class DataType(Enum):
    STRING = 1
    NUMBER = 2
    TIMESTAMP = 3
    BOOLEAN = 4

    def __str__(self) -> str:
        return self.name
