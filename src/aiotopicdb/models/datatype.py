"""
DataType enumeration. Part of the Contextualise (https://contextualise.dev) project.

June 12, 2016
Brett Alistair Kromkamp (brettkromkamp@gmail.com)
"""

from enum import IntEnum


class DataType(IntEnum):
    STRING = 1
    NUMBER = 2
    TIMESTAMP = 3
    BOOLEAN = 4

    def __str__(self):
        return self.name
