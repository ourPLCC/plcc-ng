from ...LL1Error import LL1Error
from .build_parsing_table import Table


def check_parsing_table_for_ll1(parsingTable: Table) -> list[LL1Error]:
    errorList = []
    for X, a in parsingTable.getKeys():
        entries = parsingTable.getCell(X, a)
        if len(entries) > 1:
            errorList.append(LL1Error((X, a), set(entries), len(entries)))
    return errorList
