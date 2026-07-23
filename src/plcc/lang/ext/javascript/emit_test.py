import io
import json
import os
import signal
import subprocess
import sys
import time

import pytest
from docopt import DocoptExit

from .emit import main as run_main


def _minimal_model():
    return {
        "start": "program",
        "classes": [
            {"name": "Program", "abstract": False, "extends": None,
             "fields": [], "rule_name": "program"},
        ],
        "semantic_sections": [],
    }


def _arith_model():
    return {
        "start": "program",
        "classes": [
            {"name": "Program", "abstract": False, "extends": None,
             "rule_name": "program",
             "fields": [{"name": "expr", "type": "Expr"}]},
            {"name": "Expr", "abstract": False, "extends": None,
             "rule_name": "Expr",
             "fields": [{"name": "term", "type": "Term"}, {"name": "rest", "type": "ExprRest"}]},
            {"name": "ExprRest", "abstract": True, "extends": None,
             "rule_name": "ExprRest", "fields": []},
            {"name": "AddRest", "abstract": False, "extends": "ExprRest",
             "rule_name": "ExprRest",
             "fields": [{"name": "term", "type": "Term"}, {"name": "rest", "type": "ExprRest"}]},
            {"name": "NilRest", "abstract": False, "extends": "ExprRest",
             "rule_name": "ExprRest", "fields": []},
            {"name": "Term", "abstract": False, "extends": None,
             "rule_name": "Term",
             "fields": [{"name": "num", "type": "Token"}]},
        ],
        "semantic_sections": [
            {
                "language": "javascript",
                "fragments": [
                    {"class_name": "Program", "kind": "body",
                     "body": "_run() {\n    return String(this.expr.eval());\n}"},
                    {"class_name": "AddRest", "kind": "body",
                     "body": "eval(acc) {\n    return this.rest.eval(acc + this.term.eval());\n}"},
                    {"class_name": "NilRest", "kind": "body",
                     "body": "eval(acc) {\n    return acc;\n}"},
                    {"class_name": "Term", "kind": "body",
                     "body": "eval() {\n    return parseInt(this.num.lexeme);\n}"},
                    {"class_name": "Expr", "kind": "body",
                     "body": "eval() {\n    return this.rest.eval(this.term.eval());\n}"},
                ]
            }
        ]
    }


def test_no_args_prints_usage():
    with pytest.raises((DocoptExit, SystemExit)):
        run_main([])


def test_emit_generates_start_js(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_minimal_model())))
    run_main([f'--output={tmp_path}'])
    assert (tmp_path / '_Start.js').exists()


def test_start_class_extends_start(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_minimal_model())))
    run_main([f'--output={tmp_path}'])
    content = (tmp_path / 'Program.js').read_text()
    assert "require('./_Start')" in content
    assert 'class Program extends _Start' in content


def test_start_class_with_explicit_parent_does_not_get_start(tmp_path, monkeypatch):
    model = _minimal_model()
    model['classes'][0]['extends'] = 'SomeBase'
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])
    content = (tmp_path / 'Program.js').read_text()
    assert '_Start' not in content


def test_non_start_class_does_not_extend_start(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_arith_model())))
    run_main([f'--output={tmp_path}'])
    content = (tmp_path / 'Term.js').read_text()
    assert '_Start' not in content


def test_emit_produces_one_js_file_per_class(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_arith_model())))
    run_main([f'--output={tmp_path}'])
    for name in ["Program", "Expr", "ExprRest", "AddRest", "NilRest", "Term"]:
        assert (tmp_path / f'{name}.js').exists(), f'{name}.js missing'


def test_emit_produces_main_js(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_arith_model())))
    run_main([f'--output={tmp_path}'])
    assert (tmp_path / 'main.js').exists()


def test_emit_copies_runtime_directory(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_minimal_model())))
    run_main([f'--output={tmp_path}'])
    assert (tmp_path / 'runtime' / 'base.js').exists()
    assert (tmp_path / 'runtime' / 'registry.js').exists()
    assert (tmp_path / 'runtime' / 'deserialize.js').exists()
    assert not (tmp_path / 'runtime' / 'base_test.py').exists()


def test_emit_class_file_imports_language_error(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_minimal_model())))
    run_main([f'--output={tmp_path}'])
    program_js = (tmp_path / 'Program.js').read_text()
    assert "{ Node, Token, LanguageError } = require('./runtime/base')" in program_js


def test_concrete_class_has_rule_name_and_fields(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_arith_model())))
    run_main([f'--output={tmp_path}'])
    content = (tmp_path / 'Term.js').read_text()
    assert '_RULE_NAME' in content
    assert '_FIELDS' in content
    assert 'constructor' in content


def test_abstract_class_has_no_rule_name_or_constructor(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_arith_model())))
    run_main([f'--output={tmp_path}'])
    content = (tmp_path / 'ExprRest.js').read_text()
    assert '_RULE_NAME' not in content
    assert '_FIELDS' not in content
    assert 'constructor' not in content


def test_subclass_requires_parent(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_arith_model())))
    run_main([f'--output={tmp_path}'])
    content = (tmp_path / 'AddRest.js').read_text()
    assert "require('./ExprRest')" in content
    assert 'class AddRest extends ExprRest' in content


def test_body_fragment_placed_in_class(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_arith_model())))
    run_main([f'--output={tmp_path}'])
    content = (tmp_path / 'Term.js').read_text()
    assert 'eval()' in content
    assert 'parseInt(this.num.lexeme)' in content


def test_top_fragment_placed_before_requires(tmp_path, monkeypatch):
    model = _minimal_model()
    model['semantic_sections'] = [{"language": "javascript", "fragments": [
        {"class_name": "Program", "kind": "top", "body": "'use strict';"}
    ]}]
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])
    content = (tmp_path / 'Program.js').read_text()
    assert content.index("'use strict';") < content.index("require(")


def test_import_fragment_placed_before_class(tmp_path, monkeypatch):
    model = _minimal_model()
    model['semantic_sections'] = [{"language": "javascript", "fragments": [
        {"class_name": "Program", "kind": "import", "body": "const fs = require('fs');"}
    ]}]
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])
    content = (tmp_path / 'Program.js').read_text()
    assert content.index("const fs = require('fs');") < content.index('class Program')


def test_init_fragment_placed_in_constructor(tmp_path, monkeypatch):
    model = _minimal_model()
    model['classes'][0]['fields'] = [{"name": "x", "type": "Token"}]
    model['semantic_sections'] = [{"language": "javascript", "fragments": [
        {"class_name": "Program", "kind": "init", "body": "this.extra = 42;"}
    ]}]
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])
    content = (tmp_path / 'Program.js').read_text()
    ctor_start = content.index('constructor(')
    ctor_end = content.index('}', ctor_start)
    ctor_body = content[ctor_start:ctor_end]
    assert 'this.extra = 42;' in ctor_body


def test_file_fragment_replaces_entire_file(tmp_path, monkeypatch):
    model = _arith_model()
    model['semantic_sections'][0]['fragments'].append(
        {"class_name": "Env", "kind": "file", "body": "class Env {}\nmodule.exports = { Env };\n"}
    )
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])
    content = (tmp_path / 'Env.js').read_text()
    assert content == "class Env {}\nmodule.exports = { Env };\n"


def test_language_tag_is_case_insensitive(tmp_path, monkeypatch):
    model = _arith_model()
    model['semantic_sections'][0]['language'] = 'JavaScript'
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])
    content = (tmp_path / 'Term.js').read_text()
    assert 'parseInt(this.num.lexeme)' in content


def test_emit_generated_main_is_runnable(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_arith_model())))
    run_main([f'--output={tmp_path}'])
    result = subprocess.run(
        ['node', str(tmp_path / 'main.js')],
        input='', capture_output=True, text=True,
    )
    assert result.returncode == 0


@pytest.mark.skip(reason="timing-sensitive: readline EOF races with SIGINT when subprocess.communicate() closes stdin")
def test_emit_generated_main_exits_130_on_sigint(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_arith_model())))
    run_main([f'--output={tmp_path}'])
    env = {k: v for k, v in os.environ.items() if not k.startswith('COV_CORE')}
    proc = subprocess.Popen(
        ['node', str(tmp_path / 'main.js')],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env=env,
    )
    time.sleep(0.1)
    proc.send_signal(signal.SIGINT)
    try:
        stdout, stderr = proc.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
        pytest.fail("subprocess did not exit after SIGINT within 5 seconds")
    assert proc.returncode == 130
    assert b'Traceback' not in stderr
    assert b'User interrupted execution by ^C.' in stdout


def test_default_run_returns_instead_of_printing(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_minimal_model())))
    run_main([f'--output={tmp_path}'])
    start_js = (tmp_path / '_Start.js').read_text()
    assert 'return String(this);' in start_js
    assert 'console.log' not in start_js


def test_emit_generated_main_result_value_is_unquoted_string(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_arith_model())))
    run_main([f'--output={tmp_path}'])
    tree_json = json.dumps({
        "kind": "tree",
        "rule": "program",
        "children": [
            ["expr", {
                "kind": "tree", "rule": "Expr", "children": [
                    ["term", {"kind": "tree", "rule": "Term", "children": [
                        ["num", {"kind": "token", "name": "NUM", "lexeme": "3"}]
                    ]}],
                    ["rest", {"kind": "tree", "rule": "ExprRest", "children": []}]
                ]
            }]
        ]
    })
    result = subprocess.run(
        ['node', str(tmp_path / 'main.js')],
        input=tree_json + '\n',
        capture_output=True,
        text=True,
    )
    records = [json.loads(l) for l in result.stdout.splitlines() if l]
    result_records = [r for r in records if r.get('kind') == 'result']
    assert result_records, f"No result record found in: {result.stdout}"
    assert result_records[0]['value'] == '3'


def test_emit_generated_main_non_string_return_is_specification_error(tmp_path, monkeypatch):
    model = _arith_model()
    model['semantic_sections'][0]['fragments'][0] = {
        "class_name": "Program", "kind": "body",
        "body": "_run() {\n    return this.expr.eval();\n}"
    }
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])
    tree_json = json.dumps({
        "kind": "tree",
        "rule": "program",
        "children": [
            ["expr", {
                "kind": "tree", "rule": "Expr", "children": [
                    ["term", {"kind": "tree", "rule": "Term", "children": [
                        ["num", {"kind": "token", "name": "NUM", "lexeme": "3"}]
                    ]}],
                    ["rest", {"kind": "tree", "rule": "ExprRest", "children": []}]
                ]
            }]
        ]
    })
    result = subprocess.run(
        ['node', str(tmp_path / 'main.js')],
        input=tree_json + '\n',
        capture_output=True,
        text=True,
    )
    records = [json.loads(l) for l in result.stdout.splitlines() if l]
    spec_error_records = [r for r in records if r.get('kind') == 'specification_error']
    assert spec_error_records, f"No specification_error record found in: {result.stdout}"
    assert 'must return a string' in spec_error_records[0]['message']
    assert result.returncode != 0
