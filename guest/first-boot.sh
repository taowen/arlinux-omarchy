#!/bin/sh
set -eu
root=${BIONICX_ROOTFS:?missing BIONICX_ROOTFS}
export BIONICX_VIRTUAL_ROOT=1 BIONICX_REWRITE_ABSOLUTE_SYMLINKS=1
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
# Preserve the platform cache generator when glibc is upgraded by pacman.
if ! grep -q '^NoExtract = usr/bin/ldconfig$' "$root/etc/pacman.conf"; then
    sed -i '/^\[options\]/a NoExtract = usr/bin/ldconfig' "$root/etc/pacman.conf"
fi
cp "$root/usr/lib/arlinux-platform/ldconfig" "$root/usr/bin/ldconfig"
chmod 755 "$root/usr/bin/ldconfig"
mkdir -p "$root/etc/ld.so.conf.d"
printf '/usr/lib/arlinux-platform\n/usr/lib\n' > "$root/etc/ld.so.conf.d/arlinux.conf"
ldconfig
# Android supplies identity and service management. Keep package scriptlets
# and desktop-cache hooks, but omit Linux boot/service-account operations.
mkdir -p "$root/etc/pacman.d/hooks"
for hook in 20-systemd-sysusers.hook 21-systemd-tmpfiles.hook \
            10-openssh-mark-sshd-for-restart.hook; do
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
runtime_epoch=$root/var/lib/arlinux/runtime-epoch-1
if [ ! -f "$runtime_epoch" ]; then
    echo 'ARLINUX:Updating the base runtime...'
    pacman -Syy --needed --noconfirm glibc coreutils bash pacman
    mkdir -p "$(dirname "$runtime_epoch")"
    : > "$runtime_epoch"
    exit 75
fi
set -- xterm curl ca-certificates ttf-dejavu noto-fonts-cjk fontconfig xorg-xrdb dbus \
    at-spi2-core python-dbus python-atspi python-gobject python-pip mpg123 \
    wl-clipboard wtype xclip xdotool patch wayland libx11 libxcb libxxf86vm \
    gtk3 nss libxss libxtst libsecret alsa-plugins libpulse \
    cups libdrm mesa pango cairo \
    quickshell qt6-declarative qt6-svg qt6-wayland qt6-multimedia qt6-5compat qt6-imageformats \
    inotify-tools hyprutils hyprwire re2 readline jq socat imagemagick libnotify \
    ttf-jetbrains-mono-nerd noto-fonts bash-completion xdg-utils xdg-terminal-exec neovim thunar papirus-icon-theme
if ! pacman -Q "$@" >/dev/null 2>&1; then
    echo 'ARLINUX:Updating Arch Linux ARM and installing desktop components...'
    pacman -Syyu --needed --noconfirm "$@"
fi

if ! python3 -c 'import dogtail, edge_tts' >/dev/null 2>&1; then
    echo 'ARLINUX:Installing desktop automation and online speech support...'
    python3 -m pip install --break-system-packages --no-cache-dir \
        'dogtail==1.0.5' 'edge-tts==7.2.8'
fi
guest=$root/usr/lib/arlinux/guest
python_source=$root/usr/lib/arlinux/python
mkdir -p "$python_source/arlinux"
cp "$guest/arlinux/"*.py "$python_source/arlinux/"
python_site=$(python3 -c 'import sys; print("python%d.%d/site-packages" % sys.version_info[:2])')
mkdir -p "$root/usr/lib/$python_site"
printf '/usr/lib/arlinux/python\n' > "$root/usr/lib/$python_site/arlinux.pth"

"$root/bin/sh" "$guest/opencode-install.sh"
"$root/bin/sh" "$guest/opencode-instructions.sh"

mkdir -p "$root/etc/pulse/client.conf.d" "$root/etc/alsa/conf.d"
printf 'default-server = unix:%s/runtime/pulse-native\nautospawn = no\nenable-shm = no\n' \
    "$BIONICX_FILES" > "$root/etc/pulse/client.conf.d/arlinux.conf"
cat > "$root/etc/alsa/conf.d/99-arlinux-pulse.conf" <<'ALSA'
pcm.!default { type pulse }
ctl.!default { type pulse }
ALSA

# The compositor runs in Android. Extract only the CLI from the signed Arch
# package, without installing the Linux compositor or its DRM backend. This
# also avoids coupling the client to ARM repository Aquamarine rebuild timing.
if [ ! -x "$root/usr/bin/hyprctl" ]; then
    echo 'ARLINUX:Installing the Hyprland control client...'
    archive=$(pacman -Spdd --print-format '%f' hyprland)
    pacman -Sddw --noconfirm hyprland
    bsdtar -xOf "$root/var/cache/pacman/pkg/$archive" usr/bin/hyprctl > "$root/usr/bin/hyprctl.new"
    chmod 755 "$root/usr/bin/hyprctl.new"
    mv "$root/usr/bin/hyprctl.new" "$root/usr/bin/hyprctl"
    printf '%s\n' "$archive" > "$root/usr/lib/arlinux/hyprctl-package"
fi

# Installed Wayland clients use the distribution's current protocol symbols.
# The graphics overlay contains older bootstrap fallbacks for bare seeds.
for so in libwayland-client.so.0 libwayland-server.so.0 libwayland-egl.so.1; do
    if [ -e "$root/usr/lib/$so" ]; then
        rm -f "$root/usr/lib/arlinux-platform/$so"
    fi
done
