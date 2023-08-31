"""
DataType enumeration. Part of the Contextualise (https://contextualise.dev) project.

June 12, 2016
Brett Alistair Kromkamp (brettkromkamp@gmail.com)
"""

from enum import Enum


class DataType(str, Enum):
    STRING = "STRING"
    NUMBER = "NUMBER"
    TIMESTAMP = "TIMESTAMP"
    BOOLEAN = "BOOLEAN"

    def __str__(self):
        return self.name
