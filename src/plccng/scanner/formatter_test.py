from .structs import Token
from .LexError import LexError
from ..lines import Line
from .Skip import Skip
from .formatter import Formatter
import json
import pytest


def test_empty():
    formatter = Formatter()
    iterable = iter([])
    strings = formatter.format(iterable)
    assert len(list(strings)) == 0

def test_invalid_type():
    formatter = Formatter()
    with pytest.raises(TypeError):
        strings = formatter.format(iter(["invalid"]))
        next(strings)

def test_single_Token():
    formatter = Formatter()
    iterable = iter([makeToken()])
    strings = formatter.format(iterable)
    assertNextJsonStringIsCorrect(strings, '''
        {
            "Type": "Token",
            "Name": "name",
            "Lexeme": "lexeme",
            "File": "fileName",
            "Line": 1,
            "Column": 2
        }
    ''')

def test_single_lexError():
    formatter = Formatter()
    iterable = iter([makeLexError()])
    strings = formatter.format(iterable)
    assertNextJsonStringIsCorrect(strings, '''
        {
            "Type": "LexError",
            "File": "fileName",
            "Line": 1,
            "Column": 2
        }
    ''')

def test_yield_skip_true():
    formatter = Formatter(yieldSkips=True)
    iterable = iter([makeSkip()])
    strings = formatter.format(iterable)
    assertNextJsonStringIsCorrect(strings, '''
        {
            "Type": "Skip",
            "Name": "name",
            "Lexeme": "lexeme",
            "File": "fileName",
            "Line": 1,
            "Column": 2
        }
    ''')

def test_yield_skip_false():
    formatter = Formatter(yieldSkips=False)
    iterable = iter([makeSkip()])
    strings = formatter.format(iterable)
    assert len(list(strings)) == 0

def test_consecutive():
    formatter = Formatter()
    iterable = iter([makeLexError(column=1), makeLexError(column=2)])
    strings = formatter.format(iterable)
    assertNextJsonStringIsCorrect(strings, '''
        {
            "Type": "LexError",
            "File": "fileName",
            "Line": 1,
            "Column": 1
        }
    ''')

    assertNextJsonStringIsCorrect(strings, '''
        {
            "Type": "LexError",
            "File": "fileName",
            "Line": 1,
            "Column": 2
        }
    ''')

def assertNextJsonStringIsCorrect(strings, expected):
    jsonString = next(strings)
    assert json.loads(jsonString) == json.loads(expected)

def makeLine(string="string", number=1, file="fileName"):
    return Line(string, number, file)

def makeToken(name="name", lexeme="lexeme", line=makeLine(), column=2):
    return Token(name, lexeme, line, column)

def makeSkip(lexeme="lexeme", name="name", line=makeLine(), column=2):
    return Skip(lexeme, name, line, column)

def makeLexError(line=makeLine(), column=2):
    return LexError(line, column)
