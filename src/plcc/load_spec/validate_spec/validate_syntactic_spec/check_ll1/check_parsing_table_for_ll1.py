from collections import defaultdict
from dataclasses import dataclass
from .build_parsing_table import Table


@dataclass
class LL1Error:
    def __init__(self, cell, production):
        self.cell = cell
        self.production = production
        self.message = f"Two production rules in the same parsing table cell: {cell} -> {production}"


def check_parsing_table_for_ll1(parsingTable: Table) -> list[LL1Error]:
    errorList = []
    for X, a in parsingTable.getKeys():
        if len(parsingTable.getCell(X, a)) > 1:
            errorList.append(LL1Error((X, a), parsingTable.getCell(X, a)))
    return errorList



