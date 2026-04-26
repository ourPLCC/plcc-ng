class Registry:
    def __init__(self):
        self._by_rule = {}

    def register(self, *classes):
        for cls in classes:
            if getattr(cls, '_abstract', False):
                continue
            rule_name = cls._rule_name
            fields = frozenset(cls._fields)
            self._by_rule.setdefault(rule_name, {})[fields] = cls

    def lookup(self, rule_name, field_names):
        candidates = self._by_rule.get(rule_name)
        if candidates is None:
            raise KeyError(f"No class registered for rule '{rule_name}'")
        key = frozenset(field_names)
        cls = candidates.get(key)
        if cls is None:
            raise KeyError(
                f"No class for rule '{rule_name}' with fields {set(field_names)}"
            )
        return cls

    def deserialize(self, tree):
        from .deserialize import deserialize
        return deserialize(tree, self)
