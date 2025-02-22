from ..structs import LexError, Skip, Token
import re

class Matcher:
    def __init__(self, spec):
        self.spec = spec

    def match(self, line, index):
        patterns = self.compile_regex()
        matches = []
        for pattern in patterns:
            test_match = re.match(pattern[0], line.text[index: ])
            if(test_match and pattern[1] == "Skip"):
                return Skip(lexeme = test_match.group(), name=pattern[2], column=test_match.end()+1)
            elif(test_match and pattern[1] == "Token"):
                matches.append(Token(lexeme=test_match.group(), name=pattern[2], column=test_match.end()+index))
            else:
                continue

        if matches:
            return self.get_longest_match(matches)
        else:
            return LexError(line=line, column=index+1)

    #Helper methods
    def compile_regex(self):
        patterns = []
        for object in self.spec:
            pattern = re.compile(object["regex"])
            patterns.append([pattern, object["type"], object["name"]])
        return patterns

    def get_longest_match(self, match_list):
            longest = match_list[0]
            for i in range(1, len(match_list)):
                if (len(match_list[i].lexeme) > len(longest.lexeme)):
                    longest = match_list[i]
            return longest

