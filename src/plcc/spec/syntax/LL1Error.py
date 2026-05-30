from dataclasses import dataclass


@dataclass
class LL1Error:
    def __init__(self, cell, production, count):
        self.cell = cell
        self.production = production
        self.count = count
        self.message = f"{count} rules in parsing table cell {cell}: {production}"
