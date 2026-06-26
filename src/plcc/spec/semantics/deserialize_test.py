import pytest
from .deserialize import deserialize_semantic_spec


def _line(string='X\n', number=1, file='g.plcc'):
    return {'string': string, 'number': number, 'file': file}

def _frag(class_name, modifier=None, block=True):
    return {
        'targetLocator': {
            'line': _line(class_name + '\n'),
            'className': class_name,
            'modifier': modifier,
        },
        'block': {'lines': [_line('%%%\n'), _line('%%%\n')]} if block else None,
    }

def _spec(fragments, language='Java'):
    return {'semantics': {'language': language, 'codeFragmentList': fragments}}


def test_returns_none_when_no_semantics_key():
    assert deserialize_semantic_spec({}) is None

def test_language_preserved():
    result = deserialize_semantic_spec(_spec([], 'Python'))
    assert result.language == 'Python'

def test_empty_fragment_list():
    result = deserialize_semantic_spec(_spec([]))
    assert result.codeFragmentList == []

def test_class_name_preserved():
    result = deserialize_semantic_spec(_spec([_frag('MyClass')]))
    assert result.codeFragmentList[0].targetLocator.className == 'MyClass'

def test_modifier_preserved():
    result = deserialize_semantic_spec(_spec([_frag('MyClass', modifier='init')]))
    assert result.codeFragmentList[0].targetLocator.modifier == 'init'

def test_null_modifier_preserved():
    result = deserialize_semantic_spec(_spec([_frag('MyClass', modifier=None)]))
    assert result.codeFragmentList[0].targetLocator.modifier is None

def test_line_fields_preserved():
    frag = {
        'targetLocator': {
            'line': {'string': 'MyClass\n', 'number': 7, 'file': 'grammar.plcc'},
            'className': 'MyClass',
            'modifier': None,
        },
        'block': {'lines': []},
    }
    result = deserialize_semantic_spec({'semantics': {'language': 'Java', 'codeFragmentList': [frag]}})
    line = result.codeFragmentList[0].targetLocator.line
    assert line.string == 'MyClass\n'
    assert line.number == 7
    assert line.file == 'grammar.plcc'

def test_null_block_preserved():
    result = deserialize_semantic_spec(_spec([_frag('MyClass', block=False)]))
    assert result.codeFragmentList[0].block is None

def test_null_locator_preserved():
    frag = {'targetLocator': None, 'block': {'lines': []}}
    result = deserialize_semantic_spec({'semantics': {'language': 'Java', 'codeFragmentList': [frag]}})
    assert result.codeFragmentList[0].targetLocator is None

def test_multiple_fragments():
    result = deserialize_semantic_spec(_spec([_frag('A'), _frag('B')]))
    assert len(result.codeFragmentList) == 2
    assert result.codeFragmentList[1].targetLocator.className == 'B'
