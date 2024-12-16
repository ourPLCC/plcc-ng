from pytest import fixture
from .LL1Wrapper import wrap_ll1
from plcc.load_spec.parse_spec.parse_syntactic_spec.structs import (
    LhsNonTerminal, RhsNonTerminal, Terminal, CapturingTerminal
)

@fixture
def lhsWrapped():
    return wrap_ll1(getDefaultNonterminalName(), getLhsNonTerminal())

@fixture
def rhsWrapped():
    return wrap_ll1(getDefaultNonterminalName(), getRhsNonTerminal())

@fixture
def terminalWrapped():
    return wrap_ll1('TERMINAL', getTerminal())

@fixture
def capturingTerminalWrapped():
    return wrap_ll1('TERMINAL', getCapturingTerminal())

def test_init(lhsWrapped):
    assert lhsWrapped.name == getDefaultNonterminalName()
    assert lhsWrapped.specObject == getLhsNonTerminal()

def test_nonterminal_eq_with_same_name_and_object(lhsWrapped):
    otherWrapped = createWrapper(lhsWrapped.name, lhsWrapped.specObject)
    assert lhsWrapped == otherWrapped

def test_terminal_eq_with_same_name_and_object(terminalWrapped):
    otherWrapped = createWrapper(terminalWrapped.name, terminalWrapped.specObject)
    assert terminalWrapped == otherWrapped

def test_nonterminal_eq_with_same_name_and_diff_object(lhsWrapped, rhsWrapped):
    assert lhsWrapped == rhsWrapped

def test_terminal_eq_with_same_name_and_diff_object(terminalWrapped, capturingTerminalWrapped):
    assert terminalWrapped == capturingTerminalWrapped

def test_nonterminal_not_eq_with_diff_name(lhsWrapped):
    otherWrapped = createWrapper(getOtherName(), lhsWrapped.specObject)
    assert lhsWrapped != otherWrapped

def test_terminal_not_eq_with_diff_name(terminalWrapped):
    otherWrapped = createWrapper(getOtherTerminalName(), terminalWrapped.specObject)
    assert terminalWrapped != otherWrapped

def test_not_eq_if_other_not_wrapped(lhsWrapped):
    assert lhsWrapped != getOtherName()

def test_none_objects_eq_when_same_instance():
    wrapped = createWrappedWithNoneObject(getDefaultNonterminalName())
    otherWrapped = wrapped
    assert wrapped == otherWrapped

def test_none_object_eq_when_diff_instance():
    wrapped = createWrappedWithNoneObject(getDefaultNonterminalName())
    otherWrapped = createWrappedWithNoneObject(getDefaultNonterminalName())
    assert wrapped == otherWrapped

def test_eq_object_and_none_same_name(lhsWrapped):
    otherWrapped = createWrappedWithNoneObject(lhsWrapped.name)
    assert lhsWrapped == otherWrapped

def test_hash_nonterminal_same_name_diff_object(lhsWrapped, rhsWrapped):
    assert hash(lhsWrapped) == hash(rhsWrapped)

def test_hash_terminal_same_name_diff_object(terminalWrapped, capturingTerminalWrapped):
    assert hash(terminalWrapped) == hash(capturingTerminalWrapped)

def test_hash_nonterminal_diff_name(lhsWrapped):
    otherWrapped = createWrapper(getOtherName(), lhsWrapped.specObject)
    assert hash(lhsWrapped) != hash(otherWrapped)

def test_hash_terminal_diff_name(terminalWrapped):
    otherWrapped = createWrapper(getOtherTerminalName(), terminalWrapped.specObject)
    assert hash(terminalWrapped) != hash(otherWrapped)

def test_hash_object_and_none_same_name(lhsWrapped):
    otherWrapped = createWrappedWithNoneObject(lhsWrapped.name)
    assert hash(lhsWrapped) == hash(otherWrapped)

def test_hash_object_and_none_diff_name(lhsWrapped):
    otherWrapped = createWrappedWithNoneObject(getOtherName())
    assert hash(lhsWrapped) != hash(otherWrapped)

def createWrapper(name, specObject):
    return wrap_ll1(name, specObject)

def createWrappedWithNoneObject(name):
    return wrap_ll1(name, None)

def getDefaultNonterminalName():
    return 'nonTerminal'

def getDefaultTerminalName():
    return 'TERMINAL'

def getOtherName():
    return 'otherName'

def getOtherTerminalName():
    return 'OTHERTERMINAL'

def getLhsNonTerminal():
    return LhsNonTerminal(getDefaultNonterminalName())

def getRhsNonTerminal():
    return RhsNonTerminal(getDefaultNonterminalName())

def getTerminal():
    return Terminal(getDefaultTerminalName())

def getCapturingTerminal():
    return CapturingTerminal(getDefaultTerminalName())
