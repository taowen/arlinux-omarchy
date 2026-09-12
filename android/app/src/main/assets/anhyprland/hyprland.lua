local files = assert(os.getenv('XDG_RUNTIME_DIR')):gsub('/runtime$', '')
dofile(files .. '/rootfs/usr/lib/arlinux/guest/hyprland.lua')
