from typing import List

from ...errors import InvalidRhsAltNameError, InvalidRhsTerminalError, MissingNonTerminalError, InvalidRhsNameError
from ...structs import CapturingTerminal, LhsNonTerminal, Line, RepeatingSyntacticRule, RhsNonTerminal, Symbol, SyntacticRule, Terminal
from ...structs import (
    SyntacticSpec
)
from ...errors import (
    InvalidRhsSeparatorTypeError
)
from .validate_rhs import validate_rhs

from ...parse_spec import (
    parse_rough,
    parse_syntactic_spec
)


def test_rhs_terminal_cannot_start_with_number():
    spec = parse("<sentence> ::= 1WORD")
    errors = validate(spec)
    assert isinstance(errors[0], InvalidRhsTerminalError)

def test_rhs_non_terminal_alt_name_cannot_start_with_uppercase():
     invalid_alt_name = parse('''
         <word> ::= 
         <sentence> ::= <word>:Name 
     ''')
     errors = validate(invalid_alt_name)
     assert isinstance(errors[0], InvalidRhsAltNameError)

def test_valid_rhs_alt_name():
    valid_alt_name_non_terminal = parse('''
        <word> ::= 
        <sentence> ::= <word>:name
    ''')
    errors = validate(valid_alt_name_non_terminal)
    assert len(errors) == 0

def test_valid_separator_terminal():
    valid_separator = parse('''
         <sentence> **= WORD +PERIOD 
    ''')
    errors = validate(valid_separator)
    assert len(errors) == 0

def test_missing_non_terminal():
    missing_non_terminal = parse('''
         <sentence> ::= <word>
    ''')
    errors = validate(missing_non_terminal)
    assert isinstance(errors[0], MissingNonTerminalError)

def test_invalid_separator_terminal():
    invalid_separator = parse('''
         <sentence> **= WORD +period 
    ''')

    errors = validate(invalid_separator)
    assert isinstance(errors[0], InvalidRhsSeparatorTypeError)

def test_non_terminals_generate_and_cache():
    spec = parse('''
        <one> ::= NUM
        <two> ::= NUM
        <three> ::= NUM
        <four> ::= NUM
    ''')
    assert spec.getNonTerminals() == {"one", "two", "three", "four"} == spec.getNonTerminals()

def test_rhs_non_terminal_must_not_start_with_underscore():
    invalid_separator = parse('''
         <sentence> ::= <_hello>
    ''')

    errors = validate(invalid_separator)
    assert isinstance(errors[0], InvalidRhsNameError)

def parse(string):
    rough = list(parse_rough(string))
    spec =  parse_syntactic_spec(rough)
    return spec

def validate(syntacticSpec: SyntacticSpec):
    return validate_rhs(syntacticSpec)
