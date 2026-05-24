import io
import json
import pytest

from .emit import build_diagram, main

_SIMPLE_MODEL = {
    "start": "expr",
    "classes": [
        {"name": "Expr", "abstract": True, "extends": None, "fields": []},
        {"name": "AddExpr", "abstract": False, "extends": "Expr",
         "fields": [{"name": "left", "type": "Expr"},
                    {"name": "right", "type": "Expr"}]},
    ],
    "semantic_sections": []
}


def test_build_diagram_starts_with_classDiagram():
    result = build_diagram(_SIMPLE_MODEL)
    assert result.startswith('classDiagram\n')


def test_build_diagram_ends_with_newline():
    result = build_diagram(_SIMPLE_MODEL)
    assert result.endswith('\n')


def test_build_diagram_abstract_class_has_annotation():
    result = build_diagram(_SIMPLE_MODEL)
    assert '<<abstract>>' in result
    assert 'class Expr' in result


def test_build_diagram_concrete_class_has_fields():
    result = build_diagram(_SIMPLE_MODEL)
    assert 'left: Expr' in result
    assert 'right: Expr' in result


def test_build_diagram_inheritance_arrow():
    result = build_diagram(_SIMPLE_MODEL)
    assert 'AddExpr --|> Expr' in result


def test_build_diagram_empty_model():
    model = {"classes": [], "semantic_sections": []}
    result = build_diagram(model)
    assert result == 'classDiagram\n'


def test_main_writes_diagram_to_stdout(monkeypatch, capsys):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_SIMPLE_MODEL)))
    main([])
    out, _ = capsys.readouterr()
    assert 'classDiagram' in out
    assert 'AddExpr --|> Expr' in out
