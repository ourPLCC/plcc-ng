import json
import pytest
from .structs import Line, Match, Skip, Token, LexError

class Scanner:
    def __init__(self):
        self.matcher = Matcher()


    def scan(self, lines):
        return 0