from .structs import Token
from .LexError import LexError
from ..lines import Line
from .Skip import Skip
from .formatter import Formatter
import json


def test_empty():
    formatter = Formatter()
    strings = formatter.format(iter([]))
    assert len(list(strings)) == 0

def test_single_Token():
    formatter = Formatter()
    strings = formatter.format(iter([Token("lexeme", "name", makeLine("string", 1, "fileName"),column=3)]))
    assert json.loads(next(strings)) == json.loads('''
{"Type": "Token",
"Name": "lexeme",
"Lexeme": "name",
"File": "fileName",
"Line": 1,
"Column": 3}''')

def test_single_lexError():
    formatter = Formatter()
    strings = formatter.format(iter([LexError(makeLine("string", 1, "-"), 3)]))
    assert json.loads(next(strings)) == json.loads('''
{"Type": "LexError",
"File": "-",
"Line": 1,
"Column": 3}''')

def test_consecutive():
    formatter = Formatter()
    strings = formatter.format(iter([LexError(makeLine("string", 1, "fileName"), 3), LexError(makeLine("string2", 2, "-"), 4)]))
    assert json.loads(next(strings)) == json.loads('''
{"Type": "LexError",
"File": "fileName",
"Line": 1,
"Column": 3}''')
    assert json.loads(next(strings)) == json.loads('''
{"Type": "LexError",
"File": "-",
"Line": 2,
"Column": 4}''')

def makeLine(string, number, file=None):
    return Line(string, number, file)
