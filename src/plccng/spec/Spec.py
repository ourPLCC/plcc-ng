from dataclasses import dataclass

from ..spec import lexical, semantics, syntax


@dataclass
class Spec:
    lexical: lexical.LexicalSpec
    syntax: syntax.SyntacticSpec
    semantics: list[semantics.SemanticSpec]
