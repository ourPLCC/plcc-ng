import re

_TERMINAL_RE = re.compile(r'^[A-Z_][A-Z0-9_]*$')


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


def _longest_common_prefix(productions: list[list[dict]]) -> list[dict]:
    if not productions:
        return []
    shortest = min(len(p) for p in productions)
    prefix = []
    for i in range(shortest):
        sym = productions[0][i]["symbol"]
        if all(p[i]["symbol"] == sym for p in productions):
            prefix.append(productions[0][i])
        else:
            break
    return prefix


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
    non_empty = [p["production"] for p in productions if p["production"]]
    lcp = _longest_common_prefix(non_empty)
    tail_nt = nt + "Tail"

    lines = [
        f"  This is a FIRST/FIRST conflict: all productions start with {lookahead}, so",
        f"  the parser cannot choose between them.",
        "",
    ]

    if not lcp:
        lines += [
            f"  Tip: the conflict arises through nullable leading symbols — the productions",
            f"  have no common visible prefix to factor out. The grammar likely needs",
            f"  deeper restructuring to eliminate the ambiguity.",
        ]
    else:
        lines.append(f"  Tip: left-factor the common prefix:")
        lcp_str = " ".join(_render_symbol(s["symbol"]) for s in lcp)
        lines.append(f"    {_nt(nt)} ::= {lcp_str} {_nt(tail_nt)}")
        for prod_syms in non_empty:
            remainder = prod_syms[len(lcp):]
            if remainder:
                rhs = " ".join(_render_symbol(s["symbol"]) for s in remainder)
                lines.append(f"    {_nt(tail_nt)} ::= {rhs}")
            else:
                lines.append(f"    {_nt(tail_nt)} ::=    (empty)")

    return lines
