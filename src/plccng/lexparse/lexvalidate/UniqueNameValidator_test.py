from types import NoneType
from .. import parse_lexical_spec
from .UniqueNameValidator import UniqueNameValidator, DuplicateName


def test_detects_duplicate_tokens():
    assertDetectsDuplicate('''
        token ONE 'one'
        token ONE 'two'
    ''')


def test_detects_duplicate_skips():
    assertDetectsDuplicate('''
        skip ONE 'one'
        skip ONE 'two'
    ''')


def test_detects_skip_duplicating_a_token():
    assertDetectsDuplicate('''
        token ONE 'one'
        skip ONE 'two'
    ''')


def test_detects_token_duplicating_a_skip():
    assertDetectsDuplicate('''
        skip ONE 'two'
        token ONE 'one'
    ''')


def test_no_duplicates_passes():
    assertResults(
        '''
            skip TWO 'two'
            token ONE 'one'
        ''',
        [
            NoneType,
            NoneType
        ]
    )


def test_mixed_duplicates():
    assertResults(
        '''
            skip ONE '1'
            token TWO '2'
            token ONE '1'
            token THREE '3'
            skip TWO '2'
        ''',
        [
            NoneType,
            NoneType,
            DuplicateName,
            NoneType,
            DuplicateName
        ]
    )


def test_multiple_instances_of_same_duplication():
    assertResults(
        '''
            skip ONE '1'
            token TWO '2'
            token ONE '1'
            token THREE '3'
            skip ONE '1'
        ''',
        [
            NoneType,
            NoneType,
            DuplicateName,
            NoneType,
            DuplicateName
        ]
    )


def assertDetectsDuplicate(string):
    assertResults(string, [NoneType, DuplicateName])


def assertResults(string, expectedResults):
    spec = parse_lexical_spec.from_string(string)
    assert len(spec.ruleList) == len(expectedResults)
    pairs = zip(spec.ruleList, expectedResults)
    v = UniqueNameValidator()
    for rule, expected in pairs:
        e = v.validate(rule)
        assert isinstance(e, expected)
