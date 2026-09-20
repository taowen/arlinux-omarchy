Arlinux Omarchy

This desktop layers Omarchy on Arch Linux ARM. Common shortcuts include
Super+Enter for a terminal, Super+number for workspaces, and Alt+F4 to close a
window.

Install packages with pacman:

  pacman -Syu
  pacman -S package-name

Omarchy source is installed at /usr/share/omarchy. User configuration lives in
~/.config/omarchy and ~/.config/hypr, while desktop logs are written under
$XDG_RUNTIME_DIR.

Android supplies the display, input, audio, network, lock screen, and
application lifecycle.
