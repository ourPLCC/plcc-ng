from .structs import Token
from .Skip import Skip
from .LexError import LexError
from ..lines import Line
from .sink import Sink

def test_token(capfd):
    sink = Sink(printSkips=False)
    sink.write(makeToken())
    out, err = capfd.readouterr()
    assert '"Type": "Token"' in out
    assert err == ''

def test_lexError(capfd):
    sink = Sink(printSkips=False)
    sink.write(makeLexError())
    out, err = capfd.readouterr()
    assert '"Type": "LexError"' in out
    assert err == ''

def test_print_skip(capfd):
    sink = Sink(printSkips=True)
    sink.write(makeSkip())
    out, err = capfd.readouterr()
    assert '"Type": "Skip"' in out
    assert err == ''

def test_do_not_print_skip(capfd):
    sink = Sink(printSkips=False)
    sink.write(makeSkip())
    out, err = capfd.readouterr()
    assert out == ''
    assert err == ''

def test_consecutive(capfd):
    sink = Sink(printSkips=False)
    sink.write(makeToken())
    out, err = capfd.readouterr()
    assert '"Type": "Token"' in out
    assert '"Type": "LexError"' not in out
    sink.write(makeLexError())
    out, err = capfd.readouterr()
    assert '"Type": "LexError"' in out
    assert '"Type": "Token"' not in out


def makeToken(lexeme="lexeme", name="name", column=3):
    return Token(lexeme, name, makeLine(), column)

def makeLexError(column=3):
    return LexError(makeLine(), column)



def makeLine(string="string", number=1, file="fileName"):
    return Line(string, number, file)


def makeSkip(lexeme="lexeme", name="name", line=makeLine(), column=2):
    return Skip(lexeme, name, line, column)
