#!/bin/sh
set -eu

root=${BIONICX_ROOTFS:?missing BIONICX_ROOTFS}
files=${BIONICX_FILES:?missing BIONICX_FILES}
guest=$root/usr/lib/arlinux/guest
manifest=$guest/opencode-downloads.tsv

row=$(awk -F '\t' '$1 == "opencode-desktop" { print; exit }' "$manifest")
[ -n "$row" ] || { echo 'OpenCode 下载清单无效' >&2; exit 1; }
old_ifs=$IFS
IFS=$(printf '\t')
set -- $row
IFS=$old_ifs
version=$2
expected=$3
url=$4

marker=$root/opt/OpenCode/.arlinux-version
if [ -x "$root/opt/OpenCode/ai.opencode.desktop" ] &&
        [ "$(cat "$marker" 2>/dev/null || true)" = "$version" ]; then
    exit 0
fi

cache=$files/downloads
package=$cache/opencode-desktop-$version-aarch64.rpm
mkdir -p "$cache"
if [ ! -f "$package" ] ||
        [ "$(sha256sum "$package" | awk '{print $1}')" != "$expected" ]; then
    rm -f "$package.part"
    echo "ARLINUX:正在下载 OpenCode Desktop $version…"
    curl -fL --retry 3 --connect-timeout 20 -o "$package.part" "$url"
    actual=$(sha256sum "$package.part" | awk '{print $1}')
    [ "$actual" = "$expected" ] || {
        rm -f "$package.part"
        echo 'OpenCode Desktop SHA-256 校验失败' >&2
        exit 1
    }
    mv "$package.part" "$package"
fi

echo "ARLINUX:正在安装 OpenCode Desktop $version…"
rm -rf "$root/opt/OpenCode"
# Arch's standard libarchive reads the official RPM payload directly.
bsdtar -xpf "$package" -C "$root"
mkdir -p "$root/usr/bin"
ln -sfn /opt/OpenCode/ai.opencode.desktop "$root/usr/bin/ai.opencode.desktop"
chmod 755 "$root/opt/OpenCode/ai.opencode.desktop" "$root/opt/OpenCode/chrome-sandbox"
printf '%s\n' "$version" > "$marker"
[ -x "$root/opt/OpenCode/ai.opencode.desktop" ] || {
    echo 'OpenCode Desktop 安装后缺少主程序' >&2
    exit 1
}
