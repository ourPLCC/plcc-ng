import re

_TERMINAL_RE = re.compile(r'^[A-Z][A-Z0-9_]*$')


def format_conflict_message(conflict: dict) -> str:
    nt = conflict["nonterminal"]
    lookahead = conflict["lookahead"]
    conflict_type = conflict.get("conflict_type", "first_first")
    productions = conflict["productions"]

    lines = [
        f"LL(1) conflict: {_nt(nt)} on lookahead {lookahead}",
        "",
        "  All of these productions apply:",
    ]
    for prod in productions:
        lines.append(f"    {_render_production(nt, prod)}")
    lines.append("")

    if conflict_type == "first_follow":
        lines.extend(_first_follow_lines(nt, lookahead))
    else:
        lines.extend(_first_first_lines(nt, lookahead, productions))

    return "\n".join(lines)


def _nt(name: str) -> str:
    return f"<{name}>"


def _render_symbol(sym: str) -> str:
    if _TERMINAL_RE.match(sym):
        return sym
    return _nt(sym)


def _render_production(nt: str, production_entry: dict) -> str:
    symbols = production_entry["production"]
    lhs = _nt(nt)
    if not symbols:
        return f"{lhs} ::=    (empty)"
    rhs = " ".join(_render_symbol(s["symbol"]) for s in symbols)
    return f"{lhs} ::= {rhs}"


def _first_follow_lines(nt: str, lookahead: str) -> list[str]:
    return [
        f"  This is a FIRST/FOLLOW conflict: {lookahead} can start the non-empty production(s)",
        f"  above, but also appears in the FOLLOW set of {_nt(nt)}, making the empty",
        f"  production ambiguous here.",
        "",
        f"  Tip: look at the rule(s) that use {_nt(nt)} — one of them places",
        f"  {lookahead} in a position that follows {_nt(nt)}, creating the ambiguity.",
        f"  This often means the grammar is genuinely ambiguous (e.g., the",
        f"  dangling-else problem) and must be restructured.",
    ]


def _first_first_lines(nt: str, lookahead: str, productions: list[dict]) -> list[str]:
    # Filled in Tasks 4 and 5
    return []
