import pytest

from plccng.lineparse import Line


from ..LexicalRule import LexicalRule
from ..LexicalSpec import LexicalSpec
from .check_for_duplicate_names import DuplicateName
from .check_format_of_names import InvalidName
from .check_format_of_patterns import InvalidPattern
from .check_for_unrecognized_lines import UnrecognizedLine
from .lexvalidate import lexvalidate


def test_empty_no_errors():
    lexicalSpec = makeLexicalSpec([])
    errors = lexvalidate(lexicalSpec)
    assert len(errors) == 0

def test_None_no_errors():
    lexicalSpec = makeLexicalSpec(None)
    errors = lexvalidate(lexicalSpec)
    assert len(errors) == 0

def test_lowercase_name_format_error():
    assertInvalidName("invalid_name")

def test_whitespace_name_format_error():
    assertInvalidName("NAME ERROR")

def test_empty_name_format_error():
    assertInvalidName("")

def test_invalid_character_format_error():
    assertInvalidName("TE$T")

def test_name_start_with_number_format_error():
    assertInvalidName("1WHITESPACE")

def test_valid_name_no_error():
    assertValidName("TEST")

def test_duplicate_names_duplicate_error():
    validName = "VALID"
    duplicateName = validName
    assertDuplicationError(validName, duplicateName)

def test_unique_names_no_error():
    validName = "VALID"
    otherValidName = "VALID_2"
    assertNoDuplicationError(validName, otherValidName)

def test_line_invalid_rule_error():
    assertInvalidRule("gibberish with no pattern or token")

def test_rule_followed_by_line_invalid_rule_error():
    assertInvalidRule("TEST \'\\w+\' there is nothing useful here")

def test_closing_quotes_pattern_is_an_error():
    assertInvalidPattern("\"")

def test_closing_quotes_anywhere_in_pattern_is_an_error():
    assertInvalidPattern("+\"+")

def test_pattern_cant_be_empty():
    assertInvalidPattern("")

def test_pattern_cant_be_quote_with_whitespace():
    assertInvalidPattern(" ' ")

def test_multiple_errors_all_counted():
    validName = makeLexicalRule(name="NAME")
    invalidName = makeLexicalRule(name="name")
    duplicateName = validName
    line = makeLine("no rules here")
    invalidPattern = makeLexicalRule(pattern="+\"+")
    lexicalSpec = makeLexicalSpec([validName, invalidName, duplicateName, line, invalidPattern])
    errors = lexvalidate(lexicalSpec)
    assert len(errors) == 4

    errorTypes = set(c.__class__ for c in errors)
    assert InvalidName in errorTypes
    assert DuplicateName in errorTypes
    assert UnrecognizedLine in errorTypes
    assert InvalidPattern in errorTypes


def makeLexicalSpec(ruleList=None):
    return LexicalSpec(ruleList)

def makeLexicalRule(name='TEST', pattern='TEST'):
    return LexicalRule(makeLine('TEST'), False, name, pattern)

def makeLine(string, lineNumber=1, file=None):
    return Line(string, lineNumber, file)

def makeLexicalSpecWithOneTokenRule(name='TEST', pattern='TEST'):
    invalidName = makeLexicalRule(name=name, pattern=pattern)
    lexicalSpec = makeLexicalSpec([invalidName])
    return lexicalSpec

def makeLexicalSpecWithTwoTokenRules(name1, name2):
    validName = makeLexicalRule(name=name1)
    duplicateName = makeLexicalRule(name=name2)
    lexicalSpec = makeLexicalSpec([validName, duplicateName])
    return lexicalSpec

def makeInvalidNameFormatError(rule):
    return InvalidName(rule=rule)

def makeDuplicateNameError(rule):
    return DuplicateName(rule=rule)

def makeInvalidPatternError(rule):
    return InvalidPattern(rule=rule)

def makeInvalidRuleError(line):
    return UnrecognizedLine(line=line)

def assertInvalidName(givenName: str):
    lexicalSpec = makeLexicalSpecWithOneTokenRule(name=givenName)
    errors = lexvalidate(lexicalSpec)
    assert len(errors) == 1
    assert errors[0] == makeInvalidNameFormatError(lexicalSpec.ruleList[0])

def assertValidName(givenName: str):
    lexicalSpec = makeLexicalSpecWithOneTokenRule(name=givenName)
    errors = lexvalidate(lexicalSpec)
    assert len(errors) == 0

def assertInvalidPattern(givenPattern: str):
    lexicalSpec = makeLexicalSpecWithOneTokenRule(pattern=givenPattern)
    errors = lexvalidate(lexicalSpec)
    assert len(errors) == 1
    assert errors[0] == makeInvalidPatternError(lexicalSpec.ruleList[0])

def assertInvalidRule(lineStr: str):
    line = makeLine(lineStr)
    lexicalSpec = makeLexicalSpec([line])
    errors = lexvalidate(lexicalSpec)
    assert len(errors) == 1
    assert errors[0] == makeInvalidRuleError(line)

def assertDuplicationError(givenName1: str, givenName2: str):
    lexicalSpec = makeLexicalSpecWithTwoTokenRules(name1=givenName1, name2=givenName2)
    errors = lexvalidate(lexicalSpec)
    assert len(errors) == 1
    assert errors[0] == makeDuplicateNameError(lexicalSpec.ruleList[0])

def assertNoDuplicationError(givenName1: str, givenName2: str):
    lexicalSpec = makeLexicalSpecWithTwoTokenRules(name1=givenName1, name2=givenName2)
    errors = lexvalidate(lexicalSpec)
    assert len(errors) == 0
