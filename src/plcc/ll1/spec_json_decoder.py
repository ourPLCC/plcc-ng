from plcc.spec.syntax.validations.ll1.Grammar import Grammar


def decode(spec_dict: dict) -> tuple:
    """
    Build a Grammar from a spec JSON dict.

    Returns (grammar, field_map) where:
      grammar   — base Grammar with string symbol keys, compatible with all
                  LL(1) algorithms (build_first_sets, build_follow_sets, etc.)
      field_map — dict[(nt_name, prod_tuple)] -> list[str|None]
                  Maps each production to its per-symbol field names.
                  None means the symbol is elided from the parse tree.
    """
    grammar = Grammar()
    field_map = {}
    for rule in spec_dict.get("syntax", {}).get("rules", []):
        nt = rule["lhs"]["name"]
        rhs = rule.get("rhsSymbolList", [])
        if not rhs:
            grammar.addRule(nt, [])
            field_map[(nt, ())] = []
        else:
            syms = [s["name"] for s in rhs]
            fields = [_field(s) for s in rhs]
            grammar.addRule(nt, syms)
            field_map[(nt, tuple(syms))] = fields
    return grammar, field_map


def _field(sym: dict) -> str | None:
    """Return the field name for a symbol dict, or None if elided."""
    if not sym.get("isCapturing", False):
        return None
    alt = sym.get("altName")
    name = sym["name"]
    return (alt if alt else name).lower()
