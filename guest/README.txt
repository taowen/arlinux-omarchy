Arlinux Omarchy

This desktop layers Omarchy on Arch Linux ARM. Common shortcuts include
Super+Enter for a terminal, Super+number for workspaces, and Alt+F4 to close a
window.

Install packages from the menu or terminal:

  omarchy-pacman update
  omarchy-pacman install package-name

The Android host runs only these package transactions with the virtual-root
identity needed by pacman; the desktop and other applications remain ordinary
unprivileged guest processes.

Omarchy source is installed at /usr/share/omarchy. User configuration lives in
~/.config/omarchy and ~/.config/hypr, while desktop logs are written under
$XDG_RUNTIME_DIR.

Android supplies the display, input, audio, network, lock screen, and
application lifecycle.
