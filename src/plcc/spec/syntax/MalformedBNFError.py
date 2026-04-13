class MalformedBNFError(Exception):
    def __init__(self, line):
        self.line = line
