from pytest import raises, mark, fixture
from collections import defaultdict

from .check_parsing_table_for_ll1 import check_parsing_table_for_ll1, LL1Error
from .build_parsing_table import Table

def test_more_than_one_entry_yields_error():
    table = defaultdict(list)
    table = Table({
        ('X', 'a') : set(['V', 'E'])
    })

    errors = check_parsing_table_for_ll1(table)
    assert len(errors) == 1
    assert errors[0].cell == ('X', 'a')
    assert errors[0].production == {'V', 'E'}

def test_no_incorrect_cells_yields_no_errors():
    table = Table({
        ('X', 'a') : set(['V']),
        ('A', 'b') : set(['d']),
        ('A', 'c') : set(['e'])
    })
    errors = check_parsing_table_for_ll1(table)
    assert len(errors) == 0

def test_each_cell_with_duplicate_yields_an_error():
    table = Table({
        ('X', 'a') : set(['V', 'E']),
        ('A', 'b') : set(['d']),
        ('A', 'c') : set(['e', 'E'])
    })
    errors = check_parsing_table_for_ll1(table)
    assert len(errors) == 2
    assert errors[0].cell == ('X', 'a')
    assert errors[0].production == {'V', 'E'}
    assert errors[1].cell == ('A', 'c')
    assert errors[1].production == {'e', 'E'}

