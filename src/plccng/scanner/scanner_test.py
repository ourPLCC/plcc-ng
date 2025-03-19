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
    scanner = make_scanner_with_blank_matcher()
    results = list(scanner.scan(twoLinesWithErrors))
    assert all(isinstance(item, LexError) for item in results)


def test_lex_error_in_middle_of_the_line_moves_on_to_the_next_line():
    lines = makeLines([' this line should create a skip first', 'after the skip and lexerror this line should be up next'])
    scanner = make_scanner_with_whitespace_matcher()
    results = scanner.scan(lines)
    check1 = next(results)
    assert isinstance(check1, Skip) and check1.lexeme == ' '
    check2 = next(results)
    assert isinstance(check2, LexError) and check2.line.string == ' this line should create a skip first'
    check3 = next(results)
    assert isinstance(check3, LexError) and check3.line.string == 'after the skip and lexerror this line should be up next'

def test_once_whole_line_is_indexed_scanner_moves_on_to_next_line():
    lines = makeLines(['this whole line should be processed', 'then we move on to this line'])
    scanner = make_scanner_with_5_character_matcher()
    results = scanner.scan(lines)
    while True:
        try:
            check = next(results)
            assert check.column < len(check.line.string)
        except StopIteration:
            break

def test_iteration_stops_after_all_lines_scanned():
    lines = makeLines(['this line is a lex error', ' ', 'the line before this one should be good', ' this line is a mixed bag'])
    scanner = make_scanner_with_blank_matcher()
    results = scanner.scan(lines)
    next(results)
    next(results)
    next(results)
    next(results)
    with pytest.raises(StopIteration):
        next(results)

def makeLines(lines):
    line_objects=[]
    for line in lines:
        line_objects.append(Line(string=line, file=None, number=1))
    return line_objects

def make_scanner_with_blank_matcher():
    matcher = BlankMatcher()
    scanner = Scanner(matcher)
    return scanner

def make_scanner_with_whitespace_matcher():
    matcher = SingleWhiteSpaceMatcher()
    scanner = Scanner(matcher)
    return scanner

def make_scanner_with_5_character_matcher():
    matcher = FiveCharacterMatcher()
    scanner = Scanner(matcher)
    return scanner


class BlankMatcher():
    def __init__(self):
        pass

    def match(self, line, index):
        return LexError(line=line, column=index)

#Only matches Skip Tokens to whitespace, everything else is a lex error
class SingleWhiteSpaceMatcher():
    def __init__(self):
        pass

    def match(self, line, index):
        if line.string[index] == " ":
            return Skip(name="whitespace", lexeme=" ", line=line, column=index)
        else:
            return LexError(line=line, column=index)

#Matches any 5 set of characters as a Token, used for checking proper index handling
#??? Should the check for Final Index be in Matcher or Scanner ???
class FiveCharacterMatcher():
    def __init__(self):
        pass

    def match(self, line, index):
        final_index = len(line.string) - 1
        if index+5 > final_index:
            return Token(name="Token", lexeme=line.string[index:final_index], line=line, column=final_index)
        return Token(name="Token", lexeme=line.string[index:index+5], line=line, column=index+5)
