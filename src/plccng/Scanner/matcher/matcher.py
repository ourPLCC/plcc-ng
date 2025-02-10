from ...load_spec.structs import LexicalRule, Line
import re

class Matcher:
    def __init__(self, rules):
        self.rules = rules

    def match(self, string):
        for r in self.rules:
            test = re.search(r.pattern, string)
            if(not test):
                return "LexError"
            else:
                return test.group()


