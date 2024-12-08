"""
Part of the Contextualise AI (https://contextualise.dev) project

Brett Alistair Kromkamp - brettkromkamp@gmail.com
December 8, 2024
"""

from enum import Enum


class TemporalType(Enum):
    EVENT = 1
    ERA = 2

    def __str__(self):
        return self.name.lower()
