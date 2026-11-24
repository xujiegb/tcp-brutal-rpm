#!/usr/bin/env bash
set -euo pipefail
export LC_ALL=C

cd "$(git rev-parse --show-toplevel)"
original=$(git show HEAD:tcp-brutal.spec)
version=$(sed -nE 's/^Version:[[:blank:]]+([0-9]+\.[0-9]+\.[0-9]+)[[:blank:]]*$/\1/p' <<< "$original")
release=$(sed -nE 's/^Release:[[:blank:]]+([1-9][0-9]*)%\{\?dist\}[[:blank:]]*$/\1/p' <<< "$original")
[[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]
[[ "$release" =~ ^[1-9][0-9]*$ ]]
archive="tcp-brutal-$version.tar.gz"

verify_archive() {
    test -s "$archive"
    tar -tzf "$archive" \
        "tcp-brutal-$version/brutal.h" \
        "tcp-brutal-$version/brutal_cc.c" \
        "tcp-brutal-$version/brutal_rules.c" \
        "tcp-brutal-$version/brutal_sockopt.c" \
        "tcp-brutal-$version/Makefile" \
        "tcp-brutal-$version/tools/brutalctl.c" \
        "tcp-brutal-$version/scripts/mkdkmsconf.sh" >/dev/null
}

expected_spec() {
    sed -E "s|^Source0:.*|Source0:        $archive|" <<< "$original"
}

case "${1:-}" in
    version)
        printf '%s\n' "$version"
        ;;
    archive)
        temp=$(mktemp)
        trap 'rm -f "$temp"' EXIT
        curl --fail --silent --show-error --location --retry 3 \
            --output "$temp" \
            "https://github.com/HyNetworks/tcp-brutal/archive/refs/tags/v$version.tar.gz"
        mv "$temp" "$archive"
        verify_archive
        printf '%s\n' "$archive"
        ;;
    spec)
        verify_archive
        expected_spec > tcp-brutal.spec
        ;;
    verify)
        verify_archive
        diff -u <(expected_spec) tcp-brutal.spec
        ;;
    *)
        exit 2
        ;;
esac
