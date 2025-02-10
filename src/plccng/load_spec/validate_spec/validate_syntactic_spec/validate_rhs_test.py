from ...errors import (
    InvalidSeparator,
    InvalidAttribute,
    InvalidTerminal,
    UndefinedNonterminal,
    InvalidNonterminal,
    DuplicateAttribute
)
from ...parse_spec import (
    parse_rough,
    parse_syntactic_spec
)
from .validate_rhs import validate_rhs


def test_rhs_non_terminal_must_not_start_with_underscore():
    assertError(InvalidNonterminal, '''<sentence> ::= <_hello>''')


def test_no_duplicate_Rhs_nonterminal():
    assertError(DuplicateAttribute, '''<sentence> ::= <verb> <verb>''')


def test_duplicate_Rhs_nonterminal_with_same_alt_name_not_allowed():
    assertError(DuplicateAttribute, '''<sentence> ::= <verb>:name <verb>:name''')


def test_duplicate_rhs_nonterminal_with_different_alt_name_allowed():
    assertValid(DuplicateAttribute, '''<sentence> ::= <verb>:name <verb>:different''')


def test_duplicate_non_captured_terminals_allowed():
    assertValid(DuplicateAttribute, '''<sentence> ::= ONE ONE ONE ONE''')


def test_duplicate_captured_terminals_not_allowed():
    assertError(DuplicateAttribute, '''<sentence> ::= <ONE> <ONE>''')


def test_duplicate_captured_terminals_allowed_with_alt_name():
    assertValid('''<sentence> ::= <ONE>:name <ONE>:different''')


def test_duplicate_captured_terminals_not_allowed_with_same_alt_name():
    assertError(DuplicateAttribute, '''<sentence> ::= <ONE>:same <ONE>:same''')


def test_different_names_allowed():
    assertValid(DuplicateAttribute, '''<sentence> ::= <this> <IS> <all> <legal>''')


def test_duplicate_captured_terminal_and_non_terminal_not_allowed():
    assertError(DuplicateAttribute, '''<sentence> ::= <NO> <no>''')


def test_duplicate_altName_and_nonterminal_name_not_allowed():
    assertError(DuplicateAttribute, '''<sentence> ::= <no>:yes <yes>''')


def test_duplicate_altName_and_terminal_name_not_allowed():
    assertError(DuplicateAttribute, '''<sentence> ::= <no>:yes <YES>''')


def test_one_nonterminal_with_different_altName_allowed():
    assertValid(DuplicateAttribute, '''<sentence> ::= <no>:yes <no>''')


def test_rhs_terminal_cannot_start_with_number():
    assertError(InvalidTerminal, "<sentence> ::= 1WORD")


def test_rhs_non_terminal_alt_name_cannot_start_with_uppercase():
     assertError(InvalidAttribute, '''<sentence> ::= <word>:Name''')


def test_valid_spec():
    assertValid('''
        <word> ::=
        <sentence> ::= <word>
    ''')


def test_valid_rhs_alt_name():
    assertValid(InvalidAttribute, '''<sentence> ::= <word>:name''')


def test_valid_separator_terminal():
    assertValid('''<sentence> **= WORD +PERIOD''')


def test_missing_non_terminal():
    assertError(UndefinedNonterminal, '''<sentence> ::= <word>''')


def test_invalid_separator_terminal():
    assertError(InvalidSeparator, '''<sentence> **= WORD +period''')


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
    rough = list(parse_rough(string))
    spec =  parse_syntactic_spec(rough)
    return spec
