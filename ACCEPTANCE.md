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
| Thunar, WebView Example Domain, XTerm | Pass | Pass |
| Catppuccin → Tokyo Night | Pass | Pass |
| Hardware renderer | Zink / Turnip, GL 4.6 | Zink / libhybris, GL 2.1 |
| Unreaped compositor application children | 0 | 0 |
| UID, sanitized exec, mprotect and PATH tests | Pass | Pass |
| Fork/exec isolation and pidfd regression | Skipped: Linux 4.19 lacks pidfd | Pass |

The installed APK is 667419282 bytes, SHA-256
`91dde8c9265eaeca7a25224d90fef56d212561da5c2e5204c05b78f38a3f47fb`.
The runtime checks use the same runtime libraries as the final APK; the final
Android launcher additionally includes dynamic profile argument allocation.
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
```

The desktop test restarts this APK and closes its test application windows.
It finishes on Tokyo Night. Results and original device screenshots are written
to `build/desktop-DEVICE/`; distribution/runtime identity checks are separate.

## Accessibility

AT-SPI transport is present, but Omarchy's shell accessibility is not ready.
On the Redmi test session, enabling `org.a11y.Status.ScreenReaderEnabled`
registered the Qt 6.11.2 `quickshell` application with the accessibility bus.
With the menu open, `/org/a11y/atspi/accessible/root` still reported
`ChildCount = 0`. The panel/menu therefore cannot currently be operated through
named AT-SPI controls. Desktop acceptance uses the public Hyprland/Quickshell
IPC interfaces and screenshots, and does not claim accessibility coverage.
Android browser/application accessibility support in Arlinux is a separate
bridge and does not supply the missing Quickshell widget tree.

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
