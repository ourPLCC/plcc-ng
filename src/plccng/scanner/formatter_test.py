from .structs import Token
from .Skip import Skip
from .LexError import LexError
from ..lines import Line
from .formatter import Formatter


def test_empty():
    formatter = Formatter()
    jsonString = formatter.format([])
    assert jsonString == '[\n]'

def test_single_Token():
    formatter = Formatter()
    jsonString = formatter.format([Token("lexeme", "name", makeLine("string", 1, "-"),column=3)])
    assert jsonString == '[\n\t{\n\t\t"Type": "Token",\n\t\t"Name": "lexeme",\n\t\t"Lexeme": "name",\n\t\t"Line": 1,\n\t\t"Column": 3\n\t},\n\n]'

def test_single_Skip():
    formatter = Formatter()
    jsonString = formatter.format([Skip("lexeme", "name", 3)])
    assert jsonString == '[\n\t{\n\t\t"Type": "Skip",\n\t\t"Name": "name",\n\t\t"Lexeme": "lexeme",\n\t\t"Column": 3\n\t},\n\n]'

def test_single_lexError():
    formatter = Formatter()
    jsonString = formatter.format([LexError(makeLine("string", 1, "-"), 3)])
    assert jsonString == '[\n\t{\n\t\t"Type": "LexError",\n\t\t"Line": "string",\n\t\t"Column": 3\n\t},\n]'

def test_consecutive():
    formatter = Formatter()
    jsonString = formatter.format([LexError(makeLine("string", 1, "-"), 3), LexError(makeLine("string2", 2, "-"), 4)])
    assert jsonString == '[\n\t{\n\t\t"Type": "LexError",\n\t\t"Line": "string",\n\t\t"Column": 3\n\t},\n\t{\n\t\t"Type": "LexError",\n\t\t"Line": "string2",\n\t\t"Column": 4\n\t},\n]'


def makeLine(string, number, file=None):
    return Line(string, number, file)
