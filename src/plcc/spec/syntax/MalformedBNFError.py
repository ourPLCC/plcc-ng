import re


class MalformedBNFError(Exception):
    _EXAMPLES = (
        "Examples:\n"
        "  <nonTerminal> ::=\n"
        "  <nonTerminal> ::= TOKEN <TOKEN> <rhs>\n"
        "  <nonTerminal>:ClassName ::= TOKEN <TOKEN>:field1 <rhs>:field2\n"
        "  <nonTerminal> **= <rhs>\n"
        "  <nonTerminal> **= <rhs> +SEPARATOR"
    )

    def __init__(self, line):
        self.line = line
        self.column = self._compute_column()

    def _compute_column(self):
        original = self.line.string
        leading = len(original) - len(original.lstrip())
        lhs_match = re.match(r"<\S+>(?::\S+)?", original.lstrip())
        if lhs_match:
            return leading + lhs_match.end() + 1
        return leading + 1

    @property
    def kind(self):
        return "syntax error"

    @property
    def hint(self):
        return self._EXAMPLES

    def __str__(self):
        caret = " " * (self.column - 1) + "^"
        return (
            f"{self.line.file}:{self.line.number}:{self.column}: syntax error\n"
            f"{self.line.string}\n"
            f"{caret}\n"
            f"{self._EXAMPLES}"
        )
