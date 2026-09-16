# arlinux-omarchy

Omarchy desktop on Android, packaged as an independent Arlinux application.
It runs Omarchy's Quickshell panel, menus, themes and Hyprland configuration
on Arch Linux ARM. Android hosts the compositor through anhyprland; Linux
applications retain glibc and hardware rendering through Mesa Zink and
Turnip or libhybris.

Application ID: `io.taowen.arlinux.omarchy`. Its rootfs, package database and
home directory belong to this APK, independently of Arlinux Arch and Debian.
Arlinux Arch keeps its separate plain xterm startup; this product does not change it.
Startup shows the Omarchy wallpaper and panel, with no terminal window.
The application menu includes Thunar, Neovim, an optional themed XTerm and the
shared Android WebView browser. Android applications can be opened with `arlinux-app PACKAGE`.

The bundled Omarchy source is the local 4.0.0 alpha / `quattro` revision
`31bd80daa4613ffdee995ac27467fce5a2990806`, pinned in `rootfs.lock.json` and
`third_party/omarchy`. This is an Android port of that desktop, not an Omarchy
bare-metal installation. It does not run the upstream disk, bootloader or
systemd installation scripts.

![Omarchy on Redmi](docs/screenshots/redmi-desktop.png)

Device results and limitations are recorded in [ACCEPTANCE.md](ACCEPTANCE.md).

## Development

This repository is consumed from `arlinux/distributions/omarchy`. The former
Podman product and host build entrypoints have been removed; development now
uses the parent checkout inside WSL 2. Omarchy's upstream source remains pinned
at `third_party/omarchy`, while Arlinux pins anhyprland centrally.

Install the APK and press Start. First boot needs network access to initialize
signed Arch ARM / Arch Linux CN repositories and install desktop packages.
Both repository defaults use Tsinghua TUNA. Existing user mirrors are preserved.
The rootfs archive hash is verified at build time; package signatures remain
required at runtime.

## Desktop

- Super+Enter opens the terminal; Super+number changes workspace.
- Super+Space or the top-left icon opens the Omarchy menu. Super+Alt+Space
  opens the application list. Shortcuts require a physical keyboard.
- Alt+F4 closes a window. Super+mouse drag moves or resizes windows.
- `pacman -Syu` updates Arch; `pacman -S PACKAGE` installs applications.
- `omarchy-launch-browser URL` uses the selected browser desktop entry. The
  initial browser is Arlinux WebView; its private-browsing mode is unsupported.
- `omarchy-theme-set THEME` changes the current Omarchy theme.

Personal shell configuration lives in `~/.config/omarchy/shell.json`.
Hyprland input, binding, appearance and autostart overrides live in
`~/.config/hypr/{input,bindings,looknfeel,autostart}.lua`. The product's Android
bootstrap is `files/anhyprland/hyprland.lua`; it loads the updated guest adapter
on each configuration reload. Current theme files live in
`~/.local/state/omarchy/current/theme`.

Logs are in `$XDG_RUNTIME_DIR/omarchy-shell.log`, `omarchy-launch.log`. Display time follows Android's timezone.

## Accessibility

The panel and application menu expose standard AT-SPI controls. Workspace tabs
are named `Workspace 1`, `Workspace 2`, etc. and expose their selected state.
`Omarchy menu`, menu entries and `Close menu` support the Action interface;
`Search menu` supports EditableText for filtering the application list.
The session enables Qt accessibility and includes Python's `pyatspi` bindings.

Run the accessibility device check below with an empty desktop and closed menu.
It switches workspaces, opens and closes the menu, edits and clears search,
and launches a terminal by its accessible name. Desktop actions use AT-SPI;
Hyprland queries observe the result and close the test terminal.
This coverage does not certify every upstream plugin or Android TalkBack
navigation of the Linux desktop. The Android application/browser bridge is
separate.

## Android adaptations

`profile.json` starts a supervised D-Bus desktop session. Hyprland's executor
passes application commands through `guest/host-exec.sh`, entering glibc with
the desktop's environment and D-Bus connection. This also covers commands
originating from IPC and workspace rules. The standard Omarchy shell handles
its own panel, menu, wallpaper, application list and notifications.

Android manages the device's power, network, lock screen and audio service.
The Linux idle, lock, battery, media-control and polkit plugins are disabled by
default. Linux login/PAM, system-wide services, DRM monitor management and
systemd-dependent Omarchy maintenance commands are outside this port.
GTK image loading uses Glycin's automatic fallback when Android denies
nested bubblewrap namespaces. A wrapper preserves bubblewrap's failure and
normalizes its Android permission message so Glycin recognizes the unavailable
sandbox. Image decoder processes remain within this APK's Android sandbox.

The desktop uses XTerm because foot's controlling-terminal setup is rejected
by Android. Xwayland's default visual is 32-bit; XTerm's core X11 background
erases leave the high byte zero. An XTerm/UXTerm-only `force_rgbx` window rule
ignores that byte so Backspace, clearing and Neovim do not expose wallpaper.
Omarchy's normal whole-window opacity still applies. The full collection of upstream preinstalled applications is not
bundled; install ARM-compatible applications through pacman.

Only `hyprctl` is extracted from the signed Arch Hyprland package. The Linux
compositor and Aquamarine dependency are not installed in the guest; the
Android compositor is pinned separately. Its package provenance is recorded
in `/usr/lib/arlinux/hyprctl-package`. Installed Wayland libraries replace the
older bootstrap fallbacks so current Qt clients can use their required symbols.

The shared glibc recipe preserves upstream `mprotect` permission semantics.
An imported compatibility fallback corrupted heap memory when Qt attempted an
executable mapping denied by Android. The port does not disable Quickshell's
allocator or modify its packaged executable.

The desktop profile enables `BIONICX_FORK_EXEC=1`. Qt's forkfd subprocess
callback then uses `fork()` with a pidfd, keeping the guest exec adapter's
allocations, stack and loader environment separate from the parent. The
shared-memory vfork path could replace Quickshell with one of its own Bash
commands during startup. Other clone modes and profiles retain their defaults.

## Checks

```sh
python3 distributions/omarchy/tests/test-repositories.py
python3 distributions/omarchy/tests/test-accessibility-patch.py
python3 distributions/omarchy/tests/test-terminal-render-device.py --serial DEVICE
python3 distributions/omarchy/tests/test-accessibility-device.py --serial DEVICE
python3 distributions/omarchy/tests/test-desktop-device.py --serial DEVICE
python3 distributions/omarchy/tests/test-pacman-device.py --serial DEVICE
python3 tests/test-product-device.py --product distributions/omarchy --serial DEVICE
```

Generated APKs, rootfs archives and dependency caches stay under ignored build
directories. Submodules preserve the upstream sources and their licenses.
