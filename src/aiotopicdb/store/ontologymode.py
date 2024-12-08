"""
Part of the Contextualise AI (https://contextualise.dev) project

Brett Alistair Kromkamp - brettkromkamp@gmail.com
December 8, 2024
"""

from enum import Enum


class OntologyMode(Enum):
    STRICT = 1
    LENIENT = 2

    def __str__(self):
        return self.name
