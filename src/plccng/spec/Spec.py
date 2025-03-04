from dataclasses import dataclass

from ..spec import lexical, semantics, syntax


@dataclass
class Spec:
    lex: lexical.LexicalSpec
    syn: syntax.SyntacticSpec
    sems: list[semantics.SemanticSpec]
