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


def test_emits_startuml_and_enduml(monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_MODEL)))
    import sys
    from io import StringIO
    captured = StringIO()
    monkeypatch.setattr('sys.stdout', captured)
    run_main([])
    out = captured.getvalue()
    assert out.startswith('@startuml')
    assert out.rstrip().endswith('@enduml')


def test_build_diagram_contains_class_name():
    result = build_diagram(_MODEL)
    assert 'Expr' in result
    assert 'Add' in result


def test_build_diagram_abstract_class():
    result = build_diagram(_MODEL)
    assert 'abstract class Expr' in result


def test_build_diagram_inheritance_arrow():
    result = build_diagram(_MODEL)
    assert 'Expr <|-- Add' in result


def test_build_diagram_field():
    result = build_diagram(_MODEL)
    assert 'left: Expr' in result
