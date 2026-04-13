import pytest

from ..lines import Line
from .text_formatter import format
from .LexError import LexError
from .Skip import Skip
from .Token import Token


def test_invalid_type():
    with pytest.raises(TypeError):
        format("invalid")


def test_token(token):
    assert format(token) == """fileName:1:2:Token NAME 'lexeme'"""


def test_lexError(lexError):
    assert format(lexError) == """fileName:1:2:LexError 't'"""


def test_skip(skip):
    assert format(skip) == """fileName:1:2:Skip NAME 'lexeme'"""


@pytest.fixture
def token(line):
    return Token(name="NAME", lexeme="lexeme", line=line, column=2)

@pytest.fixture
def skip(line):
    return Skip(lexeme="lexeme", name="NAME", line=line, column=2)

@pytest.fixture
def lexError(line):
    return LexError(line=line, column=2)

@pytest.fixture
def line():
    return Line(string="string", number=1, file="fileName")

