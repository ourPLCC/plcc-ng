from ...lines import Line
from ..rough import Block
from .CodeFragment import CodeFragment
from .SemanticSpec import SemanticSpec
from .TargetLocator import TargetLocator


def deserialize_semantic_spec(spec):
    sem = spec.get('semantics')
    if sem is None:
        return None
    fragments = [_fragment(f) for f in sem.get('codeFragmentList', [])]
    return SemanticSpec(language=sem['language'], codeFragmentList=fragments)


def _fragment(f):
    return CodeFragment(
        targetLocator=_locator(f.get('targetLocator')),
        block=_block(f.get('block')),
    )


def _locator(loc):
    if loc is None:
        return None
    return TargetLocator(
        line=_line(loc['line']),
        className=loc['className'],
        modifier=loc.get('modifier'),
    )


def _block(blk):
    if blk is None:
        return None
    return Block(lines=[_line(l) for l in blk.get('lines', [])])


def _line(d):
    return Line(string=d['string'], number=d['number'], file=d.get('file'))
