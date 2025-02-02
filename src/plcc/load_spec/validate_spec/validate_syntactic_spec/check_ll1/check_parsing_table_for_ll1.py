from collections import defaultdict

from plcc.load_spec.errors import LL1Error
from .build_parsing_table import Table


def check_parsing_table_for_ll1(parsingTable: Table) -> list[LL1Error]:
    errorList = []
    for X, a in parsingTable.getKeys():
        if len(parsingTable.getCell(X, a)) > 1:
            errorList.append(LL1Error((X, a), parsingTable.getCell(X, a)))
    return errorList



