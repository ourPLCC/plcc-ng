from .base import Token


def deserialize(tree, registry):
    if tree['kind'] == 'token':
        return Token(kind=tree['name'], lexeme=tree['lexeme'])

    children = tree.get('children', [])
    field_names = [pair[0] for pair in children]
    cls = registry.lookup(tree['rule'], field_names)
    kwargs = {name: _deserialize_value(val, registry) for name, val in children}
    return cls(**kwargs)


def _deserialize_value(val, registry):
    if isinstance(val, list):
        return [_deserialize_value(item, registry) for item in val]
    if isinstance(val, dict) and val.get('kind') == 'token':
        return Token(kind=val['name'], lexeme=val['lexeme'])
    if isinstance(val, dict):
        return deserialize(val, registry)
    return val
