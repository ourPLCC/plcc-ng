# Sourced by bin/test/*.bash scripts. Not executable.
# Provides run_cached <cache-file> <command> [args...].

_cache_log_event() {
    local event="$1" name="$2"
    local stats_log="${PLCC_TEST_STATS_LOG:-/tmp/plcc-test-cache-stats.log}"
    echo "[cache ${event}] ${name}" >&2
    printf '%s %s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%S)" "${event}" "${name}" \
        >> "${stats_log}"
}

_cache_key() {
    local head status
    head=$(git rev-parse HEAD 2>/dev/null) || return 1
    status=$(git status --porcelain 2>/dev/null) || return 1
    printf '%s\n%s' "${head}" "${status}" | sha256sum | cut -d' ' -f1
}

run_cached() {
    local cache_file="$1"
    shift
    local name
    name=$(basename "${cache_file}" .log)
    name="${name#plcc-test-}"

    if [[ "${PLCC_NO_TEST_CACHE:-}" == "1" ]]; then
        _cache_log_event "skip" "${name}"
        "$@"
        return
    fi

    local key
    if ! key=$(_cache_key); then
        "$@"
        return
    fi

    local meta="${cache_file}.meta"
    if [[ -f "${cache_file}" && -f "${meta}" ]]; then
        local stored_key stored_exit
        stored_key=$(grep '^KEY=' "${meta}" 2>/dev/null | cut -d= -f2-) || true
        stored_exit=$(grep '^EXIT=' "${meta}" 2>/dev/null | cut -d= -f2-) || true
        if [[ "${stored_key}" == "${key}" && "${stored_exit}" =~ ^[0-9]+$ ]]; then
            _cache_log_event "hit" "${name}"
            cat "${cache_file}"
            exit "${stored_exit}"
        fi
    fi

    _cache_log_event "miss" "${name}"
    local exit_code=0
    local _exit_tmp
    _exit_tmp=$(mktemp)
    { "$@" 2>&1; echo "$?" > "${_exit_tmp}"; } | tee "${cache_file}"
    exit_code=$(cat "${_exit_tmp}")
    rm -f "${_exit_tmp}"
    printf 'KEY=%s\nEXIT=%s\n' "${key}" "${exit_code}" > "${meta}"
    exit "${exit_code}"
}
