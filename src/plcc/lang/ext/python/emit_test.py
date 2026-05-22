import io
import json
import subprocess
import sys

import pytest
from docopt import DocoptExit

from .emit import main as run_main


def _arith_model():
    return {
        "start": "program",
        "classes": [
            {"name": "Program", "abstract": False, "extends": None, "rule_name": "program",
             "fields": [{"name": "expr", "type": "Expr"}]},
            {"name": "Expr", "abstract": False, "extends": None, "rule_name": "Expr",
             "fields": [{"name": "term", "type": "Term"}, {"name": "rest", "type": "ExprRest"}]},
            {"name": "ExprRest", "abstract": True, "extends": None, "rule_name": "ExprRest",
             "fields": []},
            {"name": "AddRest", "abstract": False, "extends": "ExprRest", "rule_name": "ExprRest",
             "fields": [{"name": "term", "type": "Term"}, {"name": "rest", "type": "ExprRest"}]},
            {"name": "NilRest", "abstract": False, "extends": "ExprRest", "rule_name": "ExprRest",
             "fields": []},
            {"name": "Term", "abstract": False, "extends": None, "rule_name": "Term",
             "fields": [{"name": "num", "type": "Token"}]},
        ],
        "semantic_sections": [
            {
                "language": "Python",
                "tool": "calculate",
                "entry_point": "_run",
                "fragments": [
                    {"class_name": "Program", "kind": "body", "body": "def _run(self):\n    return self.expr.eval()"},
                    {"class_name": "AddRest", "kind": "body", "body": "def eval(self, acc):\n    return self.rest.eval(acc + self.term.eval())"},
                    {"class_name": "NilRest", "kind": "body", "body": "def eval(self, acc):\n    return acc"},
                    {"class_name": "Term", "kind": "body", "body": "def eval(self):\n    return int(self.num.lexeme)"},
                    {"class_name": "Expr", "kind": "body", "body": "def eval(self):\n    return self.rest.eval(self.term.eval())"},
                ]
            }
        ]
    }


def _minimal_model():
    return {
        "start": "program",
        "classes": [
            {"name": "Program", "abstract": False, "extends": None,
             "fields": [], "rule_name": "program"},
        ],
        "semantic_sections": [],
    }


def test_emit_generates_start_py(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_minimal_model())))
    run_main([f'--output={tmp_path}'])
    assert (tmp_path / '_Start.py').exists()


def test_start_class_extends_start(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_minimal_model())))
    run_main([f'--output={tmp_path}'])
    program_py = (tmp_path / 'Program.py').read_text()
    assert 'from _Start import _Start' in program_py
    assert 'class Program(_Start' in program_py


def test_non_start_class_does_not_extend_start(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_arith_model())))
    run_main([f'--output={tmp_path}'])
    term_py = (tmp_path / 'Term.py').read_text()
    assert '_Start' not in term_py


def test_start_class_with_semantics_still_extends_start(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_arith_model())))
    run_main([f'--output={tmp_path}'])
    program_py = (tmp_path / 'Program.py').read_text()
    assert 'from _Start import _Start' in program_py
    assert 'class Program(_Start' in program_py


def test_start_class_with_explicit_parent_does_not_get_start(tmp_path, monkeypatch):
    model = _minimal_model()
    model['classes'][0]['extends'] = 'SomeBase'
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])
    program_py = (tmp_path / 'Program.py').read_text()
    assert '_Start' not in program_py


def test_no_args_prints_usage():
    with pytest.raises((DocoptExit, SystemExit)):
        run_main([])


def test_emit_produces_one_py_file_per_class(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_arith_model())))
    run_main([f'--output={tmp_path}'])
    class_names = ["Program", "Expr", "ExprRest", "AddRest", "NilRest", "Term"]
    for name in class_names:
        assert (tmp_path / f'{name}.py').exists(), f"{name}.py missing"


def test_emit_produces_main_py(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_arith_model())))
    run_main([f'--output={tmp_path}'])
    assert (tmp_path / 'main.py').exists()


def test_emit_copies_runtime_directory(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_arith_model())))
    run_main([f'--output={tmp_path}'])
    assert (tmp_path / 'runtime' / 'base.py').exists()
    assert (tmp_path / 'runtime' / 'registry.py').exists()
    assert (tmp_path / 'runtime' / 'deserialize.py').exists()
    assert not (tmp_path / 'runtime' / 'base_test.py').exists()


def test_emit_class_file_contains_body_fragment(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_arith_model())))
    run_main([f'--output={tmp_path}'])
    term_py = (tmp_path / 'Term.py').read_text()
    assert 'def eval(self):' in term_py
    assert 'int(self.num.lexeme)' in term_py


def test_emit_class_file_imports_runtime(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_arith_model())))
    run_main([f'--output={tmp_path}'])
    program_py = (tmp_path / 'Program.py').read_text()
    assert 'import runtime.base as _plcc' in program_py


def test_emit_subclass_imports_parent(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_arith_model())))
    run_main([f'--output={tmp_path}'])
    addrest_py = (tmp_path / 'AddRest.py').read_text()
    assert 'from ExprRest import ExprRest' in addrest_py


def test_emit_main_py_contains_entry_point(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_arith_model())))
    run_main([f'--output={tmp_path}'])
    main_py = (tmp_path / 'main.py').read_text()
    assert 'tree._run()' in main_py


def test_emit_main_py_entry_point_defaults_to_run_when_null(tmp_path, monkeypatch):
    model = _arith_model()
    model['semantic_sections'][0]['entry_point'] = None
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])
    main_py = (tmp_path / 'main.py').read_text()
    assert 'tree._run()' in main_py


def test_emit_file_fragment_written_verbatim(tmp_path, monkeypatch):
    model = _arith_model()
    model['semantic_sections'][0]['fragments'].append(
        {"class_name": "Env", "kind": "file", "body": "class Env:\n    pass\n"}
    )
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])
    env_py = (tmp_path / 'Env.py').read_text()
    assert 'class Env:' in env_py


def test_emit_generated_main_is_runnable(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_arith_model())))
    run_main([f'--output={tmp_path}'])
    result = subprocess.run(
        [sys.executable, str(tmp_path / 'main.py')],
        input='',
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
