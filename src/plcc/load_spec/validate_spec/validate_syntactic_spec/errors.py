from dataclasses import dataclass


@dataclass
class ValidationError():
    def __init__(self, rule):
        self.rule = rule


@dataclass
class InvalidLhsNameError(ValidationError):
    def __init__(self, rule):
        super().__init__(rule)
        self.message = f"Invalid LHS name format for rule: '{rule.line.string}' (must start with a lower-case letter, and may contain upper or lower case letters, numbers and/or underscore) on line: {rule.line.number}"


@dataclass
class InvalidLhsAltNameError(ValidationError):
    def __init__(self, rule):
        super().__init__(rule)
        self.message = f"Invalid LHS alternate name format for rule: '{rule.line.string}' (must start with a upper-case letter, and may contain upper or lower case letters, numbers and/or underscore) on line: {rule.line.number}"


@dataclass
class DuplicateLhsError(ValidationError):
    def __init__(self, rule):
        super().__init__(rule)
        self.message = f"Duplicate lhs name: '{
            rule.line.string}' on line: {rule.line.number}"


@dataclass
class InvalidRhsNameError(ValidationError):
    def __init__(self, rule):
        super().__init__(rule)
        self.message = f"Invalid RHS name format for rule: '{
            rule.line.string}' (must start with a lower-case letter, and may contain upper or lower case letters, numbers, and underscore.) on line: {rule.line.number}"

@dataclass
class InvalidRhsAltNameError(ValidationError):
    def __init__(self, rule):
        super().__init__(rule)
        self.message = f"Invalid RHS alternate name format for rule: '{
            rule.line.string}' (must start with a lower case letter, and may contain upper or lower case letters, numbers, and underscore. on line: {rule.line.number}"


@dataclass
class InvalidRhsTerminalError(ValidationError):
    def __init__(self, rule):
        super().__init__(rule)
        self.message = f"Invalid RHS alternate name format for rule: '{
            rule.line.string}' (upper-case letters, numbers, and underscore and cannot start with a number. on line: {rule.line.number}"

@dataclass
class UndefinedTerminalError(ValidationError):
    def __init__(self, rule):
        super().__init__(rule)
        self.message = f"Undefined terminal for rule: '{
            rule.line.string}' on line: {rule.line.number}. All terminals must be defined in the lexical section of the grammar file."

@dataclass
class InvalidRhsSeparatorTypeError(ValidationError):
    def __init__(self, rule):
        super().__init__(rule)
        self.message = f"Invalid RHS separator, must be terminal: '{
            rule.line.string}' "
