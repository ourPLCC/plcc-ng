
from plccng.lexparse.LexicalParser import LexicalParser
import plccng.roughparse as roughparse

from . import lexvalidate


def from_string(string, file=None, startLineNumber=1):
    rough = roughparse.fromstring(string, file=file, startLineNumber=startLineNumber)
    return from_lines(rough)


def from_lines(lines):
    rough = _from_lines_without_validation(lines)
    errors = lexvalidate.lexvalidate(rough)
    return rough, errors


def _from_string_without_validation(string, file=None, startLineNumber=1):
    rough = roughparse.fromstring(string, file=file, startLineNumber=startLineNumber)
    return _from_lines_without_validation(rough)


def _from_lines_without_validation(lines):
    return LexicalParser(lines).parseLexicalSpec()
