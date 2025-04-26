import json

import pytest

from ..lines import Line
from .json_formatter import format
from .LexError import LexError
from .Skip import Skip
from .Token import Token


def test_invalid_type():
    with pytest.raises(TypeError):
        format("invalid")


def test_token():
    string = format(makeToken())
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
    string = format(makeLexError())
    assertJsonStringIsCorrect(string, '''
        {
            "Type": "LexError",
            "File": "fileName",
            "Line": 1,
            "Column": 2
        }
    ''')

def test_skip():
    string = format(makeSkip())
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
    return Token(name=name, lexeme=lexeme, line=line, column=column)


def makeSkip(lexeme="lexeme", name="name", line=makeLine(), column=2):
    return Skip(lexeme=lexeme, name=name, line=line, column=column)


def makeLexError(line=makeLine(), column=2):
    return LexError(line=line, column=column)
