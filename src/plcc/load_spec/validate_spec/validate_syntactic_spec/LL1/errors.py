from dataclasses import dataclass
from ..errors import ValidationError

@dataclass
class InvalidNonterminalError(ValidationError):
    def __init__(self, rule):
        super().__init__(rule)
        self.message = f"Invalid nonterminal format for: '{rule}' (must not be empty and it must be an object that has __hah__ and __eq__ methods)"

@dataclass
class InvalidFormError(ValidationError):
    def __init__(self, rule):
        super().__init__(rule)
        self.message = f"Invalid form format: '{rule}' (must be a list)"

@dataclass
class InvalidSyntacticSpecError(ValidationError):
    def __init__(self, rule):
        super().__init__(rule)
        self.message = f"Invalid SyntacticSpec: '{rule}' (must be a SyntacticSpec object)"

@dataclass
class InvalidSymbolError(ValidationError):
    def __init__(self, rule):
        super().__init__(rule)
        self.message = f"Invalid Symbol: '{rule}' (must be a Symbol object)"

@dataclass
class LeftRecursionError(ValidationError):
    def __init__(self, rule):
        super().__init__(rule)
        self.message = f"Left recursion detected: '{rule}'"
