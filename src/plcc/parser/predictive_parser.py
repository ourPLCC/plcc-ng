class Tracer:
    def __init__(self):
        self._events = []
        self._depth = 0

    def push(self, sym):
        self._depth += 1

    def pop(self):
        self._depth -= 1

    def predict(self, sym, lookahead, production):
        self._events.append({
            "event": "predict",
            "sym": sym,
            "lookahead": lookahead,
            "production": production,
            "depth": self._depth,
        })

    def shift(self, token):
        self._events.append({
            "event": "shift",
            "name": token["name"],
            "lexeme": token["lexeme"],
            "source": token.get("source", {}),
            "depth": self._depth,
        })

    def complete(self, rule):
        self._events.append({
            "event": "complete",
            "rule": rule,
            "depth": self._depth,
        })

    @property
    def events(self):
        return list(self._events)


class ParseError(Exception):
    def __init__(self, message, source=None, found=None):
        super().__init__(message)
        self.source = source or {}
        self.found = found


class NodeBuilder:
    def __init__(self, rule):
        self.rule = rule
        self.children = []
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


def parse(ll1: dict, tokens: list, tracer=None) -> tuple:
    """
    Parse tokens against the LL(1) parse table.

    ll1    — dict with keys: start_symbol, parse_table, arbno (optional)
    tokens — list of token dicts (may include a trailing 'eof' sentinel)
    tracer — optional Tracer; records predict/shift/complete events when provided

    Returns (tree_dict, consumed_count, extensible).
    Raises ParseError on any syntax error.
    """
    parse_table = ll1["parse_table"]
    arbno = ll1.get("arbno", {})
    start = ll1["start_symbol"]
    cursor = [0]
    extensible = [False]

    SENTINEL = {"name": "eof", "lexeme": "", "source": {"file": "", "line": 0, "column": 0}}

    def current():
        return tokens[cursor[0]] if cursor[0] < len(tokens) else SENTINEL

    def advance():
        tok = tokens[cursor[0]]
        cursor[0] += 1
        return tok

    def _display_name(token_name):
        return "end of file" if token_name == "eof" else repr(token_name)

    def expect(sym):
        tok = current()
        if tok["name"] != sym:
            raise ParseError(
                f"expected {sym!r}, got {_display_name(tok['name'])}",
                source=tok["source"],
                found=tok["name"],
            )
        tok = advance()
        if tracer:
            tracer.shift(tok)
        return tok

    def is_nonterminal(sym):
        return sym in parse_table or sym in arbno

    def parse_nt(sym):
        if sym in arbno:
            return _parse_arbno(sym)
        return _parse_regular(sym)

    def _parse_regular(sym):
        lookahead = current()["name"]
        nt_table = parse_table.get(sym)
        if nt_table is None:
            raise ParseError(
                f"no parse table entry for nonterminal {sym!r}",
                source=current()["source"],
            )
        production = nt_table.get(lookahead)
        if production is None:
            raise ParseError(
                f"unexpected {_display_name(lookahead)}, no production for {sym!r}",
                source=current()["source"],
                found=lookahead,
            )
        # The parse reached eof here but a real terminal could have continued
        # this nonterminal — the sentence is a prefix of a longer one.
        if lookahead == "eof" and any(k != "eof" for k in nt_table):
            extensible[0] = True
        production_name = production.get("alt") or sym
        if tracer:
            tracer.predict(sym, lookahead, production_name)
            tracer.push(sym)
        builder = NodeBuilder(production_name)
        for entry in production["production"]:
            s, f = entry["symbol"], entry["field"]
            if is_nonterminal(s):
                child_builder = parse_nt(s)
                builder.note_span_from(child_builder)
                if f is not None:
                    builder.children.append([f, child_builder.to_node()])
            else:
                tok = expect(s)
                builder.note_token(tok)
                if f is not None:
                    builder.children.append([f, tok])
        if tracer:
            tracer.pop()
            tracer.complete(production_name)
        return builder

    def _parse_arbno(sym):
        entry = arbno[sym]
        lookahead_set = set(entry["lookahead"])
        separator = entry["separator"]
        rhs = entry["rhs"]
        builder = NodeBuilder(sym)
        list_fields = {item["field"]: [] for item in rhs}

        def parse_iteration():
            if tracer:
                tracer.push(sym)
            for item in rhs:
                if item["is_terminal"]:
                    tok = expect(item["symbol"])
                    builder.note_token(tok)
                    list_fields[item["field"]].append(tok)
                else:
                    child_builder = parse_nt(item["symbol"])
                    builder.note_span_from(child_builder)
                    list_fields[item["field"]].append(child_builder.to_node())
            if tracer:
                tracer.pop()

        if current()["name"] in lookahead_set:
            if tracer:
                tracer.predict(sym, current()["name"], None)
            parse_iteration()
            if tracer:
                tracer.complete(sym)
            if separator:
                while current()["name"] == separator:
                    expect(separator)
                    if tracer:
                        tracer.predict(sym, current()["name"], None)
                    parse_iteration()
                    if tracer:
                        tracer.complete(sym)
            else:
                while current()["name"] in lookahead_set:
                    if tracer:
                        tracer.predict(sym, current()["name"], None)
                    parse_iteration()
                    if tracer:
                        tracer.complete(sym)

        for field, values in list_fields.items():
            builder.children.append([field, values])

        # Sitting at eof where another iteration could have started: extensible.
        if current()["name"] == "eof" and lookahead_set:
            extensible[0] = True

        return builder

    root_builder = parse_nt(start)
    return root_builder.to_node(), cursor[0], extensible[0]
