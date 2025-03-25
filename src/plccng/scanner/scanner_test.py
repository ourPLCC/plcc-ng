import pytest

from ..lines import parseLines
from .scanner import Scanner
from .structs import LexError, Line, Skip, Token


@pytest.fixture
def errorRaisingMatcher():
    class ErrorRaisingMatcher:
        def match(self, line, index):
            return LexError(line=line, column=index)

    return ErrorRaisingMatcher()

@pytest.fixture
def whiteSpaceSkipMatcher():
    class WhiteSpaceSkipMatcher():
        def match(self, line, index):
            if line.string[index] == " ":
                return Skip(name="whitespace", lexeme=" ", line=line, column=index)
            else:
                return LexError(line=line, column=index)
    
    return WhiteSpaceSkipMatcher()

#Matches up to 5 of any characters (whitespace included) in a string
@pytest.fixture
def fiveCharacterMatcher():
    class FiveCharacterMatcher():
        def match(self, line, index):
            final_index = len(line.string) - 1
            if index+5 > final_index:
                return Token(name="Token", lexeme=line.string[index:final_index], line=line, column=final_index)
            return Token(name="Token", lexeme=line.string[index:index+5], line=line, column=index+5)
    
    return FiveCharacterMatcher()

    


def test_no_lines_given_returns_nothing():
    scanner = Scanner(matcher=None)
    results = scanner.scan(None)
    assert list(results) == []


def test_empty_lines_given_returns_nothing():
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


def test_LexError_at_the_start_of_the_line_moves_on_to_next_line(errorRaisingMatcher):
    scanner = Scanner(errorRaisingMatcher)
    twoLinesWithErrors = parseLines('''\
blah blah
next line
''')
    scanner = Scanner(errorRaisingMatcher)
    results = list(scanner.scan(twoLinesWithErrors))
    assert all(isinstance(item, LexError) for item in results)


def test_lex_error_in_middle_of_the_line_moves_on_to_the_next_line(whiteSpaceSkipMatcher):
    lineWithErrorinTheMiddle = parseLines('''\
 this line should create a skip first
after the skip and lexerror this line should also be a lex error
''')
    scanner = Scanner(whiteSpaceSkipMatcher)
    results = list(scanner.scan(lineWithErrorinTheMiddle))
    assert isinstance(results[0], Skip)
    assert isinstance(results[1], LexError)
    assert results[2].line.string == 'after the skip and lexerror this line should also be a lex error'


def test_once_whole_line_is_indexed_scanner_moves_on_to_next_line(fiveCharacterMatcher):
    linesThatWillPassCompletely = parseLines('''\
this line should pass just fine
this line is what we should move on to next
''')
    scanner = Scanner(fiveCharacterMatcher)
    results = list(scanner.scan(linesThatWillPassCompletely))
    for result in results:
        assert result.column < len(result.line.string)


def test_iteration_stops_after_all_lines_scanned(errorRaisingMatcher):
    lines = parseLines('''\
this line is a lex error
 
the line before this one should be good
this line is a mixed bag
''')
    scanner = Scanner(errorRaisingMatcher)
    results = list(scanner.scan(lines))
    assert len(results) == 4
