from pytest import raises, mark, fixture
from collections import defaultdict

from .check_parsing_table_for_ll1 import check_parsing_table_for_ll1, LL1Error

def test_more_than_one_entry_yields_error():
    table = defaultdict(list)
    table = { ('X', 'a') : ['V', 'E']}

    errors = check_parsing_table_for_ll1(table)
    assert len(errors) == 1
    assert errors[0].message == createLL1ErrorMessage(('X', 'a'), ['V', 'E'])

def test_no_incorrect_cells_yields_no_errors():
    table = {
    ('X', 'a') : ['V'],
    ('A', 'b') : ['d'],
    ('A', 'c') : ['e']
}
    errors = check_parsing_table_for_ll1(table)
    assert len(errors) == 0

def test_each_cell_with_duplicate_yields_an_error():
    table = {
    ('X', 'a') : ['V', 'E'],
    ('A', 'b') : ['d'],
    ('A', 'c') : ['e', 'E']
    }

    errors = check_parsing_table_for_ll1(table)
    assert len(errors) == 2
    assert errors[0].message == createLL1ErrorMessage(('X', 'a'), ['V', 'E'])
    assert errors[1].message == createLL1ErrorMessage(('A', 'c'), ['e', 'E'])

def createLL1ErrorMessage(cell, production):
    return (f"Two production rules in the same parsing table cell: {cell} -> {production}")
