# Android desktop acceptance

The port uses Omarchy's pinned Quickshell shell and Hyprland Lua configuration
on Arch Linux ARM. The device suite in `tests/test-desktop-device.py` exercises
startup, native compositor command dispatch, the real menu/application list,
workspaces, Thunar, the Android WebView browser, XTerm and theme changes.
It also checks that closed application supervisors are reaped.

The default desktop starts with the Tokyo Night landscape wallpaper and panel.
There is no automatically opened terminal, Android extra-key bar, keyboard
handle or desktop IME toggle. Physical key events and pointer input remain.

## Verified 2026-09-12

| Check | Redmi / Adreno 650 | vivo X300 / Mali-G1-Ultra MC12 |
| --- | --- | --- |
| Normal APK startup and empty desktop | Pass | Pass, including a second cold-start run |
| Panel, menu and application list | Pass | Pass |
| Workspace 2 → 1 | Pass | Pass |
| AT-SPI tree, named actions, selected tabs, editable search and app launch | Pass | Pass |
| Thunar, WebView Example Domain, XTerm | Pass | Pass |
| XTerm typing → Backspace and Ctrl+L background pixel comparison | 0 changed pixels | 0 changed pixels |
| Catppuccin → Tokyo Night | Pass | Pass |
| Hardware renderer | Zink / Turnip, GL 4.6 | Zink / libhybris, GL 2.1 |
| Unreaped compositor application children | 0 | 0 |
| UID, sanitized exec, mprotect and PATH tests | Pass | Pass |
| Fork/exec isolation and pidfd regression | Skipped: Linux 4.19 lacks pidfd | Pass |

The installed APK is 667293580 bytes, SHA-256
`b01e1f703e78a58d45b5764053afb7b3d210a040834e5dceb571e7a06e2bb82a`.
The distribution/runtime checks above were verified for the preceding desktop
build. This accessibility build adds a Quickshell-only Qt initialization hook;
its desktop and AT-SPI checks use the final installed APK.
No diagnostic preload or manual guest session is used for desktop acceptance.
Repository bootstrap policy tests also pass.

Original screenshots: [Redmi desktop](docs/screenshots/redmi-desktop.png),
[X300 browser](docs/screenshots/x300-browser.png),
[X300 files](docs/screenshots/x300-files.png).

## Reproduce

```sh
ARLINUX_DIR=third_party/arlinux tests/test-desktop-device.py --serial DEVICE
third_party/arlinux/tests/test-product-device.py --product . --serial DEVICE
python3 tests/test-repositories.py
python3 tests/test-accessibility-patch.py
ARLINUX_DIR=third_party/arlinux tests/test-terminal-render-device.py --serial DEVICE
ARLINUX_DIR=third_party/arlinux tests/test-accessibility-device.py --serial DEVICE
```

The desktop test restarts this APK and closes its test application windows.
It finishes on Tokyo Night. Results and original device screenshots are written
to `build/desktop-DEVICE/`; distribution/runtime identity checks are separate.

## Accessibility

The normal APK exposes Quickshell's panel and menu through AT-SPI on both
devices. `tests/test-accessibility-device.py` performs named Action calls to
switch workspaces 2 → 1 (checking selected state), open and close the menu,
enter Apps, and launch Omarchy Terminal. EditableText filters, clears and
refilters the application list. The test checks that closing the menu removes
its entries from the accessible tree and that the terminal actually maps.
The [filtered menu screenshot](docs/screenshots/redmi-accessibility-search.png)
was captured after an AT-SPI EditableText operation and visually inspected.
No coordinate clicks or Quickshell IPC perform these test actions. Hyprland
IPC is used for observations and closing the test terminal.

Quickshell 0.3.1 destroys a temporary QCoreApplication before creating its
QGuiApplication. Qt's cleanup removed Qt Quick's accessibility factory, leaving
the AT-SPI application with zero children. This product's runtime registers
Qt Quick's exported module initializer with Qt's application startup hook,
restricted to the Quickshell process. The packaged Qt and Quickshell binaries
remain unchanged. A product QML patch supplies names, roles, actions and a real
editable search field. It is checked in full before application and is
idempotent; conflicting user changes stop application without partial edits.

Coverage is the panel, workspaces and application menu; other upstream plugins
and Android TalkBack navigation are not certified. Android browser/application
accessibility remains a separate bridge. Arlinux Arch retains its independent
plain xterm entry and has no changes from this fix.

## Terminal background regression

`tests/test-terminal-render-device.py` opens its own XTerm on an unused
workspace, injects `a`, Backspace and Ctrl+L, and compares the prompt/background
pixels with the initial frame. It hides the terminal cursor, checks that typing
actually changes the image, then closes its terminal and restores the workspace.
Pillow is required on the host. Keep the pointer outside the first two lines.
The `--negative-control` option disables `force_rgbx` on that test window and
is expected to fail: the Redmi reproduction changed 51,456 pixels after
Backspace. Both corrected devices report zero changed pixels after Backspace
and Ctrl+L. Neovim's welcome screen was also visually checked on both devices; see the
[corrected terminal and Neovim](docs/screenshots/redmi-terminal-neovim.png).

The cause is the port's 32-bit default X visual: XTerm's RGB erases have a zero
high byte that is otherwise interpreted as alpha. The product applies
`force_rgbx` only to XTerm/UXTerm; the existing theme opacity is preserved.
Other applications retain their per-pixel alpha behavior.

## Platform boundaries

The compositor can briefly report unavailable FP16 render targets at startup;
some HDR/color-management effects are unavailable. Desktop acceptance covers
the SDR rendering paths above.

Android owns device power, networking, audio and locking. This product menu
exposes desktop operations supported by this port; Linux service-management,
bootloader and machine-installation menus are omitted. Arch package signatures
remain enabled. The bundled upstream application catalog is not preinstalled.

GTK image loaders cannot create bubblewrap namespaces inside these Android
applications. The wrapper preserves the failed command and identifies the
Android permission failure to Glycin's existing automatic fallback. Decoder
processes remain in the APK's Android sandbox, without a second Linux namespace
sandbox. The relevant upstream detection is in
[GNOME Glycin's sandbox implementation](https://github.com/GNOME/glycin/blob/2.1.5/glycin/src/sandbox.rs).
