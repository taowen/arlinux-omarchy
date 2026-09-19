"""Private stdin runner for the host-side arlinux-py command."""

from __future__ import annotations

import glob
import os
import sys


def _select_accessibility_bus() -> None:
    """Give host-launched scripts the same AT-SPI session as the desktop."""
    os.environ["NO_AT_BRIDGE"] = "0"
    try:
        import dbus
    except ImportError:
        return
    current = os.environ.get("DBUS_SESSION_BUS_ADDRESS")
    addresses = [current] if current else []
    paths = sorted(
        glob.glob("/tmp/dbus-*"),
        key=lambda path: os.path.getmtime(path),
        reverse=True,
    )
    addresses.extend("unix:path=" + path for path in paths)
    for address in addresses:
        try:
            bus = dbus.bus.BusConnection(address)
            bus.get_name_owner("org.a11y.Bus")
            bus.close()
            os.environ["DBUS_SESSION_BUS_ADDRESS"] = address
            return
        except Exception:
            continue


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python3 -m arlinux._runner SCRIPT [args...]", file=sys.stderr)
        return 2
    filename = sys.argv[1]
    sys.argv = sys.argv[1:]
    source = sys.stdin.buffer.read()
    _select_accessibility_bus()
    namespace = {
        "__name__": "__main__",
        "__file__": filename,
        "__package__": None,
        "__cached__": None,
    }
    exec(compile(source, filename, "exec"), namespace, namespace)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
