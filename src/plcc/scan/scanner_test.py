import pytest

from ..lines import parseLines
from ..spec import parseSpec
from ..spec.lexical.TokenRule import TokenRule
from .scanner import Scanner
from .LexError import LexError
from .Skip import Skip
from .Token import Token
from . import matcher as matcherModule


@pytest.fixture
def errorRaisingMatcher():
    class ErrorRaisingMatcher:
        def match(self, line, index):
            return LexError(line=line, column=index+1)
    return ErrorRaisingMatcher()


@pytest.fixture
def tabSkipMatcher():
    class TabSkipMatcher():
        def match(self, line, index):
            if line.string[index] == "\t":
                return Skip(name="whitespace", lexeme="\t", line=line, column=index+1)
            else:
                return LexError(line=line, column=index+1)
    return TabSkipMatcher()


@pytest.fixture
def fiveCharacterMatcher():
    class FiveCharacterMatcher():
        def match(self, line, index):
            return Token(name="Token", lexeme=line.string[index:index+5], line=line, column=index+1)
    return FiveCharacterMatcher()


def test_None_returns_empty():
    scanner = Scanner(matcher=None)
    results = scanner.scan(None)
    assert list(results) == []


def test_empty_returns_empty():
    scanner = Scanner(matcher=None)
    results = scanner.scan([])
    assert list(results) == []


def test_LexError(errorRaisingMatcher):
    scanner = Scanner(errorRaisingMatcher)
    oneLineWithError = parseLines('''\
blah blah
''')
    result = list(scanner.scan(oneLineWithError))
    assertLexErrors(result, lineNumber=1, startColumn=1)


def test_LexError_at_start_goes_through_whole_line_one_character_at_a_time(errorRaisingMatcher):
    scanner = Scanner(errorRaisingMatcher)
    twoLinesWithErrors = parseLines('''\
0123456789
0123456789
''')
    scanner = Scanner(errorRaisingMatcher)
    results = list(scanner.scan(twoLinesWithErrors))
    assertLexErrors(results[0:11], lineNumber=1, startColumn=1)
    assertLexErrors(results[11:], lineNumber=2, startColumn=1)


def test_LexError_in_middle_of_a_line(tabSkipMatcher):
    twoLines = parseLines('''\
\terrors\tmore
''')
    scanner = Scanner(tabSkipMatcher)
    results = list(scanner.scan(twoLines))
    assert isinstance(results[0], Skip)
    assertLexErrors(results[1:7], lineNumber=1, startColumn=2)
    assert isinstance(results[7], Skip)
    assertLexErrors(results[8:], lineNumber=1, startColumn=9)

def test_can_match_multiple_tokens(fiveCharacterMatcher):
    lines = parseLines('''\
12345123451234512345
1234512345
''')
    scanner = Scanner(fiveCharacterMatcher)
    results = list(scanner.scan(lines))
    assert len(results) == 8


def test_scanner_does_not_hang_on_zero_length_skip():
    spec_str = r"skip WS '\s*'" + "\n" + r"token NUM '\d+'"
    spec, _ = parseSpec(spec_str)
    m = matcherModule.Matcher(spec.lexical.ruleList)
    scanner = Scanner(m)
    lines = parseLines("2\n")
    results = list(scanner.scan(lines))
    tokens = [r for r in results if isinstance(r, Token)]
    assert len(tokens) == 1
    assert tokens[0].name == "NUM"
    assert tokens[0].lexeme == "2"


def test_newline_token_rule_matches_line_endings():
    """token NEWLINE '\\n' can match each line ending when Line.string includes the trailing newline."""
    from ..lines.parse_from_strings import parse_from_strings
    nl_rule = TokenRule(line=None, name='NL', pattern=r'\n')
    word_rule = TokenRule(line=None, name='WORD', pattern=r'\w+')
    scanner = Scanner(matcher=makeMatcher([nl_rule, word_rule]))
    lines = list(parse_from_strings(['hello\n', 'world\n']))
    results = list(scanner.scan(lines))
    token_names = [r.name for r in results if isinstance(r, Token)]
    assert token_names == ['WORD', 'NL', 'WORD', 'NL']


def makeMatcher(rules):
    from .matcher import Matcher
    return Matcher(rules)


def assertLexErrors(results, lineNumber, startColumn):
    c = startColumn
    for r in results:
        assertLexErrorAtLineNumberAndColumn(r, lineNumber, c)
        c += 1


def assertLexErrorAtLineNumberAndColumn(result, lineNumber, column):
    assert isinstance(result, LexError)
    assert result.line.number == lineNumber
    assert result.column == column
