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
                "fragments": [
                    {"class_name": "Program", "kind": "body",
                     "body": "    public String _run() {\n        return expr.toString();\n    }"},
                ]
            }
        ]
    }


def _minimal_model():
    return {
        "start": "program",
        "classes": [
            {"name": "Program", "abstract": False, "extends": None,
             "rule_name": "program", "fields": []},
        ],
        "semantic_sections": [],
    }


def test_emit_generates_start_java(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_minimal_model())))
    run_main([f'--output={tmp_path}'])
    assert (tmp_path / '_Start.java').exists()
    assert 'abstract class _Start' in (tmp_path / '_Start.java').read_text()


def test_start_class_extends_start(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_minimal_model())))
    run_main([f'--output={tmp_path}'])
    program_java = (tmp_path / 'Program.java').read_text()
    assert 'extends _Start' in program_java


def test_start_java_uses_underscore_run(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_minimal_model())))
    run_main([f'--output={tmp_path}'])
    start_java = (tmp_path / '_Start.java').read_text()
    assert 'public String _run()' in start_java
    assert '$run' not in start_java


def test_start_java_run_returns_instead_of_printing(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_minimal_model())))
    run_main([f'--output={tmp_path}'])
    start_java = (tmp_path / '_Start.java').read_text()
    assert 'return this.toString();' in start_java
    assert 'System.out.println' not in start_java


def test_non_start_class_does_not_extend_start(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_trivial_model())))
    run_main([f'--output={tmp_path}'])
    expr_java = (tmp_path / 'Expr.java').read_text()
    assert 'extends _Start' not in expr_java


def test_start_class_with_semantics_still_extends_start(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_trivial_model())))
    run_main([f'--output={tmp_path}'])
    program_java = (tmp_path / 'Program.java').read_text()
    assert 'extends _Start' in program_java


def test_start_class_with_explicit_parent_does_not_get_start_injected(tmp_path, monkeypatch):
    model = _minimal_model()
    model['classes'][0]['extends'] = 'SomeBase'
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])
    program_java = (tmp_path / 'Program.java').read_text()
    assert 'extends _Start' not in program_java
    assert 'extends SomeBase' in program_java


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
    assert not (tmp_path / 'runtime' / 'Main.java').exists()


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
    assert 'return expr.toString();' in program_java


def test_body_fragment_injected_into_abstract_class(tmp_path, monkeypatch):
    model = _trivial_model()
    model['semantic_sections'][0]['fragments'].append(
        {"class_name": "Expr", "kind": "body",
         "body": "    public abstract int eval();"}
    )
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])
    expr_java = (tmp_path / 'Expr.java').read_text()
    assert 'public abstract int eval()' in expr_java


def test_import_fragment_appears_in_abstract_class_file(tmp_path, monkeypatch):
    model = _trivial_model()
    model['semantic_sections'][0]['fragments'].append(
        {"class_name": "Expr", "kind": "import",
         "body": "import java.util.function.Function;"}
    )
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])
    expr_java = (tmp_path / 'Expr.java').read_text()
    assert 'import java.util.function.Function;' in expr_java


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


def test_main_java_references_start_class(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_trivial_model())))
    run_main([f'--output={tmp_path}'])
    main_java = (tmp_path / 'Main.java').read_text()
    assert 'Program root' in main_java


def test_verbose_flag_accepted(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_trivial_model())))
    run_main([f'--output={tmp_path}', '-v'])


def test_class_fragment_appears_on_class_declaration_line(tmp_path, monkeypatch):
    model = _trivial_model()
    model['semantic_sections'][0]['fragments'].append(
        {"class_name": "Program", "kind": "class", "body": "implements Runnable"}
    )
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])
    program_java = (tmp_path / 'Program.java').read_text()
    class_decl_line = next(l for l in program_java.splitlines() if 'class Program' in l)
    assert 'implements Runnable' in class_decl_line


def test_class_fragment_appears_on_abstract_class_declaration_line(tmp_path, monkeypatch):
    model = _trivial_model()
    model['semantic_sections'][0]['fragments'].append(
        {"class_name": "Expr", "kind": "class", "body": "implements Cloneable"}
    )
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])
    expr_java = (tmp_path / 'Expr.java').read_text()
    class_decl_line = next(l for l in expr_java.splitlines() if 'class Expr' in l)
    assert 'implements Cloneable' in class_decl_line


def test_body_fragment_pasted_into_class_when_language_is_lowercase(tmp_path, monkeypatch):
    model = _trivial_model()
    model['semantic_sections'][0]['language'] = 'java'
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])
    program_java = (tmp_path / 'Program.java').read_text()
    assert 'return expr.toString();' in program_java


def test_emit_main_java_catches_language_error_separately(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_minimal_model())))
    run_main([f'--output={tmp_path}'])
    main_java = (tmp_path / 'Main.java').read_text()
    assert 'LanguageError' in main_java
    assert 'specification_error' in main_java


def test_emit_main_java_contains_ready_signal(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_minimal_model())))
    run_main([f'--output={tmp_path}'])
    main_java = (tmp_path / 'Main.java').read_text()
    assert '"ready"' in main_java


def test_emit_copies_language_error_java(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_minimal_model())))
    run_main([f'--output={tmp_path}'])
    assert (tmp_path / 'runtime' / 'LanguageError.java').exists()


def test_emit_class_file_imports_language_error(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_minimal_model())))
    run_main([f'--output={tmp_path}'])
    program_java = (tmp_path / 'Program.java').read_text()
    assert 'import runtime.LanguageError;' in program_java


def test_main_java_validates_non_null_result(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_minimal_model())))
    run_main([f'--output={tmp_path}'])
    main_java = (tmp_path / 'Main.java').read_text()
    assert 'if (result == null)' in main_java
    assert 'must return a string' in main_java
