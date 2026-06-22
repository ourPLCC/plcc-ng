import subprocess
from pathlib import Path

RUNTIME_DIR = Path(__file__).parent


def _node(code):
    return subprocess.run(
        ['node', '-e', code],
        capture_output=True, text=True,
        cwd=str(RUNTIME_DIR),
    )


def test_deserialize_token_node():
    r = _node("""
const { deserialize } = require('./deserialize');
const { Token } = require('./base');
const t = deserialize({ kind: 'token', name: 'NUM', lexeme: '42' }, null);
console.log(t instanceof Token, t.kind, t.lexeme);
""")
    assert r.returncode == 0
    assert r.stdout.strip() == 'true NUM 42'


def test_deserialize_rule_node_with_token_field():
    r = _node("""
const { deserialize } = require('./deserialize');
const { Registry } = require('./registry');
const { Token } = require('./base');
class Num {
    static _RULE_NAME = 'num'; static _FIELDS = ['val'];
    constructor(val) { this.val = val; }
}
const reg = new Registry(); reg.register(Num);
const node = deserialize({
    kind: 'rule', rule: 'num',
    children: [['val', { kind: 'token', name: 'INT', lexeme: '5' }]]
}, reg);
console.log(node instanceof Num, node.val instanceof Token, node.val.lexeme);
""")
    assert r.returncode == 0
    assert r.stdout.strip() == 'true true 5'


def test_deserialize_nested_rule_nodes():
    r = _node("""
const { deserialize } = require('./deserialize');
const { Registry } = require('./registry');
class Inner {
    static _RULE_NAME = 'inner'; static _FIELDS = [];
    constructor() {}
}
class Outer {
    static _RULE_NAME = 'outer'; static _FIELDS = ['inner'];
    constructor(inner) { this.inner = inner; }
}
const reg = new Registry(); reg.register(Inner, Outer);
const node = deserialize({
    kind: 'rule', rule: 'outer',
    children: [['inner', { kind: 'rule', rule: 'inner', children: [] }]]
}, reg);
console.log(node instanceof Outer, node.inner instanceof Inner);
""")
    assert r.returncode == 0
    assert r.stdout.strip() == 'true true'


def test_deserialize_list_field():
    r = _node("""
const { deserialize } = require('./deserialize');
const { Registry } = require('./registry');
const { Token } = require('./base');
class Lst {
    static _RULE_NAME = 'lst'; static _FIELDS = ['items'];
    constructor(items) { this.items = items; }
}
const reg = new Registry(); reg.register(Lst);
const node = deserialize({
    kind: 'rule', rule: 'lst',
    children: [['items', [
        { kind: 'token', name: 'N', lexeme: '1' },
        { kind: 'token', name: 'N', lexeme: '2' },
    ]]]
}, reg);
console.log(Array.isArray(node.items), node.items.length, node.items[0].lexeme);
""")
    assert r.returncode == 0
    assert r.stdout.strip() == 'true 2 1'
