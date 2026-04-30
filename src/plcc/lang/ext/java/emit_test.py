import io
import json

import pytest
from docopt import DocoptExit

from .emit import main as run_main


def _trivial_model():
    return {
        "start": "program",
        "classes": [
            {"name": "Program", "abstract": False, "extends": None, "rule_name": "program",
             "fields": [{"name": "expr", "type": "Expr", "is_list": False}]},
            {"name": "Expr", "abstract": True, "extends": None, "rule_name": "expr",
             "fields": []},
            {"name": "NumExpr", "abstract": False, "extends": "Expr", "rule_name": "expr",
             "fields": [{"name": "num", "type": "runtime.Token", "is_list": False}]},
        ],
        "semantic_sections": [
            {
                "language": "Java",
                "tool": "Java",
                "entry_point": "$run",
                "fragments": [
                    {"class_name": "Program", "kind": "body",
                     "body": "    public void $run() {\n        System.out.println(expr.toString());\n    }"},
                ]
            }
        ]
    }


def test_no_args_prints_usage():
    with pytest.raises((DocoptExit, SystemExit)):
        run_main([])


def test_emit_produces_one_java_file_per_class(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_trivial_model())))
    run_main([f'--output={tmp_path}'])
    for name in ["Program", "Expr", "NumExpr"]:
        assert (tmp_path / f'{name}.java').exists(), f"{name}.java missing"


def test_emit_produces_main_java(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_trivial_model())))
    run_main([f'--output={tmp_path}'])
    assert (tmp_path / 'Main.java').exists()


def test_emit_copies_runtime_directory(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_trivial_model())))
    run_main([f'--output={tmp_path}'])
    assert (tmp_path / 'runtime' / 'Node.java').exists()
    assert (tmp_path / 'runtime' / 'Token.java').exists()
    assert (tmp_path / 'runtime' / 'Registry.java').exists()
    assert (tmp_path / 'runtime' / 'Deserializer.java').exists()
    assert list((tmp_path / 'runtime').glob('org.json*.jar'))


def test_abstract_class_generates_no_constructor(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_trivial_model())))
    run_main([f'--output={tmp_path}'])
    expr_java = (tmp_path / 'Expr.java').read_text()
    assert 'abstract' in expr_java
    assert 'public Expr(' not in expr_java


def test_concrete_class_has_map_constructor(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_trivial_model())))
    run_main([f'--output={tmp_path}'])
    program_java = (tmp_path / 'Program.java').read_text()
    assert 'public Program(java.util.Map<String, Object> fields)' in program_java
    assert 'this.expr = (Expr) fields.get("expr")' in program_java


def test_concrete_class_has_rule_metadata(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_trivial_model())))
    run_main([f'--output={tmp_path}'])
    program_java = (tmp_path / 'Program.java').read_text()
    assert '_RULE_NAME' in program_java
    assert '_FIELDS' in program_java


def test_list_field_generates_list_type(tmp_path, monkeypatch):
    model = _trivial_model()
    model['classes'].append({
        "name": "Rands", "abstract": False, "extends": None, "rule_name": "rands",
        "fields": [{"name": "exprList", "type": "Expr", "is_list": True}]
    })
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])
    rands_java = (tmp_path / 'Rands.java').read_text()
    assert 'java.util.List<Expr>' in rands_java
    assert 'this.exprList = (java.util.List<Expr>) fields.get("exprList")' in rands_java


def test_body_fragment_pasted_into_class(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_trivial_model())))
    run_main([f'--output={tmp_path}'])
    program_java = (tmp_path / 'Program.java').read_text()
    assert 'System.out.println(expr.toString())' in program_java


def test_import_fragment_appears_at_top(tmp_path, monkeypatch):
    model = _trivial_model()
    model['semantic_sections'][0]['fragments'].append(
        {"class_name": "Program", "kind": "import", "body": "import java.util.ArrayList;"}
    )
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])
    program_java = (tmp_path / 'Program.java').read_text()
    assert 'import java.util.ArrayList;' in program_java


def test_init_fragment_appears_inside_constructor(tmp_path, monkeypatch):
    model = _trivial_model()
    model['semantic_sections'][0]['fragments'].append(
        {"class_name": "Program", "kind": "init", "body": "System.out.println(\"init\");"}
    )
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])
    program_java = (tmp_path / 'Program.java').read_text()
    ctor_pos = program_java.index('public Program(')
    init_pos = program_java.index('System.out.println("init")')
    assert init_pos > ctor_pos, "init fragment must be inside constructor"


def test_file_fragment_written_as_standalone_java_file(tmp_path, monkeypatch):
    model = _trivial_model()
    model['semantic_sections'][0]['fragments'].append(
        {"class_name": "Env", "kind": "file", "body": "public class Env {}\n"}
    )
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])
    assert (tmp_path / 'Env.java').exists()
    assert 'public class Env {}' in (tmp_path / 'Env.java').read_text()


def test_hash_comment_class_name_is_skipped(tmp_path, monkeypatch):
    model = _trivial_model()
    model['semantic_sections'][0]['fragments'].append(
        {"class_name": "# a comment", "kind": "body", "body": "// ignored"}
    )
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])
    assert not (tmp_path / '# a comment.java').exists()


def test_entry_point_defaults_to_dollar_run_when_null(tmp_path, monkeypatch):
    model = _trivial_model()
    model['semantic_sections'][0]['entry_point'] = None
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])
    main_java = (tmp_path / 'Main.java').read_text()
    assert '"$run"' in main_java


def test_declared_entry_point_is_used(tmp_path, monkeypatch):
    model = _trivial_model()
    model['semantic_sections'][0]['entry_point'] = 'eval'
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])
    main_java = (tmp_path / 'Main.java').read_text()
    assert '"eval"' in main_java


def test_main_java_references_start_class(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_trivial_model())))
    run_main([f'--output={tmp_path}'])
    main_java = (tmp_path / 'Main.java').read_text()
    assert 'Program root' in main_java


def test_verbose_flag_accepted(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_trivial_model())))
    run_main([f'--output={tmp_path}', '--verbose=1'])
