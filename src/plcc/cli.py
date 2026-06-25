import re
import sys

from docopt import DocoptExit, docopt, parse_options


def parse_args(doc, argv):
    try:
        return docopt(doc, argv)
    except DocoptExit as e:
        _reformat_if_cryptic(str(e), doc)
        raise SystemExit(str(e))


def _reformat_if_cryptic(msg, doc):
    m = re.search(r"Option\(([^)]+)\)", msg)
    if not m:
        return
    parts = [p.strip().strip("'") for p in m.group(1).split(",")]
    short, long_ = parts[0], parts[1]
    opt = long_ if long_ != "None" else short
    opts = parse_options(doc)
    known = {o.short for o in opts if o.short} | {o.longer for o in opts if o.longer}
    kind = "duplicate" if (short in known or long_ in known) else "unrecognized"
    usage = re.search(r"(Usage:.*)", msg, re.DOTALL)
    usage_str = usage.group(1) if usage else ""
    print(f"error: {kind} option '{opt}'\n{usage_str}", file=sys.stderr)
    raise SystemExit(1)
