from dataclasses import dataclass

from .CodeFragment import CodeFragment


@dataclass
class SemanticSpec:
    language: str
    tool: str
    codeFragmentList: list[CodeFragment]
    entry_point: str | None = None
