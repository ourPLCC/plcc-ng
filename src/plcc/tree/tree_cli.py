"""plcc-tree
    Parse token JSONL from stdin into tree JSONL.

Usage:
    plcc-tree [options] --spec=SPEC_JSON

Options:
    --spec=SPEC_JSON   Path to spec JSON file (output of plcc-spec).
    -h --help          Show this message.
"""

import json
import sys

from docopt import docopt


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    # Phase 1: --spec is accepted for interface compatibility but not yet used.
    # The minimal implementation wraps each token in a tree record unconditionally.
    # Phase 2 will implement a real LL(1) parser using the spec.
    _ = args['--spec']
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        record = json.loads(line)
        if record.get('kind') == 'error':
            # Pass error records through unchanged
            print(json.dumps(record), flush=True)
        elif record.get('kind') == 'token':
            # Wrap each token in a minimal tree record
            tree = {
                'kind': 'tree',
                'rule': 'program',
                'children': [record],
            }
            print(json.dumps(tree), flush=True)
