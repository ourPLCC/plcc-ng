#!/usr/bin/env bash
set -euo pipefail

if command -v pdm &>/dev/null; then
    exit 0
fi

pip install --quiet pdm
