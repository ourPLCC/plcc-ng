from plcc.load_spec.structs import Line


from dataclasses import dataclass


@dataclass
class ValidationError:
    line: Line
    message: str


class MalformedBNFError(Exception):
    def __init__(self, line):
        self.line = line


@dataclass
class InvalidNameFormatError(ValidationError):
    def __init__(self, rule):
        self.line = rule.line
        self.message = f"Invalid name format for rule '{rule.name}' (Must be uppercase letters, numbers, and underscores, and cannot start with a number) on line: {rule.line.number}"


@dataclass
class DuplicateNameError(ValidationError):
    def __init__(self, rule):
        self.line = rule.line
        self.message = f"Duplicate rule name found '{rule.name}' on line: {rule.line.number}"


@dataclass
class InvalidPatternError(ValidationError):
    def __init__(self, rule):
        self.line = rule.line
        self.message = f"Invalid pattern format found '{rule.pattern}' on line: {rule.line.number} (Patterns can not contain closing closing quotes)"


@dataclass
class InvalidRuleError(ValidationError):
    def __init__(self, line):
        self.line = line
        self.message = f"Invalid rule format found on line: {line.number}"


@dataclass
class InvalidClassNameError:
    line: Line
    message: str


@dataclass
class ValidationError3():
    def __init__(self, rule):
        self.rule = rule


@dataclass
class InvalidLhsNameError(ValidationError3):
    def __init__(self, rule):
        super().__init__(rule)
        self.message = f"Invalid LHS name format for rule: '{rule.line.string}' (must start with a lower-case letter, and may contain upper or lower case letters, numbers and/or underscore) on line: {rule.line.number}"


@dataclass
class InvalidLhsAltNameError(ValidationError3):
    def __init__(self, rule):
        super().__init__(rule)
        self.message = f"Invalid LHS alternate name format for rule: '{rule.line.string}' (must start with a upper-case letter, and may contain upper or lower case letters, numbers and/or underscore) on line: {rule.line.number}"


@dataclass
class DuplicateLhsError(ValidationError3):
    def __init__(self, rule):
        super().__init__(rule)
        self.message = f"Duplicate lhs name: '{
            rule.line.string}' on line: {rule.line.number}"


@dataclass
class InvalidRhsNameError(ValidationError3):
    def __init__(self, rule):
        super().__init__(rule)
        self.message = f"Invalid RHS name format for rule: '{
            rule.line.string}' (must start with a lower-case letter, and may contain upper or lower case letters, numbers, and underscore.) on line: {rule.line.number}"


@dataclass
class InvalidRhsAltNameError(ValidationError3):
    def __init__(self, rule):
        super().__init__(rule)
        self.message = f"Invalid RHS alternate name format for rule: '{
            rule.line.string}' (must start with a lower case letter, and may contain upper or lower case letters, numbers, and underscore. on line: {rule.line.number}"


@dataclass
class InvalidRhsTerminalError(ValidationError3):
    def __init__(self, rule):
        super().__init__(rule)
        self.message = f"Invalid RHS alternate name format for rule: '{
            rule.line.string}' (upper-case letters, numbers, and underscore and cannot start with a number. on line: {rule.line.number}"


@dataclass
class UndefinedTerminalError(ValidationError3):
    def __init__(self, rule):
        super().__init__(rule)
        self.message = f"Undefined terminal for rule: '{
            rule.line.string}' on line: {rule.line.number}. All terminals must be defined in the lexical section of the grammar file."


@dataclass
class InvalidRhsSeparatorTypeError(ValidationError3):
    def __init__(self, rule):
        super().__init__(rule)
        self.message = f"Invalid RHS separator, must be terminal: '{
            rule.line.string}' "


@dataclass
class LL1Error:
    def __init__(self, cell, production):
        self.cell = cell
        self.production = production
        self.message = f"Two production rules in the same parsing table cell: {cell} -> {production}"


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
