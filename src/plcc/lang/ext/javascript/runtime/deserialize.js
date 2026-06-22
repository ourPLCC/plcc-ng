const { Token } = require('./base');

function deserialize(tree, registry) {
    if (tree.kind === 'token') {
        return new Token(tree.name, tree.lexeme);
    }
    const children = tree.children || [];
    const fieldNames = children.map(([name]) => name);
    const cls = registry.lookup(tree.rule, fieldNames);
    const args = children.map(([, val]) => _deserializeValue(val, registry));
    return new cls(...args);
}

function _deserializeValue(val, registry) {
    if (Array.isArray(val)) {
        return val.map(item => _deserializeValue(item, registry));
    }
    if (val && typeof val === 'object' && val.kind === 'token') {
        return new Token(val.name, val.lexeme);
    }
    if (val && typeof val === 'object') {
        return deserialize(val, registry);
    }
    return val;
}

module.exports = { deserialize };
