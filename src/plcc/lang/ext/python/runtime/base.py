class Node:
    pass


class Token:
    def __init__(self, kind, lexeme):
        self.kind = kind
        self.lexeme = lexeme

    def __str__(self):
        return self.lexeme
