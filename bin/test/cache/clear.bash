#!/usr/bin/env bash
set -euo pipefail

removed=0
for f in /tmp/plcc-test-*.log /tmp/plcc-test-*.log.meta; do
    [[ -f "$f" ]] || continue
    rm "$f"
    echo "removed $f"
    (( removed++ )) || true
done

if (( removed == 0 )); then
    echo "no cache files found"
fi
