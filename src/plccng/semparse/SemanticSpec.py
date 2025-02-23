from .CodeFragment import CodeFragment


from dataclasses import dataclass


@dataclass
class SemanticSpec:
    language: str
    tool: str
    codeFragmentList: list[CodeFragment]
