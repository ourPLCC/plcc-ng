from .Spec import Spec
from .split_rough import split_rough
from . import lexical, rough, semantics, syntax


def parseSpec(string, file=None, startLineNumber=1):
    rough_, errors = rough.parseRough(string, file, startLineNumber)
    rough_ = iter(rough_)
    rough_lex, rough_syn, rough_sems = split_rough(rough_)
    lex_, errors = lexical.parseLexicalSpec(rough_lex)
    syn_ = syntax.parse_syntactic_spec(rough_syn)
    sems_ = [semantics.parse_semantic_spec(rs) for rs in rough_sems]
    return Spec(lexical=lex_, syntax=syn_, semantics=sems_), errors
