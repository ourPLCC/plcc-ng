from dataclasses import dataclass

from plcc.spec.syntax.validations.ll1.Grammar import Grammar


@dataclass
class Rule:
    alt: str | None
    fields: list[str | None]


def decode(spec_dict: dict) -> tuple:
    """
    Build a Grammar from a spec JSON dict.

    Returns (grammar, productions, arbno_rules) where:
      grammar      — Grammar with both regular and internal arbno expansion rules
      productions  — dict[(nt_name, prod_tuple)] -> Rule(alt, fields)
      arbno_rules  — dict[nt_name] -> {rhs, separator}
    """
    grammar = Grammar()
    productions = {}
    arbno_rules = {}
    for rule in spec_dict.get("syntax", {}).get("rules", []):
        nt = rule["lhs"]["name"]
        alt = rule["lhs"].get("altName")
        rhs = rule.get("rhsSymbolList", [])
        if "separator" in rule:
            _handle_arbno(grammar, arbno_rules, nt, rhs, rule["separator"])
        elif not rhs:
            grammar.addRule(nt, [])
            productions[(nt, ())] = Rule(alt=alt, fields=[])
        else:
            syms = [s["name"] for s in rhs]
            fields = [_field(s) for s in rhs]
            grammar.addRule(nt, syms)
            productions[(nt, tuple(syms))] = Rule(alt=alt, fields=fields)
    return grammar, productions, arbno_rules


def _handle_arbno(grammar, arbno_rules, nt, rhs, separator_entry):
    separator = separator_entry["name"] if separator_entry else None
    cont = nt + "#"
    syms = [s["name"] for s in rhs]

    # Expand into right-recursive internal rules for LL(1) analysis only.
    grammar.addRule(nt, syms + [cont])
    grammar.addRule(nt, [])
    if separator:
        grammar.addRule(cont, [separator] + syms + [cont])
    else:
        grammar.addRule(cont, syms + [cont])
    grammar.addRule(cont, [])

    arbno_rhs = [
        {
            "field": _arbno_field(s),
            "symbol": s["name"],
            "is_terminal": bool(s.get("isTerminal", False)),
        }
        for s in rhs
        if s.get("isCapturing", False)
    ]
    arbno_rules[nt] = {"rhs": arbno_rhs, "separator": separator}


def _arbno_field(sym: dict) -> str:
    alt = sym.get("altName")
    name = sym["name"]
    return (alt if alt else name).lower() + "List"


def _field(sym: dict) -> str | None:
    """Return the field name for a symbol dict, or None if elided."""
    if not sym.get("isCapturing", False):
        return None
    alt = sym.get("altName")
    name = sym["name"]
    return (alt if alt else name).lower()
