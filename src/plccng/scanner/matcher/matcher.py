from ..structs import LexError, Skip, Token
import re

class Matcher:
    def __init__(self, spec):
        self.spec = spec

    def match(self, line, index):
        return LexError(line=line, column=1)

    #def compile_regex():
     #   patterns =

