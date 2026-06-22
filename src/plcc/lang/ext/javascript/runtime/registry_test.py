import subprocess
from pathlib import Path

RUNTIME_DIR = Path(__file__).parent


def _node(code):
    return subprocess.run(
        ['node', '-e', code],
        capture_output=True, text=True,
        cwd=str(RUNTIME_DIR),
    )


def test_register_and_lookup_by_rule_and_fields():
    r = _node("""
const { Registry } = require('./registry');
class Foo { static _RULE_NAME = 'foo'; static _FIELDS = ['x', 'y']; }
const reg = new Registry();
reg.register(Foo);
console.log(reg.lookup('foo', ['x', 'y']) === Foo);
""")
    assert r.returncode == 0
    assert r.stdout.strip() == 'true'


def test_lookup_unknown_rule_throws():
    r = _node("""
const { Registry } = require('./registry');
const reg = new Registry();
try { reg.lookup('missing', []); console.log('no error'); }
catch(e) { console.log('threw'); }
""")
    assert r.returncode == 0
    assert r.stdout.strip() == 'threw'


def test_lookup_wrong_fields_throws():
    r = _node("""
const { Registry } = require('./registry');
class Foo { static _RULE_NAME = 'foo'; static _FIELDS = ['x']; }
const reg = new Registry();
reg.register(Foo);
try { reg.lookup('foo', ['y']); console.log('no error'); }
catch(e) { console.log('threw'); }
""")
    assert r.returncode == 0
    assert r.stdout.strip() == 'threw'


def test_field_order_does_not_matter():
    r = _node("""
const { Registry } = require('./registry');
class Foo { static _RULE_NAME = 'foo'; static _FIELDS = ['x', 'y']; }
const reg = new Registry();
reg.register(Foo);
console.log(reg.lookup('foo', ['y', 'x']) === Foo);
""")
    assert r.returncode == 0
    assert r.stdout.strip() == 'true'


def test_two_classes_same_rule_different_fields():
    r = _node("""
const { Registry } = require('./registry');
class A { static _RULE_NAME = 'r'; static _FIELDS = ['x']; }
class B { static _RULE_NAME = 'r'; static _FIELDS = ['x', 'y']; }
const reg = new Registry();
reg.register(A, B);
console.log(reg.lookup('r', ['x']) === A, reg.lookup('r', ['x', 'y']) === B);
""")
    assert r.returncode == 0
    assert r.stdout.strip() == 'true true'
