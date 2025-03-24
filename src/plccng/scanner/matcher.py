from .Token import Token
from .LexError import LexError
from .Skip import Skip
import re

class Matcher:
    def __init__(self, spec):
        self.spec = spec

    def match(self, line, index):
        compiled_patterns = self.compile_regex()
        matches = []
        for ruleIndex, pattern in enumerate(compiled_patterns):
            test_match = re.match(pattern, line.string[index: ])
            if(test_match and self.spec[ruleIndex].isSkip):
                return Skip(lexeme = test_match.group(), name=self.spec[ruleIndex].name, column=test_match.end()+1)
            elif(test_match and not self.spec[ruleIndex].isSkip):
                matches.append(Token(lexeme=test_match.group(), name=self.spec[ruleIndex].name, column=test_match.end()+index))
            else:
                continue
        if matches:
            return self.get_longest_match(matches)
        else:
            return LexError(line=line, column=index+1)

    #Helper methods
    def compile_regex(self):
        compiled_patterns = []
        for rule in self.spec:
            pattern = re.compile(rule.pattern)
            compiled_patterns.append(pattern)
        return compiled_patterns

    def get_longest_match(self, match_list):
            return max(match_list, key=lambda m: len(m.lexeme))
