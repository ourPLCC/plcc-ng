from dataclasses import dataclass
from .ValidationError import ValidationError


@dataclass
class SpecError(Exception, ValidationError):
    column: int

    def __str__(self):
        m = f'\n{self.message}' if self.message else ''
        return f'''{self.__class__.__name__}: {self.line.file}:{self.line.number}:{self.column}\n{self.line.string}\n{' '*(self.column-1)}^{m}\n'''
