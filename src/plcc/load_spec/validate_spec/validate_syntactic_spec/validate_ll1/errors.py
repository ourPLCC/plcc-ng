from dataclasses import dataclass

@dataclass
class InvalidSyntacticSpecException(Exception):
    def __init__(self, rule):
        super().__init__(rule)
        self.message = f"Invalid Syntactic Spec: '{rule}' (must be a SyntacticSpec object)"

@dataclass
class InvalidSymbolException(Exception):
    def __init__(self, rule):
        super().__init__(rule)
        self.message = f"Invalid Symbol: '{rule}' (must be a Symbol object)"

@dataclass
class LeftRecursionException(Exception):
    def __init__(self, rule):
        super().__init__(rule)
        self.message = f"Left recursion detected: '{rule}'"
