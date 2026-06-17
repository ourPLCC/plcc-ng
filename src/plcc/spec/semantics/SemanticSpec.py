from dataclasses import dataclass

from .CodeFragment import CodeFragment


@dataclass
class SemanticSpec:
    language: str
    codeFragmentList: list[CodeFragment]
