class ParseError(Exception):
    pass


class NodeBuilder:
    def __init__(self, rule):
        self.rule = rule
        self.children = []      # [[field, node], ...]
        self.first_tok = None
        self.last_tok = None

    def note_token(self, tok):
        if self.first_tok is None:
            self.first_tok = tok
        self.last_tok = tok

    def note_span_from(self, child_builder):
        if child_builder.first_tok is not None:
            if self.first_tok is None:
                self.first_tok = child_builder.first_tok
            self.last_tok = child_builder.last_tok

    def to_node(self):
        source = {}
        if self.first_tok is not None and self.last_tok is not None:
            fs = self.first_tok["source"]
            ls = self.last_tok["source"]
            source = {
                "file": fs.get("file", ""),
                "line": fs["line"],
                "column": fs["column"],
                "endLine": ls["line"],
                "endColumn": ls["column"] + len(self.last_tok["lexeme"]) - 1,
            }
        return {
            "kind": "tree",
            "rule": self.rule,
            "source": source,
            "children": self.children,
        }


def parse(ll1: dict, tokens: list) -> dict:
    """
    Parse tokens against the LL(1) parse table.

    ll1    — dict with keys: start_symbol, parse_table
    tokens — list of token dicts from plcc-tokens (without $ sentinel)

    Returns the root parse tree dict.
    Raises ParseError on any syntax error.
    """
    parse_table = ll1["parse_table"]
    start = ll1["start_symbol"]
    cursor = [0]

    SENTINEL = {"name": "$", "lexeme": "", "source": {"file": "", "line": 0, "column": 0}}

    def current():
        return tokens[cursor[0]] if cursor[0] < len(tokens) else SENTINEL

    def advance():
        tok = tokens[cursor[0]]
        cursor[0] += 1
        return tok

    result = [None]

    # Stack: items are tuples. Kinds:
    #   ("N", sym, field, parent_builder)
    #   ("T", sym, field, parent_builder)
    #   ("end", rule, field, builder, parent_builder)
    stack = [("N", start, None, None)]

    while stack:
        item = stack.pop()
        kind = item[0]

        if kind == "T":
            _, sym, field, builder = item
            tok = current()
            if tok["name"] != sym:
                raise ParseError(
                    f"expected {sym!r}, got {tok['name']!r} "
                    f"at {tok['source']}"
                )
            tok = advance()
            if builder is not None:
                builder.note_token(tok)
            if field is not None and builder is not None:
                builder.children.append([field, tok])

        elif kind == "N":
            _, sym, field, parent_builder = item
            lookahead = current()["name"]
            nt_table = parse_table.get(sym)
            if nt_table is None:
                raise ParseError(f"no parse table entry for nonterminal {sym!r}")
            production = nt_table.get(lookahead)
            if production is None:
                raise ParseError(
                    f"unexpected {lookahead!r}, no production for {sym!r} "
                    f"at {current()['source']}"
                )
            new_builder = NodeBuilder(sym)
            stack.append(("end", sym, field, new_builder, parent_builder))
            for entry in reversed(production):
                s = entry["symbol"]
                f = entry["field"]
                if s in parse_table:
                    stack.append(("N", s, f, new_builder))
                else:
                    stack.append(("T", s, f, new_builder))

        elif kind == "end":
            _, rule, field, builder, parent_builder = item
            node = builder.to_node()
            if parent_builder is not None:
                parent_builder.note_span_from(builder)
                if field is not None:
                    parent_builder.children.append([field, node])
            else:
                result[0] = node

    tok = current()
    if tok["name"] != "$":
        raise ParseError(
            f"unexpected token {tok['name']!r} after complete parse "
            f"at {tok['source']}"
        )
    return result[0]
