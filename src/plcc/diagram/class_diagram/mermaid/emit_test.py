import io
import json
import pytest

from .emit import main as run_main, build_diagram


_MODEL = {
    "start": "program",
    "classes": [
        {"name": "Expr", "abstract": True, "extends": None, "fields": []},
        {"name": "Add", "abstract": False, "extends": "Expr",
         "fields": [{"name": "left", "type": "Expr"}]},
    ],
    "semantic_sections": []
}


def test_emits_classDiagram_header(monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_MODEL)))
    from io import StringIO
    captured = StringIO()
    monkeypatch.setattr('sys.stdout', captured)
    run_main([])
    assert captured.getvalue().startswith('classDiagram')


def test_build_diagram_contains_class_name():
    result = build_diagram(_MODEL)
    assert 'Expr' in result
    assert 'Add' in result


def test_build_diagram_abstract_marker():
    result = build_diagram(_MODEL)
    assert '<<abstract>>' in result


def test_build_diagram_inheritance_arrow():
    result = build_diagram(_MODEL)
    assert 'Add --|> Expr' in result


def test_build_diagram_field():
    result = build_diagram(_MODEL)
    assert 'left: Expr' in result
