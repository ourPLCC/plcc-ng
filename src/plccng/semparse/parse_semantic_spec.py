from plccng.lineparse import Line
from plccng.roughparse import Block, Divider

from .SemanticSpec import SemanticSpec
from .parse_code_fragments import parse_code_fragments

def parse_semantic_spec(semantic_spec: list[Divider | Line | Block]) -> SemanticSpec:
    divider = semantic_spec[0]
    codeFragmentList = parse_code_fragments(semantic_spec[1:])
    return SemanticSpec(language = divider.language, tool = divider.tool, codeFragmentList=codeFragmentList)
