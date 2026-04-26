from .base import Token


def deserialize(tree, registry):
    if tree['kind'] == 'token':
        return Token(kind=tree['name'], lexeme=tree['lexeme'])

    children = tree.get('children', [])
    field_names = [pair[0] for pair in children]
    cls = registry.lookup(tree['rule'], field_names)
    kwargs = {name: deserialize(node, registry) for name, node in children}
    return cls(**kwargs)
