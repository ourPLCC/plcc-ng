import subprocess
from pathlib import Path

RUNTIME_DIR = Path(__file__).parent


def _node(code):
    return subprocess.run(
        ['node', '-e', code],
        capture_output=True, text=True,
        cwd=str(RUNTIME_DIR),
    )


def test_node_is_a_class():
    r = _node("const { Node } = require('./base'); console.log(new Node() instanceof Node);")
    assert r.returncode == 0
    assert r.stdout.strip() == 'true'


def test_token_stores_kind_and_lexeme():
    r = _node("const { Token } = require('./base'); const t = new Token('NUM', '42'); console.log(t.kind, t.lexeme);")
    assert r.returncode == 0
    assert r.stdout.strip() == 'NUM 42'


def test_token_tostring_returns_lexeme():
    r = _node("const { Token } = require('./base'); const t = new Token('NUM', '42'); console.log(String(t));")
    assert r.returncode == 0
    assert r.stdout.strip() == '42'


def test_token_is_not_a_node():
    r = _node("const { Node, Token } = require('./base'); console.log(new Token('X', 'x') instanceof Node);")
    assert r.returncode == 0
    assert r.stdout.strip() == 'false'


def test_language_error_is_a_class():
    r = _node("const { LanguageError } = require('./base'); console.log(typeof LanguageError);")
    assert r.returncode == 0
    assert r.stdout.strip() == 'function'


def test_language_error_instance_is_error():
    r = _node("const { LanguageError } = require('./base'); const e = new LanguageError('oops'); console.log(e instanceof Error);")
    assert r.returncode == 0
    assert r.stdout.strip() == 'true'


def test_language_error_subclass_is_language_error():
    r = _node("""
const { LanguageError } = require('./base');
class MyError extends LanguageError {}
const e = new MyError('bad');
console.log(e instanceof LanguageError);
""")
    assert r.returncode == 0
    assert r.stdout.strip() == 'true'
