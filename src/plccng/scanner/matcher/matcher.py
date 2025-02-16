from ..structs import LexError, Skip, Token
import re

class Matcher:
    def __init__(self, spec):
        self.spec = spec

    def match(self, line, index):
        patterns = self.compile_regex()
        matches = []
        for pattern in patterns:
            test_match = re.match(pattern[0], line.text)
            if(test_match and pattern[1] == "Skip"):
                return Skip(lexeme = test_match.group())
            elif(test_match and pattern[1] == "Token"):
                matches.append(Token(lexeme=test_match.group()))
            else:
                continue

        if matches:
            longest = matches[0]
            for i in range(1, len(matches)):
                if (len(matches[i].lexeme) > len(longest.lexeme)):
                    longest = matches[i]
            return longest

        return LexError(line=line, column=1)

    def compile_regex(self):
        patterns = []
        for object in self.spec:
            pattern = re.compile(object["regex"])
            patterns.append([pattern, object["type"], object["name"]])
        return patterns

