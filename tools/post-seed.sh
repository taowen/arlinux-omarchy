#!/usr/bin/env bash
set -euo pipefail
rootfs=${1:?rootfs required}
framework=$(cd "$(dirname "$0")/../../.." && pwd)
"$framework/tools/build/seed-pacman-keyring.sh" \
    "$rootfs" archlinuxarm archlinux archlinuxcn
