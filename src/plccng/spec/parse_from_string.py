from ..spec.Spec import Spec
from ..spec.split_rough import split_rough
from . import lexical, rough, semantics, syntax


def parse_from_string(string):
    rough_ = iter(rough.parse_from_string(string))
    rough_lex, rough_syn, rough_sems = split_rough(rough_)
    lex_ = lexical.parse_from_lines(rough_lex)
    syn_ = syntax.parse_syntactic_spec(rough_syn)
    sems_ = [semantics.parse_semantic_spec(rs) for rs in rough_sems]
    return Spec(lexical=lex_, syntax=syn_, semantics=sems_)
