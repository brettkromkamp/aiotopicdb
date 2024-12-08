"""
Part of the Contextualise AI (https://contextualise.dev) project

Brett Alistair Kromkamp - brettkromkamp@gmail.com
December 8, 2024
"""

from enum import Enum


class RetrievalMode(Enum):
    RESOLVE_ATTRIBUTES = 1
    DONT_RESOLVE_ATTRIBUTES = 2
    RESOLVE_OCCURRENCES = 3
    DONT_RESOLVE_OCCURRENCES = 4
    INLINE_RESOURCE_DATA = 5
    DONT_INLINE_RESOURCE_DATA = 6
    FILTER_BASE_TOPICS = 7
    DONT_FILTER_BASE_TOPICS = 8

    def __str__(self):
        return self.name
