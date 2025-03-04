from types import NoneType

from .. import lexparse
from .check_for_duplicate_names import DuplicateName, check_for_duplicate_names


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
    spec = lexparse._from_string_without_validation(string)
    results = check_for_duplicate_names(spec.ruleList)
    for i, e in enumerate(expectedResults):
        if e is not NoneType:
            thing = spec.ruleList[i]
            assert e(thing) in results
