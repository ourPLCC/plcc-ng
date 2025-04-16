from .structs import Token
from .Skip import Skip
from .LexError import LexError
from ..lines import Line
from .formatter import Formatter
import json


def test_empty():
    formatter = Formatter()
    jsonString = formatter.format([])
    assert jsonString == ''

def test_single_Token():
    formatter = Formatter()
    jsonString = formatter.format([Token("lexeme", "name", makeLine("string", 1, "-"),column=3)])
    assert json.loads(jsonString) == json.loads('''
{"Type": "Token",
"Name": "lexeme",
"Lexeme": "name",
"Line": 1,
"Column": 3}''')

def test_single_Skip():
    formatter = Formatter()
    jsonString = formatter.format([Skip("lexeme", "name", 3)])
    assert json.loads(jsonString) == json.loads('''
{"Type": "Skip",
"Name": "name",
"Lexeme": "lexeme",
"Column": 3}''')

def test_single_lexError():
    formatter = Formatter()
    jsonString = formatter.format([LexError(makeLine("string", 1, "-"), 3)])
    assert json.loads(jsonString) == json.loads('''
{"Type": "LexError",
"Line": "string",
"Column": 3}''')

def makeLine(string, number, file=None):
    return Line(string, number, file)
