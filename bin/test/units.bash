#!/usr/bin/env bash

set -euo pipefail

pdm install
pdm test -v "$@"
