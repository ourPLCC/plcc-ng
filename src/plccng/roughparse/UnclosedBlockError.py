class UnclosedBlockError(Exception):
    def __init__(self, line):
        self.line = line
