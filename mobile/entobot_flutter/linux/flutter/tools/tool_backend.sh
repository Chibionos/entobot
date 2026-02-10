#!/usr/bin/env bash
# Local tool_backend.sh - workaround for Arch Linux Flutter AUR package
# missing packages/flutter_tools/bin/tool_backend.sh

set -e

readonly dart_bin="$(which dart)"

exec "${dart_bin}" "$(dirname "$0")/tool_backend.dart" "${@:1}"
