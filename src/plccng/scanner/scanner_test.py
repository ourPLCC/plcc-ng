import pytest

from ..lines import parseLines
from .scanner import Scanner
from .structs import LexError, Skip, Token


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
    assert isinstance(result[0], LexError)

def test_LexError_at_start_goes_through_whole_line_one_character_at_a_time(errorRaisingMatcher):
    scanner = Scanner(errorRaisingMatcher)
    twoLinesWithErrors = parseLines('''\
0123456789
0123456789
''')
    scanner = Scanner(errorRaisingMatcher)
    results = list(scanner.scan(twoLinesWithErrors))
    assertLexErrorsOnLine(results[0:10], lineNumber=1, startColumn=1)
    assertLexErrorsOnLine(results[10:11], lineNumber=2, startColumn=1)

def assertLexErrorsOnLine(results, lineNumber, startColumn):
    c = startColumn
    for r in results:
        assertLexErrorAtLineNumberAndColumn(r, lineNumber, c)
        c += 1

def assertLexErrorAtLineNumberAndColumn(result, number, column):
    assert isinstance(result, LexError)
    assert result.line.number == number
    assert result.column == column

def test_lex_error_in_middle(tabSkipMatcher):
    twoLines = parseLines('''\
\terrors\tmore
''')
    scanner = Scanner(tabSkipMatcher)
    results = list(scanner.scan(twoLines))
    assert isinstance(results[0], Skip)
    assert isinstance(results[1], LexError) and results[1].line.string[results[1].column-1] == 'e'
    assert isinstance(results[7], Skip)
    assert isinstance(results[8], LexError) and results[8].line.string[results[8].column-1] == 'm'

def test_can_match_multiple_tokens(fiveCharacterMatcher):
    lines = parseLines('''\
12345123451234512345
1234512345
''')
    scanner = Scanner(fiveCharacterMatcher)
    results = list(scanner.scan(lines))
    assert len(results) == 6
