#!/usr/bin/env bash
set -euo pipefail

versions() {
    SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
    "${SCRIPT_DIR}/../versions.bash"
}

if command -v javac &>/dev/null; then
    versions
    exit 0
fi

sudo apt-get update -qq
sudo apt-get install -y -qq default-jdk

versions
