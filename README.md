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
- `native/product-policy.h` contains narrowly scoped runtime compatibility.

The adaptation removes services owned by Android and keeps upstream source
changes as an explicit patch. Shared glibc, graphics, bundle, and host UI code
does not belong in this repository.

## License

The distribution recipe is GPL-3.0-or-later. The pinned Omarchy source and all
downloaded packages retain their upstream licenses.
