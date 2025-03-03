class CircularIncludeError(Exception):
    def __init__(self, line):
        self.line = line
