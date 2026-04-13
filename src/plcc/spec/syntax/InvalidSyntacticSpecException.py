from dataclasses import dataclass


@dataclass
class InvalidSyntacticSpecException(Exception):
    def __init__(self, rule):
        super().__init__(rule)
        self.message = f"Invalid Syntactic Spec: '{rule}' (must be a SyntacticSpec object)"
