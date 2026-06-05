from .ValidationError import ValidationError


class SpecError(ValidationError):
    def __init__(self, line=None, message=None, column=None, index=None):
        self.column = column if column is not None else index + 1
        ValidationError.__init__(self, line=line, message=message)

    @property
    def kind(self):
        return self.message or type(self).__name__

    @property
    def hint(self):
        return None

    def __str__(self):
        m = f'\n{self.message}' if self.message else ''
        source = self.line.string.rstrip('\n')
        return f'''{self.__class__.__name__}: {self.line.file}:{self.line.number}:{self.column}\n{source}\n{' '*(self.column-1)}^{m}\n'''
