#!/usr/bin/env bash
set -euo pipefail

STATS_LOG="${PLCC_TEST_STATS_LOG:-/tmp/plcc-test-cache-stats.log}"

if [[ ! -f "${STATS_LOG}" ]]; then
    echo "no stats yet"
    exit 0
fi

awk '
{
    event = $2
    script = $3
    total++
    events[event]++
    per_script_total[script]++
    per_script_event[script "_" event]++
}
END {
    hits   = events["hit"]   + 0
    misses = events["miss"]  + 0
    skips  = events["skip"]  + 0
    rate   = (total > 0) ? int(hits / total * 100 + 0.5) : 0
    printf "Total: %d  Hits: %d  Misses: %d  Skips: %d  Hit rate: %d%%\n",
        total, hits, misses, skips, rate
    print ""
    print "Per-script breakdown:"
    for (s in per_script_total) {
        h = per_script_event[s "_hit"]   + 0
        m = per_script_event[s "_miss"]  + 0
        k = per_script_event[s "_skip"]  + 0
        t = per_script_total[s]
        printf "  %-20s  total=%-4d  hits=%-4d  misses=%-4d  skips=%-4d\n",
            s, t, h, m, k
    }
}
' "${STATS_LOG}"
