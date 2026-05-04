class ValidationError(Exception):
    def __init__(self, line=None, message=None):
        self.line=line
        self.message = message
