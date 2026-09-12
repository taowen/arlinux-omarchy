#!/system/bin/sh
# Enter glibc without injecting its preload library into the Android shell.
files=${XDG_RUNTIME_DIR%/runtime}
root=$files/rootfs
exec >> "$files/runtime/omarchy-launch.log" 2>&1
exec "$files/bin/bionicx-exec" --env "BIONICX_ROOTFS=$root" --env "BIONICX_FILES=$files" \
  --env "LD_LIBRARY_PATH=$root/usr/lib/arlinux-platform:$root/usr/lib" \
  --env "LD_PRELOAD=$files/lib/libbionicx-runtime.so" -- \
  "$root/usr/bin/bash" -c 'source "$XDG_RUNTIME_DIR/omarchy-session.env"; exec bash -c "$1"' arlinux "$1"
