from dataclasses import dataclass


@dataclass
class LL1Error:
    def __init__(self, cell, production):
        self.cell = cell
        self.production = production
        self.message = f"Two production rules in the same parsing table cell: {cell} -> {production}"
