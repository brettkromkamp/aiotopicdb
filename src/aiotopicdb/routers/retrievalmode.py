from enum import IntEnum


class RetrievalMode(IntEnum):
    RESOLVE_ATTRIBUTES = 1
    DONT_RESOLVE_ATTRIBUTES = 2
    RESOLVE_OCCURRENCES = 3
    DONT_RESOLVE_OCCURRENCES = 4
    INLINE_RESOURCE_DATA = 5
    DONT_INLINE_RESOURCE_DATA = 6

    def __str__(self):
        return self.name
