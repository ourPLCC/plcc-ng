from ...lines import Line
from ..lexical.LexicalSpec import LexicalSpec
from ..lexical.TokenRule import TokenRule
from ..lexical.SkipRule import SkipRule
from .CapturingTerminal import CapturingTerminal
from .LhsNonTerminal import LhsNonTerminal
from .RepeatingSyntacticRule import RepeatingSyntacticRule
from .RhsNonTerminal import RhsNonTerminal
from .StandardSyntacticRule import StandardSyntacticRule
from .SyntacticSpec import SyntacticSpec
from .Terminal import Terminal


def deserialize_syntactic_spec(spec):
    rules = [_rule(r) for r in spec.get('syntax', {}).get('rules', [])]
    syn = SyntacticSpec(rules=rules)
    lex_rules = [_lex_rule(r) for r in spec.get('lexical', {}).get('ruleList', [])]
    lex = LexicalSpec(ruleList=lex_rules)
    return syn, lex


def _rule(r):
    line = _line(r['line'])
    lhs = LhsNonTerminal(name=r['lhs']['name'], altName=r['lhs'].get('altName'))
    rhs = [_symbol(s) for s in r.get('rhsSymbolList', [])]
    if 'separator' in r:
        sep = _symbol(r['separator']) if r['separator'] is not None else None
        return RepeatingSyntacticRule(line=line, lhs=lhs, rhsSymbolList=rhs, separator=sep)
    return StandardSyntacticRule(line=line, lhs=lhs, rhsSymbolList=rhs)


def _symbol(s):
    name = s.get('name')
    alt = s.get('altName')
    is_terminal = s.get('isTerminal', False)
    is_capturing = s.get('isCapturing', False)
    if is_terminal and is_capturing:
        return CapturingTerminal(name=name, altName=alt)
    if is_terminal:
        return Terminal(name=name)
    return RhsNonTerminal(name=name, altName=alt)


def _lex_rule(r):
    line = _line(r['line']) if r.get('line') else None
    RuleClass = SkipRule if r.get('isSkip') else TokenRule
    return RuleClass(line=line, name=r['name'], pattern=r['pattern'])


def _line(d):
    return Line(string=d['string'], number=d['number'], file=d.get('file'))
