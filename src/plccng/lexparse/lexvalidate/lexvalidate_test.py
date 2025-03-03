from .. import lexparse
from ..LexicalSpec import LexicalSpec
from .check_for_duplicate_names import DuplicateName
from .check_format_of_names import InvalidName
from .check_format_of_patterns import InvalidPattern
from .check_for_unrecognized_lines import UnrecognizedLine
from .lexvalidate import lexvalidate


def test_empty_no_errors():
    lexicalSpec = LexicalSpec([])
    errors = lexvalidate(lexicalSpec)
    assert len(errors) == 0


def test_None_no_errors():
    lexicalSpec = LexicalSpec(None)
    errors = lexvalidate(lexicalSpec)
    assert len(errors) == 0


def test_multiple_errors_all_counted():
    spec = lexparse._from_string_without_validation(r'''

        token NAME          '\w+'   # Valid rule.
        token BAD-NAME      '\w+'   # Invalid name: hyphens not allowed.
        token NAME          '\w+'   # Duplicate name.
        token BAD_PATTERN   '(\w+'  # Invalid pattern.
        unrecognized line

                        ''')
    errors = lexvalidate(spec)
    assert len(errors) == 4
    errorTypes = set(c.__class__ for c in errors)
    assert InvalidName in errorTypes
    assert DuplicateName in errorTypes
    assert UnrecognizedLine in errorTypes
    assert InvalidPattern in errorTypes
