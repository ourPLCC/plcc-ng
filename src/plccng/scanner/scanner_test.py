import pytest

from ..lines import parseLines
from .scanner import Scanner
from .structs import LexError, Skip, Token


@pytest.fixture
def errorRaisingMatcher():
    class ErrorRaisingMatcher:
        def match(self, line, index):
            return LexError(line=line, column=index)

    return ErrorRaisingMatcher()


@pytest.fixture
def tabSkipMatcher():
    class TabSkipMatcher():
        def match(self, line, index):
            if line.string[index] == "\t":
                return Skip(name="whitespace", lexeme="\t", line=line, column=index)
            else:
                return LexError(line=line, column=index)

    return TabSkipMatcher()


@pytest.fixture
def fiveCharacterMatcher():
    class FiveCharacterMatcher():
        def match(self, line, index):
            return Token(name="Token", lexeme=line.string[index:index+5], line=line, column=index)

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
    assert isinstance(result[0], LexError)


def test_LexError_at_start(errorRaisingMatcher):
    scanner = Scanner(errorRaisingMatcher)
    twoLinesWithErrors = parseLines('''\
first line
second line
''')
    scanner = Scanner(errorRaisingMatcher)
    results = list(scanner.scan(twoLinesWithErrors))
    assert isinstance(results[0], LexError) and results[0].line.string == 'first line'
    assert isinstance(results[1], LexError) and results[1].line.string == 'second line'

def test_lex_error_in_middle(tabSkipMatcher):
    twoLines = parseLines('''\
\tfirst line
second line
''')
    scanner = Scanner(tabSkipMatcher)
    results = list(scanner.scan(twoLines))
    assert isinstance(results[0], Skip) and results[0].line.string == '\tfirst line'
    assert isinstance(results[1], LexError) and results[1].line.string == '\tfirst line'
    assert isinstance(results[2], LexError) and results[2].line.string == 'second line'


def test_can_match_multiple_tokens(fiveCharacterMatcher):
    lines = parseLines('''\
12345123451234512345
1234512345
''')
    scanner = Scanner(fiveCharacterMatcher)
    results = list(scanner.scan(lines))
    assert len(results) == 6
