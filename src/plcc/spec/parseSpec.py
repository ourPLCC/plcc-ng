from .MultipleSemanticsError import MultipleSemanticsError
from .Spec import Spec
from .semantics.MissingLanguageDeclarationError import MissingLanguageDeclarationError
from .split_rough import split_rough
from . import lexical, rough, semantics, syntax


def parseSpec(string, file=None, startLineNumber=1):
    rough_, rough_errors = rough.parseRough(string, file, startLineNumber)
    rough_ = iter(rough_)
    rough_lex, rough_syn, rough_sems = split_rough(rough_)
    lex_, lex_errors = lexical.parseLexicalSpec(rough_lex)
    syn_, syn_errors = syntax.parse_syntactic_spec(rough_syn)

    sem_errors = []
    sem_ = None
    if len(rough_sems) > 1:
        second_divider = rough_sems[1][0]
        sem_errors.append(MultipleSemanticsError(line=second_divider.line, column=1, message="only one semantic section is allowed"))
    if rough_sems:
        try:
            sem_ = semantics.parse_semantic_spec(rough_sems[0])
        except MissingLanguageDeclarationError as e:
            sem_errors.append(e)

    return (
        Spec(lexical=lex_, syntax=syn_, semantics=sem_),
        rough_errors + lex_errors + syn_errors + sem_errors,
    )
