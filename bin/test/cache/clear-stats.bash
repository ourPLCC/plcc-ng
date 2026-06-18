#!/usr/bin/env bash
set -euo pipefail

stats_log="${PLCC_TEST_STATS_LOG:-/tmp/plcc-test-cache-stats.log}"

if [[ -f "${stats_log}" ]]; then
    rm "${stats_log}"
    echo "removed ${stats_log}"
else
    echo "no stats log found"
fi
