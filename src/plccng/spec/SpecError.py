from .ValidationError import ValidationError


class SpecError(ValidationError):
    def __init__(self, line=None, message=None, column=None, index=None):
        self.column = column if column is not None else index + 1
        ValidationError.__init__(self, line=line, message=message)

    def __str__(self):
        m = f'\n{self.message}' if self.message else ''
        return f'''{self.__class__.__name__}: {self.line.file}:{self.line.number}:{self.column}\n{self.line.string}\n{' '*(self.column-1)}^{m}\n'''
