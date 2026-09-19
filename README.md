# Arlinux Omarchy

Omarchy rootfs recipe for [arlinux-rootfs](https://github.com/taowen/arlinux-rootfs).
It layers the pinned upstream Omarchy source over an Arch Linux ARM root
filesystem and produces an AArch64 distribution bundle.

From an `arlinux-rootfs` checkout:

```bash
./build.sh build omarchy
./build.sh verify out/omarchy.arlinux-rootfs
```

`rootfs.lock.json` pins bootstrap inputs, `third_party/omarchy` pins upstream,
`tools/seed.sh` creates the root filesystem, and `guest/` contains guest setup
and launch files. Shared glibc, GPU, host UI and bundle logic do not belong in
this repository.
