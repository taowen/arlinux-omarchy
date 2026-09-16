#!/usr/bin/env bash
set -euo pipefail
product="$(cd "$(dirname "$0")/.." && pwd)"
export ARLINUX_DIR="${ARLINUX_DIR:-$(cd "$product/../.." && pwd)}"
export ANHYPRLAND_DIR="${ANHYPRLAND_DIR:-$ARLINUX_DIR/third_party/anhyprland}"
if [[ ! -x "$ARLINUX_DIR/tools/build.sh" ]]; then
    echo "Arlinux core not found at $ARLINUX_DIR; set ARLINUX_DIR to its checkout" >&2
    exit 1
fi
"$ARLINUX_DIR/tools/build.sh" ndk
"$ARLINUX_DIR/tools/build.sh" mesa
"$ARLINUX_DIR/third_party/libhybris/tools/build-aarch64.sh" --incremental
python3 "$ANHYPRLAND_DIR/android/build-deps.py" \
  scanner hyprutils hyprlang glslang muparser libzip tomlplusplus \
  libjpeg-turbo libwebp re2 libxkbcommon lunasvg lcms wayland-protocols \
  libeis libxcursor libxcb-errors libxrender libxfixes lua file \
  hyprcursor hyprgraphics aquamarine
python3 "$ANHYPRLAND_DIR/android/build-core.py"
