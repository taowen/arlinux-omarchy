#!/bin/bash
set -euo pipefail
export OMARCHY_PATH="$BIONICX_ROOTFS/usr/share/omarchy"
export PATH="$BIONICX_ROOTFS/usr/lib/arlinux/guest/bin:$OMARCHY_PATH/bin:$PATH"
export XDG_CONFIG_HOME="$HOME/.config" XDG_STATE_HOME="$HOME/.local/state" XDG_CACHE_HOME="$HOME/.cache"
export WAYLAND_DISPLAY=wayland-0
export QT_LINUX_ACCESSIBILITY_ALWAYS_ON=1
mkdir -p "$XDG_CONFIG_HOME" "$XDG_STATE_HOME/omarchy/current" "$XDG_CACHE_HOME"
mkdir -p "$HOME/Desktop" "$HOME/Documents" "$HOME/Downloads" "$HOME/Pictures"
mkdir -p "$XDG_CONFIG_HOME/gtk-3.0"
if [[ ! -f $XDG_CONFIG_HOME/gtk-3.0/settings.ini ]]; then
  cat > "$XDG_CONFIG_HOME/gtk-3.0/settings.ini" <<'GTK'
[Settings]
gtk-theme-name=Adwaita-dark
gtk-icon-theme-name=Papirus-Dark
gtk-font-name=Sans 11
gtk-application-prefer-dark-theme=1
GTK
fi
if [[ ! -f $XDG_STATE_HOME/omarchy/android-configured ]]; then
  cp -rn "$OMARCHY_PATH/config/." "$XDG_CONFIG_HOME/"
  cp "$BIONICX_ROOTFS/usr/lib/arlinux/guest/shell.json" "$XDG_CONFIG_HOME/omarchy/shell.json"
  if [[ ! -d $XDG_STATE_HOME/omarchy/current/theme ]]; then
    rm -rf "$XDG_STATE_HOME/omarchy/current/next-theme"
    cp -a "$OMARCHY_PATH/themes/tokyo-night" "$XDG_STATE_HOME/omarchy/current/next-theme"
    omarchy-theme-set-templates
    mv "$XDG_STATE_HOME/omarchy/current/next-theme" "$XDG_STATE_HOME/omarchy/current/theme"
    printf 'tokyo-night\n' > "$XDG_STATE_HOME/omarchy/current/theme.name"
    ln -s "$XDG_STATE_HOME/omarchy/current/theme/backgrounds/0-winding-road.webp" "$XDG_STATE_HOME/omarchy/current/background"
  fi
  mkdir -p "$HOME/.local/share/applications"
  cp "$BIONICX_ROOTFS/usr/lib/arlinux/guest/arlinux-omarchy-terminal.desktop" "$HOME/.local/share/applications/"
  printf 'arlinux-omarchy-terminal.desktop\n' > "$XDG_CONFIG_HOME/xdg-terminals.list"
  if [[ ! -f $XDG_CONFIG_HOME/mimeapps.list ]]; then
    printf '[Default Applications]\nx-scheme-handler/http=arlinux-browser.desktop\nx-scheme-handler/https=arlinux-browser.desktop\n' > "$XDG_CONFIG_HOME/mimeapps.list"
  fi
  # Thunar's details view exposes file rows and names through standard AT-SPI;
  # its GTK icon view exposes only the containing pane.
  xfconf-query -c thunar -p /last-view -n -t string -s ThunarDetailsView
  touch "$XDG_STATE_HOME/omarchy/android-configured"
fi
for ((attempt=0; attempt<100; attempt++)); do
  for socket in "$XDG_RUNTIME_DIR"/hypr/*/.socket.sock; do
    if [[ -S $socket ]]; then
      signature=${socket%/.socket.sock}
      signature=${signature##*/}
      # A force-stopped Android process can leave an old socket inode behind.
      # Select a responding compositor, not merely the first pathname.
      if HYPRLAND_INSTANCE_SIGNATURE="$signature" timeout 1 hyprctl -j monitors >/dev/null 2>&1; then
        export HYPRLAND_INSTANCE_SIGNATURE="$signature"
        break 2
      fi
    fi
  done
  sleep 0.1
done
: "${HYPRLAND_INSTANCE_SIGNATURE:?Hyprland IPC socket missing}"
# Host key bindings enter this same guest session, including its D-Bus bus.
export -p > "$XDG_RUNTIME_DIR/omarchy-session.env"
hyprctl reload || true
quickshell -n -p "$OMARCHY_PATH/shell" > "$XDG_RUNTIME_DIR/omarchy-shell.log" 2>&1 &
shell_pid=$!
(
  cd "$BIONICX_ROOTFS"
  exec env XDG_SESSION_TYPE=x11 "$BIONICX_ROOTFS/opt/OpenCode/ai.opencode.desktop" \
    --force-renderer-accessibility
) > "$XDG_RUNTIME_DIR/opencode-desktop.log" 2>&1 &
opencode_pid=$!
trap 'kill "$opencode_pid" "$shell_pid" 2>/dev/null || true; rm -f "$XDG_RUNTIME_DIR/omarchy-session.env"' EXIT
wait "$shell_pid"
