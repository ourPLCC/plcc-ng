import io
import json
import pytest

from .emit import main as run_main, build_diagram


_ARITH_MODEL = {
    "start": "program",
    "classes": [
        {"name": "Program",  "abstract": False, "extends": None,        "fields": [{"name": "expr", "type": "Expr"}]},
        {"name": "Expr",     "abstract": False, "extends": None,        "fields": [{"name": "term", "type": "Term"}, {"name": "rest", "type": "ExprRest"}]},
        {"name": "ExprRest", "abstract": True,  "extends": None,        "fields": []},
        {"name": "AddRest",  "abstract": False, "extends": "ExprRest",  "fields": [{"name": "term", "type": "Term"}, {"name": "rest", "type": "ExprRest"}]},
        {"name": "NilRest",  "abstract": False, "extends": "ExprRest",  "fields": []},
        {"name": "Term",     "abstract": False, "extends": None,        "fields": [{"name": "num",  "type": "Token"}]}
    ],
    "semantic_sections": []
}


def test_build_diagram_starts_with_startuml():
    result = build_diagram(_ARITH_MODEL)
    assert result.startswith('@startuml\n')


def test_build_diagram_ends_with_enduml():
    result = build_diagram(_ARITH_MODEL)
    assert result.strip().endswith('@enduml')


def test_build_diagram_contains_program_class():
    result = build_diagram(_ARITH_MODEL)
    assert 'class Program' in result


def test_build_diagram_contains_field():
    result = build_diagram(_ARITH_MODEL)
    assert 'expr: Expr' in result


def test_build_diagram_abstract_class():
    result = build_diagram(_ARITH_MODEL)
    assert 'abstract class ExprRest' in result


def test_build_diagram_concrete_class_with_no_fields():
    result = build_diagram(_ARITH_MODEL)
    assert 'class NilRest {' in result


def test_build_diagram_inheritance_arrow():
    result = build_diagram(_ARITH_MODEL)
    assert 'AddRest --|> ExprRest' in result
    assert 'NilRest --|> ExprRest' in result


def test_build_diagram_no_arrow_for_no_extends():
    result = build_diagram(_ARITH_MODEL)
    assert 'Program --|>' not in result


def test_main_writes_diagram_puml(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_ARITH_MODEL)))
    run_main([f'--output={tmp_path}'])
    assert (tmp_path / 'diagram.puml').exists()


def test_main_diagram_contains_class_name(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_ARITH_MODEL)))
    run_main([f'--output={tmp_path}'])
    content = (tmp_path / 'diagram.puml').read_text()
    assert 'ExprRest' in content


def test_main_no_args_writes_to_stdout(monkeypatch, capsys):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_ARITH_MODEL)))
    run_main([])
    captured = capsys.readouterr()
    assert '@startuml' in captured.out
