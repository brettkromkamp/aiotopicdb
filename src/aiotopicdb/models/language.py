"""
Language enumeration. Part of the Contextualise (https://contextualise.dev) project.

June 12, 2016
Brett Alistair Kromkamp (brettkromkamp@gmail.com)
"""

from enum import Enum


class Language(str, Enum):
    # https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes
    # https://en.wikipedia.org/wiki/ISO_639-2

    ENG = "ENG"
    SPA = "SPA"
    DEU = "DEU"
    ITA = "ITA"
    FRA = "FRA"
    NLD = "NLD"

    def __str__(self):
        return self.name
