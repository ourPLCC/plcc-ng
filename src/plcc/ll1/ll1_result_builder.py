from plcc.spec.syntax.validations.ll1.Grammar import Grammar
from plcc.spec.syntax.validations.ll1.build_first_sets import build_first_sets
from plcc.spec.syntax.validations.ll1.build_follow_sets import build_follow_sets
from plcc.spec.syntax.validations.ll1.build_parsing_table import build_parsing_table
from plcc.spec.syntax.validations.ll1.check_parsing_table_for_ll1 import check_parsing_table_for_ll1
from plcc.spec.syntax.validations.ll1.check_left_recursion import check_left_recursion


def build_ll1_result(grammar: Grammar, productions: dict, arbno_rules: dict = None) -> dict:
    if arbno_rules is None:
        arbno_rules = {}
    eps = grammar.getEpsilon()
    eof = grammar.getEof()

    internal_nts = set(arbno_rules) | {nt + "#" for nt in arbno_rules}

    try:
        lr_cycles = check_left_recursion(grammar)
    except (IndexError, TypeError):
        lr_cycles = []
    firsts = build_first_sets(grammar)
    follows = build_follow_sets(grammar, firsts)
    table = build_parsing_table(firsts, follows, grammar)
    conflict_errors = check_parsing_table_for_ll1(table)

    def tok(t):
        if t is eps:
            return ""
        if t is eof:
            return "eof"
        return t

    nts = sorted(
        nt for nt in grammar.getNonterminalSet()
        if nt not in internal_nts
    )

    first_sets = {nt: sorted(tok(t) for t in firsts[nt]) for nt in nts}
    follow_sets = {nt: sorted(tok(t) for t in follows[nt]) for nt in nts}

    predict_sets = {}
    for nt in nts:
        nt_preds = []
        for prod in grammar.getForms(nt):
            prod_first = firsts.get(prod, set())
            pset = {tok(t) for t in prod_first if t is not eps}
            if eps in prod_first:
                pset.update(tok(t) for t in follows[nt])
            nt_preds.append(sorted(pset))
        predict_sets[nt] = nt_preds

    bad_cells = {(e.cell[0], e.cell[1]) for e in conflict_errors}

    parse_table = {}
    for (nt, t) in table.getKeys():
        if nt in internal_nts:
            continue
        if (nt, t) in bad_cells:
            continue
        cell = table.getCell(nt, t)
        if len(cell) != 1:
            continue
        prod = next(iter(cell))
        lookahead = tok(t)
        parse_table.setdefault(nt, {})[lookahead] = _prod_entry(nt, prod, productions, eps)

    conflicts = []

    def cell_sort_key(cell):
        nt, t = cell
        return (nt, tok(t))

    for (nt, t) in sorted(bad_cells, key=cell_sort_key):
        if nt in internal_nts:
            continue
        prods = table.getCell(nt, t)
        lookahead = tok(t)
        conflict_productions = [
            _prod_entry(nt, p, productions, eps)
            for p in sorted(prods, key=str)
        ]
        conflicts.append({"nonterminal": nt, "lookahead": lookahead, "productions": conflict_productions})

    left_recursion = []
    for offending in lr_cycles:
        cycle = [rule[0] for rule in offending] + [offending[-1][1][0]]
        left_recursion.append({"cycle": cycle})

    arbno_out = {}
    for nt, entry in arbno_rules.items():
        if entry["rhs"]:
            first_item = entry["rhs"][0]
            first_sym = first_item["symbol"]
            if first_item["is_terminal"]:
                lookahead = [first_sym]
            else:
                fset = firsts.get(first_sym, set())
                lookahead = sorted(t for t in fset if t is not eps and t is not eof)
        else:
            lookahead = []
        arbno_out[nt] = {**entry, "lookahead": lookahead}

    return {
        "is_ll1": not (conflicts or left_recursion),
        "start_symbol": grammar.getStartSymbol(),
        "first_sets": first_sets,
        "follow_sets": follow_sets,
        "predict_sets": predict_sets,
        "parse_table": parse_table,
        "conflicts": conflicts,
        "left_recursion": left_recursion,
        "arbno": arbno_out,
    }


def _prod_entry(nt: str, prod: tuple, productions: dict, eps) -> dict:
    rule = productions.get((nt, prod))
    alt = rule.alt if rule is not None else None
    fields = rule.fields if rule is not None else [None] * len(prod)
    return {
        "alt": alt,
        "production": [
            {"symbol": sym, "field": fld}
            for sym, fld in zip(prod, fields)
            if sym is not eps
        ],
    }
