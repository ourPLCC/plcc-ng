import json

import pytest

from ..lines import Line
from .formatter import Formatter
from .LexError import LexError
from .Skip import Skip
from .structs import Token


def test_empty():
    formatter = Formatter()
    strings = formatter.format([])
    assert len(list(strings)) == 0


def test_invalid_type():
    formatter = Formatter()
    with pytest.raises(TypeError):
        strings = formatter.format(["invalid"])
        next(strings)


def test_single_Token():
    formatter = Formatter()
    strings = formatter.format([makeToken()])
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
    strings = formatter.format([makeLexError()])
    assertNextJsonStringIsCorrect(strings, '''
        {
            "Type": "LexError",
            "File": "fileName",
            "Line": 1,
            "Column": 2
        }
    ''')


def test_yield_skips():
    formatter = Formatter(yieldSkips=True)
    strings = formatter.format([makeSkip()])
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


def test_do_not_yield_skip():
    formatter = Formatter(yieldSkips=False)
    strings = formatter.format([makeSkip()])
    assert len(list(strings)) == 0


def test_consecutive():
    formatter = Formatter()
    strings = formatter.format([makeLexError(column=1), makeLexError(column=2)])
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
