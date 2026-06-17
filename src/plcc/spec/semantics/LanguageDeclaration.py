from dataclasses import dataclass

from ...lines import Line


@dataclass
class LanguageDeclaration:
    language: str
    line: Line
