from .structs import Token
from .Skip import Skip
from .LexError import LexError
from ..lines import Line
from .sink import Sink
from ..lines import Line

def test_token(capfd):
    sink = Sink(iter([makeToken()]))
    sink.write()
    out, err = capfd.readouterr()
    assert '"Type": "Token"' in out
    assert err == ''

def test_lexError(capfd):
    sink = Sink(iter([makeLexError()]))
    sink.write()
    out, err = capfd.readouterr()
    assert '"Type": "LexError"' in out
    assert err == ''

def test_consecutive(capfd):
    sink = Sink(iter([makeToken(), makeLexError()]))
    sink.write()
    out, err = capfd.readouterr()
    assert '"Type": "Token"' in out
    assert '"Type": "LexError"' not in out
    sink.write()
    out, err = capfd.readouterr()
    assert '"Type": "LexError"' in out
    assert '"Type": "Token"' not in out


def makeToken(lexeme="lexeme", name="name", column=3):
    return Token(lexeme, name, makeLine(), column)

def makeLexError(column=3):
    return LexError(makeLine(), column)

def makeLine(string="string", number=1, file="fileName"):
    return Line(string, number, file)
