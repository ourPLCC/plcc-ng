from .build_parsing_table import Table
from .check_parsing_table_for_ll1 import check_parsing_table_for_ll1


def test_more_than_one_entry_yields_error():
    table = Table({
        ('X', 'a'): ['V', 'E']
    })
    errors = check_parsing_table_for_ll1(table)
    assert len(errors) == 1
    assert errors[0].cell == ('X', 'a')
    assert errors[0].production == {'V', 'E'}
    assert errors[0].count == 2


def test_no_incorrect_cells_yields_no_errors():
    table = Table({
        ('X', 'a'): ['V'],
        ('A', 'b'): ['d'],
        ('A', 'c'): ['e']
    })
    errors = check_parsing_table_for_ll1(table)
    assert len(errors) == 0


def test_each_cell_with_duplicate_yields_an_error():
    table = Table({
        ('X', 'a'): ['V', 'E'],
        ('A', 'b'): ['d'],
        ('A', 'c'): ['e', 'E']
    })
    errors = check_parsing_table_for_ll1(table)
    assert len(errors) == 2
    assert errors[0].cell == ('X', 'a')
    assert errors[0].production == {'V', 'E'}
    assert errors[0].count == 2
    assert errors[1].cell == ('A', 'c')
    assert errors[1].production == {'e', 'E'}
    assert errors[1].count == 2


def test_conflict_reports_count():
    table = Table({
        ('X', 'a'): ['V', 'E']
    })
    errors = check_parsing_table_for_ll1(table)
    assert errors[0].count == 2


def test_identical_productions_in_same_cell_yield_error():
    table = Table({
        ('X', 'a'): ['V', 'V']
    })
    errors = check_parsing_table_for_ll1(table)
    assert len(errors) == 1
    assert errors[0].cell == ('X', 'a')
    assert errors[0].production == {'V'}
    assert errors[0].count == 2
