#!/usr/bin/env bash
set -euo pipefail
product="$(cd "$(dirname "$0")" && pwd)"
export ARLINUX_DIR="${ARLINUX_DIR:-$(cd "$product/../.." && pwd)}"
export ANHYPRLAND_DIR="${ANHYPRLAND_DIR:-$ARLINUX_DIR/third_party/anhyprland}"
if [[ ! -f "$ARLINUX_DIR/tools/build-product.py" ]]; then
    echo "Arlinux core not found at $ARLINUX_DIR; set ARLINUX_DIR to its checkout" >&2
    exit 1
fi
export ARLINUX_COMPOSITOR=hyprland
exec python3 "$ARLINUX_DIR/tools/build-product.py" "$product" "$@"
