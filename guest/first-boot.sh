#!/bin/sh
set -eu
root=/
# pacman's GnuPG agent inherits the setup process's stdout/stderr pipes.
# Close it before returning so Android can observe the completed first boot.
trap 'gpgconf --homedir "$root/etc/pacman.d/gnupg" --kill all >/dev/null 2>&1 || true' EXIT
if [ ! -s "$root/etc/machine-id" ]; then
    chmod u+w "$root/etc/machine-id"
    tr -d '-' < /proc/sys/kernel/random/uuid > "$root/etc/machine-id"
    chmod 444 "$root/etc/machine-id"
fi
# libalpm canonicalizes these paths inside libc, so supply real app paths.
mkdir -p "$root/etc/pacman.d/gnupg" "$root/var/lib/pacman" "$root/var/cache/pacman/pkg" "$root/var/log"
cat > "$root/etc/pacman.d/arlinux.conf" <<EOF
RootDir = $root
DBPath = $root/var/lib/pacman
CacheDir = $root/var/cache/pacman/pkg
LogFile = $root/var/log/pacman.log
GPGDir = $root/etc/pacman.d/gnupg
HookDir = $root/etc/pacman.d/hooks
DisableSandboxFilesystem
EOF
if ! grep -q '^Include = /etc/pacman.d/arlinux.conf$' "$root/etc/pacman.conf"; then
    sed -i '/^\[options\]/a Include = /etc/pacman.d/arlinux.conf' "$root/etc/pacman.conf"
fi
# Android already assigns this APK its UID; it cannot switch to the ALPM user.
# The tested Android kernel does not implement Landlock.
sed -i '/^DownloadUser[[:space:]]*=/d' "$root/etc/pacman.conf"
mkdir -p "$root/etc/ld.so.conf.d"
ldconfig
# Android supplies identity and service management. Keep package scriptlets
# and desktop-cache hooks, but omit Linux boot/service-account operations.
mkdir -p "$root/etc/pacman.d/hooks"
for hook in 20-systemd-sysusers.hook 21-systemd-tmpfiles.hook \
            10-openssh-mark-sshd-for-restart.hook \
            60-mkinitcpio-remove.hook 90-mkinitcpio-install.hook; do
    ln -sfn /dev/null "$root/etc/pacman.d/hooks/$hook"
done
[ -f "$root/etc/pacman.d/gnupg/arlinux-populated" ] || {
    echo 'Bundle is missing its prebuilt pacman trust database' >&2; exit 1;
}
# Omarchy-only packages come from archlinuxcn. Keep it after the official
# repositories so it cannot replace the base Arch Linux ARM runtime.
if ! grep -q '^\[archlinuxcn\]$' "$root/etc/pacman.conf"; then
    printf '\n' >> "$root/etc/pacman.conf"
    cat "$root/usr/lib/arlinux/guest/archlinuxcn.conf" >> "$root/etc/pacman.conf"
fi
# Published desktops contain all packages; never use the network during setup.
[ -f /usr/share/arlinux/offline-desktop ] || {
    echo 'Incomplete desktop bundle: import a prepared offline distribution ZIP.' >&2
    exit 1
}
guest=$root/usr/lib/arlinux/guest
# Guest Tools' OpenCode launcher appends this distribution note to its own
# managed instructions and provides the shared arlinux Python package.
mkdir -p "$root/etc/arlinux" "$HOME/.config/opencode/skills"
cp "$guest/opencode-omarchy-AGENTS.md" "$root/etc/arlinux/opencode-AGENTS.md"
skill=$HOME/.config/opencode/skills/omarchy
if [ ! -e "$skill" ] && [ ! -L "$skill" ]; then
    ln -s "$guest/opencode-omarchy-skill" "$skill"
fi

mkdir -p "$root/etc/pulse/client.conf.d" "$root/etc/alsa/conf.d"
printf 'default-server = unix:%s/runtime/pulse-native\nautospawn = no\nenable-shm = no\n' \
    "$BIONICX_FILES" > "$root/etc/pulse/client.conf.d/arlinux.conf"
cat > "$root/etc/alsa/conf.d/99-arlinux-pulse.conf" <<'ALSA'
pcm.!default { type pulse }
ctl.!default { type pulse }
ALSA
