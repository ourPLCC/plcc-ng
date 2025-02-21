
from plccng.spec.structs import SemanticSpec
from .parse_code_fragments import parse_code_fragments
from plccng.lines import Line
from plccng.spec.structs import Block
from plccng.spec.structs import Divider
import re

def parse_semantic_spec(semantic_spec: list[Divider | Line | Block]) -> SemanticSpec:
    divider = semantic_spec[0]
    codeFragmentList = parse_code_fragments(semantic_spec[1:])
    return SemanticSpec(language = divider.language, tool = divider.tool, codeFragmentList=codeFragmentList)

