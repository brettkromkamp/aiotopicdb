"""
Part of the Contextualise AI (https://contextualise.dev) project

Brett Alistair Kromkamp - brettkromkamp@gmail.com
December 8, 2024
"""


class TopicDbError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
