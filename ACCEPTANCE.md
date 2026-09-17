# Android desktop acceptance

The port uses Omarchy's pinned Quickshell shell and Hyprland Lua configuration
on Arch Linux ARM. The device suite in `tests/test-desktop-device.py` exercises
startup, native compositor command dispatch, the real menu/application list,
workspaces, Thunar, the Android WebView browser, XTerm and theme changes.
It also checks that closed application supervisors are reaped.

The default desktop starts with the Tokyo Night landscape wallpaper and panel.
There is no automatically opened terminal, Android extra-key bar or keyboard
handle. Physical key events and pointer input remain; a right-side inward swipe
toggles the Linux touch keyboard and its `中 / En` control switches Fcitx5.

## Verified 2026-09-13

| Check | Redmi / Adreno 650 | vivo X300 / Mali-G1-Ultra MC12 | OnePlus PJZ110 / Adreno 830 |
| --- | --- | --- | --- |
| Normal APK startup and empty desktop | Pass | Pass | Pass |
| Panel, menu and application list | Pass | Pass | Pass |
| Workspace 2 → 1 | Pass | Pass | Pass |
| AT-SPI tree, named actions, selected tabs, editable search and app launch | Pass | Pass | Pass |
| Thunar, WebView Example Domain, XTerm | Pass | Pass | Pass |
| XTerm typing → Backspace and Ctrl+L background pixel comparison | 0 changed pixels | 0 changed pixels | 0 changed pixels |
| Catppuccin → Tokyo Night | Pass | Pass | Pass |
| Hardware renderer | Zink / Turnip, GL 4.6 | Zink / libhybris, GL 2.1 | Zink / Turnip, GL 4.6 |
| Unreaped compositor application children | 0 | 0 | 0 |
| UID, sanitized exec, mprotect and PATH tests | Pass | Pass | Pass |
| Fork/exec isolation and pidfd regression | Skipped: Linux 4.19 lacks pidfd | Pass | Pass |

The APK used for the table above is 676671282 bytes, SHA-256
`5212ef367573bca4b273f972b8e1c5a0569e7b5aa23fb199fcbe9e73680c1de2`.
The checks in this table were run against this installed APK on all three
devices. [Saved results and installed-file hashes](docs/verified-pjz110-2026-09-13.json)
record the exact scope and component identities.
No diagnostic preload or manual guest session is used for desktop acceptance.
Repository bootstrap policy tests also pass.

Original screenshots: [Redmi desktop](docs/screenshots/redmi-desktop.png),
[X300 browser](docs/screenshots/x300-browser.png),
[X300 files](docs/screenshots/x300-files.png),
[PJZ110 desktop](docs/screenshots/pjz110-desktop.png),
[PJZ110 browser](docs/screenshots/pjz110-browser.png).

## Blender on OnePlus 13, 2026-09-13 — FAIL

A later APK was built from product `ac79784` and core `8a0868c`, with Mesa
`89060684726` on `arlinux-official-base`, and installed on PJZ110 only.
Its SHA-256 is `0fa39f4b2eb285af1aa72cbbd6d017bea6a4cd3eb0b09f99dc682edac06d0e99`.
The earlier three-device desktop matrix above retains its original APK identity;
it is not a Blender acceptance result for this later build.

The unmodified distribution Blender `17:5.2.1-1` executable was tested with
matching signed USD `26.05-4` and `python-cattrs` packages. Runs started inside
Omarchy Terminal after sourcing the desktop session environment, using the
existing Arlinux Blender workflow script. The installed driver hash matches
the new APK, and the Vulkan process mappings confirm that driver was loaded.

| Path | Result |
| --- | --- |
| Default OpenGL / Zink / Wayland | FAIL: unsupported 10-bit surface format 58, followed by a segmentation fault (exit 139). |
| Explicit Vulkan / Wayland | FAIL: repeated `VK_ERROR_FORMAT_NOT_SUPPORTED` during swapchain creation; no Blender window maps. All five CPU modeling/save/reopen events run, but this is not visible application success. The test process was stopped after collection. |
| Diagnostic X11 fallback | FAIL: drawable creation fails, no Blender window; later exit 137. The termination cause is not established. No permanent backend override was installed. |
| Old Turnip ICD control (`f5ebba832e8`) | Same default OpenGL surface-format error. The old ICD initializer path is verified; this control kept current EGL/Gallium, so it is not an old-APK rollback. |

These observations do not establish a regression from the branch reconstruction:
the old and new Mesa source trees are identical, and replacing only Turnip with
the previous ICD does not remove the default failure. Window-format negotiation
needs further investigation. Visible editing, successful resizing, a fresh
visible reopen and Workbench/Eevee rendering were not accepted. No application,
Mesa or compositor fix was made in this test pass.

[Exact versions, commands, hashes and results](docs/verified-blender-pjz110-2026-09-13.json)
include the package-dependency setup and the limitations of the controls.
Original failure screenshots: [OpenGL](docs/screenshots/pjz110-blender-opengl-failure.png),
[Vulkan](docs/screenshots/pjz110-blender-vulkan-failure.png).
Test processes and terminals were closed; the new APK and installed packages
remain on PJZ110. Local logs, process maps and diagnostic model files are under
Arlinux `build/blender-pjz110-official-base/`.

## Reproduce

```sh
distributions/omarchy/tests/test-desktop-device.py --serial DEVICE
tests/test-product-device.py --product distributions/omarchy --serial DEVICE
python3 distributions/omarchy/tests/test-repositories.py
python3 distributions/omarchy/tests/test-accessibility-patch.py
distributions/omarchy/tests/test-terminal-render-device.py --serial DEVICE
distributions/omarchy/tests/test-accessibility-device.py --serial DEVICE
```

The desktop test restarts this APK and closes its test application windows.
It finishes on Tokyo Night. Results and original device screenshots are written
to `build/desktop-DEVICE/`; distribution/runtime identity checks are separate.

## Accessibility

The normal APK exposes Quickshell's panel and menu through AT-SPI on all three
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
Backspace. All three devices report zero changed pixels after Backspace
and Ctrl+L. Neovim's welcome screen was also visually checked on both devices; see the
[corrected terminal and Neovim](docs/screenshots/redmi-terminal-neovim.png).

The cause is the port's 32-bit default X visual: XTerm's RGB erases have a zero
high byte that is otherwise interpreted as alpha. The product applies
`force_rgbx` only to XTerm/UXTerm; the existing theme opacity is preserved.
Other applications retain their per-pixel alpha behavior.

## Libhybris integrity regression, 2026-09-13, before the namespace fix

Arlinux `2628032` pinned libhybris `62a9a8f`, including the loader fix introduced
in `0106f4f` and its constructor regression fixtures. The Android loader verifies the
original BoringSSL HMAC before relocating its private expected digest for TLS
instruction changes. Native integrity checks, algorithm self-tests and both
crypto/SSL constructors remain active. Unsupported or damaged inputs fail
instead of disabling those checks. This does not claim FIPS certification.

The [four-device evidence](https://github.com/taowen/libhybris/blob/62a9a8f61f4c00d8c43309bd41177e292b201aa8/tests/integrity/verified-2026-09-13.json)
records 72 passing integrity cases across Redmi M2012K11AC, vivo X300,
OnePlus 8T and OnePlus PJZ110. Redmi, X300 and OnePlus 8T also each pass all
seven native/hybris Vulkan, GLES 2/3 and TLS regression cases. At that point, PJZ110's vendor
mapping permission failures reproduced with the independently built previous
libhybris version and are recorded separately, not counted as passes.

That build's generic GPU archive contained `q.so` with SHA-256
`0899cb85fba9fa326c7a467a4499455430d184ec6a98d6bc1b3d7eab7335dfa1`.
It is byte-identical to the tested library after applying the product's normal
RUNPATH. Product cache inputs now include nested linker libraries so a `q.so`
update invalidates prepared assets.

On X300, that installed file had the same hash. A probe executed inside that
APK loaded system crypto/SSL through the packaged linker: original HMAC
verification, native integrity and algorithm self-tests, nine-thread SHA-256
and random generation, and SSL context creation all passed. Redmi uses the
Turnip overlay for its desktop; its libhybris coverage is the standalone suite.

## PJZ110 namespace and presentation fixes

Arlinux `7d30871` pins libhybris `fb150ae` and Mesa `f5ebba832e8`;
anhyprland is `0f169791`. The [core graphics record](https://github.com/taowen/arlinux/blob/7d30871/docs/android16-graphics.md)
explains both failures and their separate fixes.

libhybris now uses Android's generated platform/HAL namespaces. System
Vulkan/EGL dependencies resolve to the system libraries instead of same-name
vendor copies with incompatible mapping permissions. The
[four-device namespace evidence](https://github.com/taowen/libhybris/blob/fb150ae/tests/baseline/namespace-verified-2026-09-13.json)
records passing Vulkan, GLES 2/3, TLS and namespace checks, plus another 72
passing integrity cases. PJZ110's preceding graphics failures are resolved.
A separately staged probe under the PJZ110 application UID also passes the
libhybris graphics and namespace checks.

PJZ110's default Turnip desktop additionally needed support for modern gralloc
handles without Qualcomm's old magic field. The compositor now supplies
verified Android Mapper layout metadata through `android_wlegl` version 3;
Mesa checks its format and stride before importing the buffer. Older clients
and the legacy handle path remain supported. Normal APK desktop acceptance,
including actual Wayland and Xwayland windows, now passes on PJZ110.

The current generic archive and X300 installed `q.so` both have SHA-256
`65e598c47193b236621e7ad1ea12a4f58313d02738a3b613b81cf165503b4428`.
The archive is byte-identical to the standalone-tested linker after applying
its normal product RUNPATH. A fresh system crypto/SSL probe inside the X300
APK passes original-HMAC verification, native integrity and algorithm
self-tests, nine-thread SHA-256/RAND work and SSL context creation through
this packaged linker. No integrity checks or Android mapping permissions
were disabled.

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
