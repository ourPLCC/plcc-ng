from collections import defaultdict
from dataclasses import dataclass

@dataclass
class LL1Error:
    def __init__(self, cell, production):
        self.cell = cell
        self.production = production
        self.message = f"Two production rules in the same parsing table cell: {cell} -> {production}"


def check_parsing_table_for_ll1(parsingTable: defaultdict) -> list[LL1Error]:
    errorList = []
    for cell in parsingTable:
        if len(parsingTable[cell]) > 1:
            errorList.append(LL1Error(cell, parsingTable[cell]))
    return errorList



