from ...lines import Line
from ..rough import Block, Divider
from .LanguageDeclaration import LanguageDeclaration
from .MissingLanguageDeclarationError import MissingLanguageDeclarationError
from .parse_code_fragments import parse_code_fragments
from .SemanticSpec import SemanticSpec


def parse_semantic_spec(semantic_spec: list) -> SemanticSpec:
    divider = semantic_spec[0]
    rest = list(semantic_spec[1:])
    language_decl, body_start = _extract_language(rest, divider)
    code_fragments = parse_code_fragments(rest[body_start:])
    return SemanticSpec(language=language_decl.language, codeFragmentList=code_fragments)


def _extract_language(items, divider):
    for i, item in enumerate(items):
        if isinstance(item, Line) and not _is_blank_or_comment(item.string):
            return LanguageDeclaration(language=item.string.strip(), line=item), i + 1
    raise MissingLanguageDeclarationError(line=divider.line, column=1)


def _is_blank_or_comment(s):
    if s is None:
        return True
    stripped = s.strip()
    return stripped == '' or stripped.startswith('#')
