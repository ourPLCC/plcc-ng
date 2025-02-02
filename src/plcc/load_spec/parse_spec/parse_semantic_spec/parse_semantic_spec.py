
from plcc.load_spec.structs import SemanticSpec
from .parse_code_fragments import parse_code_fragments
from plcc.load_spec.structs import Line
from plcc.load_spec.structs import Block
from plcc.load_spec.structs import Divider
import re

def parse_semantic_spec(semantic_spec: list[Divider | Line | Block]) -> SemanticSpec:
    divider = semantic_spec[0]
    codeFragmentList = parse_code_fragments(semantic_spec[1:])
    return SemanticSpec(language = divider.language, tool = divider.tool, codeFragmentList=codeFragmentList)

