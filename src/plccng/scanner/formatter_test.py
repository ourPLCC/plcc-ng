import json

import pytest

from ..lines import Line
from .formatter import Formatter
from .LexError import LexError
from .Skip import Skip
from .structs import Token


def test_invalid_type():
    formatter = Formatter()
    with pytest.raises(TypeError):
        string = formatter.format("invalid")
        next(string)


def test_token():
    formatter = Formatter()
    string = formatter.format(makeToken())
    assertJsonStringIsCorrect(string, '''
        {
            "Type": "Token",
            "Name": "name",
            "Lexeme": "lexeme",
            "File": "fileName",
            "Line": 1,
            "Column": 2
        }
    ''')


def test_lexError():
    formatter = Formatter()
    string = formatter.format(makeLexError())
    assertJsonStringIsCorrect(string, '''
        {
            "Type": "LexError",
            "File": "fileName",
            "Line": 1,
            "Column": 2
        }
    ''')

def test_skip():
    formatter = Formatter()
    string = formatter.format(makeSkip())
    assertJsonStringIsCorrect(string, '''
        {
            "Type": "Skip",
            "Name": "name",
            "Lexeme": "lexeme",
            "File": "fileName",
            "Line": 1,
            "Column": 2
        }
    ''')


def assertJsonStringIsCorrect(jsonString, expected):
    assert json.loads(jsonString) == json.loads(expected)


def makeLine(string="string", number=1, file="fileName"):
    return Line(string, number, file)


def makeToken(name="name", lexeme="lexeme", line=makeLine(), column=2):
    return Token(name, lexeme, line, column)


def makeSkip(lexeme="lexeme", name="name", line=makeLine(), column=2):
    return Skip(lexeme, name, line, column)


def makeLexError(line=makeLine(), column=2):
    return LexError(line, column)
