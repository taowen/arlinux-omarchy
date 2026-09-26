# Arlinux Omarchy

Arlinux Omarchy packages a pinned upstream Omarchy desktop on Arch Linux ARM
for [arlinux-rootfs](https://github.com/taowen/arlinux-rootfs). It demonstrates
a full Hyprland-oriented desktop using the host-provided anhyprland compositor.

This repository contains only the Linux distribution recipe and its Omarchy
adaptation. It does not contain or require the Android host source.

From an `arlinux-rootfs` checkout:

```bash
./build.sh build omarchy
./build.sh verify out/omarchy.zip
```

The build produces `out/omarchy.zip`. See the rootfs project's
[distribution authoring guide](https://github.com/taowen/arlinux-rootfs/blob/main/docs/DISTRIBUTION-AUTHORING.md)
for the interface implemented here.

## Repository layout

- `rootfs.lock.json` pins the Arch Linux ARM archive and Omarchy commit.
- `third_party/omarchy` tracks the upstream source as a submodule.
- `tools/seed.sh` assembles and adapts the immutable desktop source.
- `tools/post-seed.sh` initializes trusted package signing keys.
- `guest/first-boot.sh` installs native desktop dependencies.
- `guest/session.sh` starts the shell and OpenCode on anhyprland.

The adaptation removes services owned by Android and keeps upstream source
changes as an explicit patch. Shared glibc, graphics, bundle, and host UI code
does not belong in this repository.

## Mobile Omarchy desktop

The bundle includes Omarchy's Quickshell desktop and all 22 pinned themes. On
first launch, pacman installs Foot as the default terminal, Neovim, Thunar,
Git and common shell tools, plus Evince, imv, and mpv. The desktop menu is
limited to actions that can run in the Android-hosted Arch Linux ARM session;
it includes OpenCode, files, development tools, themes, community plugins,
and package management. Node.js, Ruby, and PHP/Composer can be installed on
demand from the menu rather than inflating every new instance.

OpenCode Desktop is the integrated agent. `omarchy agent` focuses its existing
window, while `omarchy agent prompt "TASK"` sends a task to its current session.
The packaged Omarchy skill is adapted for OpenCode's global skill directory so
the agent can discover desktop commands without assuming a PC's `sudo`,
systemd, or hardware controls. Android's right-edge voice interaction also
submits to the same OpenCode window. Other upstream agent CLIs are not installed
or selected by default.
Package transactions use the host's existing virtual-root launcher through a
same-app-UID local socket; the desktop itself remains unprivileged and no
Android root permission is required. In a terminal, use `omarchy-pacman
install PACKAGE` or `omarchy-pacman update`; direct `pacman -S` from the
unprivileged desktop cannot write the root filesystem.

Android owns the device's power, network, Bluetooth, input method, and audio
service. Their PC-specific Omarchy controls are not exposed as broken menu
entries. Likewise, the upstream Windows VM and x86 PC-gaming installers are
not available in this ARM application. Other Arch Linux ARM packages can be
installed with the package menu or `omarchy-pacman` in a terminal.
Upstream's automatic `systemd-coredump` handoff and multi-agent subscription
panel are not available in this Android session.

## License

The distribution recipe is GPL-3.0-or-later. The pinned Omarchy source and all
downloaded packages retain their upstream licenses.
