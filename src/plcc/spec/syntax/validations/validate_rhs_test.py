import pytest

from ... import rough
from ..DuplicateAttribute import DuplicateAttribute
from ..InvalidAttribute import InvalidAttribute
from ..InvalidNonterminal import InvalidNonterminal
from ..InvalidSeparator import InvalidSeparator
from ..InvalidTerminal import InvalidTerminal
from ..parse_syntactic_spec import parse_syntactic_spec
from ..UndefinedNonterminal import UndefinedNonterminal
from .validate_rhs import validate_rhs


def test_rhs_non_terminal_must_not_start_with_underscore():
    assertError(InvalidNonterminal, '''<Sentence> ::= <_Hello>''')


def test_rhs_non_terminal_must_be_pascal_case():
    # lowercase RHS nonterminal name should generate InvalidNonterminal
    assertError(InvalidNonterminal, '''<Sentence> ::= <word>
<word> ::=''')


def test_rhs_pascal_case_non_terminal_is_valid():
    assertValid(InvalidNonterminal, '''<Word> ::=
<Sentence> ::= <Word>''')


def test_rhs_single_char_field_name_is_valid():
    # field names must allow single character (e.g. "e")
    assertValid(InvalidAttribute, '''<Word> ::=
<Sentence> ::= <Word:e>''')


def test_no_duplicate_Rhs_nonterminal():
    assertError(DuplicateAttribute, '''<Verb> ::=
<Sentence> ::= <Verb> <Verb>''')


def test_duplicate_Rhs_nonterminal_with_same_alt_name_not_allowed():
    assertError(DuplicateAttribute, '''<Verb> ::=
<Sentence> ::= <Verb:name> <Verb:name>''')


def test_duplicate_rhs_nonterminal_with_different_alt_name_allowed():
    assertValid(DuplicateAttribute, '''<Verb> ::=
<Sentence> ::= <Verb:name> <Verb:different>''')


def test_duplicate_non_captured_terminals_allowed():
    assertValid(DuplicateAttribute, '''<Sentence> ::= ONE ONE ONE ONE''')


def test_duplicate_captured_terminals_not_allowed():
    assertError(DuplicateAttribute, '''<Sentence> ::= <ONE> <ONE>''')


def test_duplicate_captured_terminals_allowed_with_alt_name():
    assertValid('''<Sentence> ::= <ONE:name> <ONE:different>''')


def test_duplicate_captured_terminals_not_allowed_with_same_alt_name():
    assertError(DuplicateAttribute, '''<Sentence> ::= <ONE:same> <ONE:same>''')


def test_different_names_allowed():
    assertValid(DuplicateAttribute, '''<Sentence> ::= <No> <IS> <All> <Legal>''')


def test_duplicate_captured_terminal_and_non_terminal_not_allowed():
    # <NO> is a capturing terminal with attr "no"; <No> is a nonterminal with attr "no"
    assertError(DuplicateAttribute, '''<Sentence> ::= <NO> <No>''')


def test_duplicate_altName_and_nonterminal_name_not_allowed():
    # <No:yes> has attr "yes"; <Yes> has attr "yes" (name.lower())
    assertError(DuplicateAttribute, '''<Sentence> ::= <No:yes> <Yes>''')


def test_duplicate_altName_and_terminal_name_not_allowed():
    # <No:yes> has attr "yes"; <YES> capturing terminal has attr "yes"
    assertError(DuplicateAttribute, '''<Sentence> ::= <No:yes> <YES>''')


def test_one_nonterminal_with_different_altName_allowed():
    # <No:yes> attr "yes"; <No> attr "no" — different, so no duplicate
    assertValid(DuplicateAttribute, '''<Sentence> ::= <No:yes> <No>''')


def test_rhs_terminal_cannot_start_with_number():
    assertError(InvalidTerminal, "<Sentence> ::= 1WORD")


def test_rhs_non_terminal_alt_name_cannot_start_with_uppercase():
    assertError(InvalidAttribute, '''<Word> ::=
<Sentence> ::= <Word:Name>''')


def test_valid_spec():
    assertValid('''
        <Word> ::=
        <Sentence> ::= <Word>
    ''')


def test_valid_rhs_alt_name():
    assertValid(InvalidAttribute, '''<Word> ::=
<Sentence> ::= <Word:name>''')


def test_valid_separator_terminal():
    assertValid('''<Sentence> **= WORD +PERIOD''')


def test_missing_non_terminal():
    assertError(UndefinedNonterminal, '''<Sentence> ::= <Word>''')


def test_invalid_separator_terminal():
    assertError(InvalidSeparator, '''<Sentence> **= WORD +period''')


def assertError(expectedErrorType, spec):
    errors = validate(spec)
    errorTypes = [e.__class__ for e in errors]
    assert expectedErrorType in errorTypes


def assertValid(unexpectedErrorType, spec=None):
    if not spec:
        spec = unexpectedErrorType
        errors = validate(spec)
        assert not errors
    else:
        errors = validate(spec)
        errorTypes = [e.__class__ for e in errors]
        assert unexpectedErrorType not in errorTypes


def validate(string):
    spec = parse(string)
    return validate_rhs(spec)


def parse(string):
    rough_, errors = rough.parseRough(string)
    spec, _ = parse_syntactic_spec(rough_)
    return spec
