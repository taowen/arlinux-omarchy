#!/usr/bin/env bash
set -euo pipefail
product="$(cd "$(dirname "$0")/.." && pwd)"
export ARLINUX_DIR="${ARLINUX_DIR:-$product/third_party/arlinux}"
export ANHYPRLAND_DIR="${ANHYPRLAND_DIR:-$(dirname "$ARLINUX_DIR")/anhyprland}"
"$ARLINUX_DIR/tools/build.sh" ndk
"$ARLINUX_DIR/tools/build.sh" mesa
"$ARLINUX_DIR/third_party/libhybris/tools/build-aarch64.sh" --incremental
python3 "$ANHYPRLAND_DIR/android/build-deps.py" \
  scanner hyprutils hyprlang glslang muparser libzip tomlplusplus \
  libjpeg-turbo libwebp re2 libxkbcommon lunasvg lcms wayland-protocols \
  libeis libxcursor libxcb-errors libxrender libxfixes lua file \
  hyprcursor hyprgraphics aquamarine
python3 "$ANHYPRLAND_DIR/android/build-core.py"
