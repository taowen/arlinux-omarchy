---
name: omarchy
description: Customize and troubleshoot the Omarchy desktop in ARLinux on Android. Use for themes, the Quickshell bar, Hyprland windows, plugins, packages, or desktop commands.
---

# Omarchy on ARLinux

This is Omarchy's Arch Linux ARM desktop inside an Android application. Read
`/usr/share/omarchy/default/agents/skills/omarchy/SKILL.md` and the relevant
topic guide beside it for upstream command and configuration details. The
Android-specific differences below take precedence over PC-only instructions.

- Use `omarchy commands --json` and a command's `--help` to discover its actual
  interface. Read the installed script when uncertain; do not guess options.
- Edit user configuration under `~/.config/`, not packaged files under
  `/usr/share/omarchy/`. Verify the effect in the live desktop.
- The compositor is Android-hosted anhyprland. Use `hyprctl` for its supported
  window operations. Android owns device power, network, Bluetooth, the input
  method, and the physical display; do not run PC hardware setup scripts.
- This session has no Linux root account, `sudo`, `pkexec`, or systemd service
  manager. For Arch packages use `omarchy-pacman install PACKAGE...` or
  `omarchy-pacman update`. Do not use direct `pacman -S` from the desktop.
- `omarchy agent` focuses OpenCode Desktop, and `omarchy agent prompt "TASK"`
  sends a task to its current session. Do not overwrite an existing draft.
- For Linux GUI work use standard `dogtail`/`pyatspi`; the global OpenCode
  instructions describe the mobile accessibility and speech setup.
- The upstream Windows VM, x86 gaming setup, and systemd-coredump workflow
  do not run inside this Android application. Do not claim they do.

Prefer a small reversible change, then verify the resulting window, setting,
or package state. Explain when an upstream guide assumes a PC feature that is
not present here.
