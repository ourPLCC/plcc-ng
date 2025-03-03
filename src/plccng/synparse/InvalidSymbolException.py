from dataclasses import dataclass


@dataclass
class InvalidSymbolException(Exception):
    def __init__(self, rule):
        super().__init__(rule)
        self.message = f"Invalid Symbol: '{rule}' (must be a Symbol object)"
