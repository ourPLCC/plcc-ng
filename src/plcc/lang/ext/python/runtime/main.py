"""Stub Python interpreter — reads parse-tree JSONL, prints evaluation lines."""

import json
import sys


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        tree = json.loads(line)
        kind = tree.get("kind", "unknown")
        rule = tree.get("rule", "unknown")
        print(f"evaluated: {rule} ({kind})", flush=True)


if __name__ == "__main__":
    main()
