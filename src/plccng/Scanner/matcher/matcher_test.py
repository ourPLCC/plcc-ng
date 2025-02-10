from ...load_spec.parse_spec import parse_lexical_spec
from ...load_spec.structs import Line

from plccng.Scanner.matcher import matcher

def test_rules_attribute():
    lexical_spec = make_lexical_spec()
    test_matcher = matcher.Matcher(lexical_spec.ruleList)
    print(test_matcher.rules)

def test_empty_line():
    test_matcher = make_matcher()
    assert "LexError" == test_matcher.match("")

def test_not_empty_line():
    test_matcher = make_matcher()
    assert "-" == test_matcher.match("+++-++")

def test_return_first_rule():
    assert False

#helper methods
def make_lexical_spec():
    lexical_spec = parse_lexical_spec([makeLine('token MINUS \'\\-\'', 8, None)])
    return lexical_spec

def makeLine(str, lineNumber, file=None):
    return Line(str, lineNumber, file)

def make_matcher():
    lexical_spec = make_lexical_spec()
    test_matcher = matcher.Matcher(lexical_spec.ruleList)
    return test_matcher
