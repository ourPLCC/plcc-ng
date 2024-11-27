from dataclasses import dataclass

@dataclass
class InvalidNonterminalException(Exception):
    def __init__(self, rule):
        super().__init__(rule)
        self.message = f"Invalid nonterminal format for: '{rule}' (must not be empty and it must be an object that has __hah__ and __eq__ methods)"

@dataclass
class InvalidFormException(Exception):
    def __init__(self, rule):
        super().__init__(rule)
        self.message = f"Invalid form format: '{rule}' (must be a list)"

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
