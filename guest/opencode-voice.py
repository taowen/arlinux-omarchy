#!/usr/bin/python3
"""Focus or submit OpenCode's prompt using its standard AT-SPI interface."""

from __future__ import annotations

import glob
import os
from pathlib import Path
import subprocess
import sys
import time


def select_accessibility_bus() -> None:
    os.environ["NO_AT_BRIDGE"] = "0"
    import dbus

    current = os.environ.get("DBUS_SESSION_BUS_ADDRESS")
    addresses = [current] if current else []
    paths = sorted(glob.glob("/tmp/dbus-*"), key=os.path.getmtime, reverse=True)
    addresses.extend("unix:path=" + path for path in paths)
    for address in addresses:
        try:
            bus = dbus.bus.BusConnection(address)
            bus.get_name_owner("org.a11y.Bus")
            bus.close()
            os.environ["DBUS_SESSION_BUS_ADDRESS"] = address
            return
        except Exception:
            pass
    raise RuntimeError("OpenCode accessibility bus not found")


def descendants(node):
    yield node
    try:
        count = node.childCount
    except Exception:
        return
    for index in range(count):
        try:
            child = node[index]
        except Exception:
            continue
        yield from descendants(child)


def find_opencode():
    import pyatspi

    desktop = pyatspi.Registry.getDesktop(0)
    for app in desktop:
        try:
            if app.name == "ai.opencode.desktop":
                return app
        except Exception:
            pass
    raise RuntimeError("OpenCode window not found")


def find_named(root, role: str, name: str):
    for node in descendants(root):
        try:
            if node.getRoleName() == role and node.name == name:
                return node
        except Exception:
            pass
    raise RuntimeError(f"OpenCode {name!r} {role} not found")


def text_of(entry) -> str:
    text = entry.queryText()
    return text.getText(0, text.characterCount)


def activate(node, action_name: str) -> bool:
    actions = node.queryAction()
    for index in range(actions.nActions):
        if actions.getName(index).lower() == action_name:
            return bool(actions.doAction(index))
    return False


def focus_prompt() -> None:
    app = find_opencode()
    prompt = find_named(app, "entry", "Prompt")
    try:
        focused = prompt.queryComponent().grabFocus()
    except Exception:
        focused = False
    if not focused and not activate(prompt, "activate"):
        raise RuntimeError("could not focus OpenCode prompt")
    baseline = text_of(prompt)
    state = Path(os.environ.get("TMPDIR", "/tmp")) / "opencode-voice-baseline"
    state.write_text(baseline, encoding="utf-8")
    print("focused")


def send_prompt() -> None:
    state = Path(os.environ.get("TMPDIR", "/tmp")) / "opencode-voice-baseline"
    baseline = state.read_text(encoding="utf-8") if state.exists() else ""
    deadline = time.monotonic() + 15
    changed = None
    stable_since = None
    while time.monotonic() < deadline:
        # Electron replaces its accessible entry as the prompt changes. Never
        # hold an AT-SPI object across recognition updates.
        try:
            prompt = find_named(find_opencode(), "entry", "Prompt")
            current = text_of(prompt)
        except Exception:
            time.sleep(0.15)
            continue
        if current.strip() and current != baseline:
            if current != changed:
                changed = current
                stable_since = time.monotonic()
            elif time.monotonic() - stable_since >= 0.8:
                # Chromium advertises a Send.click AT-SPI action but returns
                # false without invoking it. Submit through the semantically
                # focused prompt's standard Enter binding instead.
                prompt = find_named(find_opencode(), "entry", "Prompt")
                if not prompt.queryComponent().grabFocus():
                    raise RuntimeError("could not refocus OpenCode prompt")
                subprocess.run(
                    ["xdotool", "key", "--clearmodifiers", "Return"],
                    check=True,
                )
                submitted = time.monotonic() + 3
                while time.monotonic() < submitted:
                    try:
                        prompt = find_named(find_opencode(), "entry", "Prompt")
                        if text_of(prompt) != current:
                            break
                    except Exception:
                        # Submission can replace the entry while navigating.
                        pass
                    time.sleep(0.1)
                else:
                    raise RuntimeError("OpenCode did not accept prompt submission")
                print("sent")
                return
        time.sleep(0.15)
    raise RuntimeError("no new voice text appeared in OpenCode prompt")


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in {"focus", "send"}:
        print("usage: opencode-voice.py focus|send", file=sys.stderr)
        return 2
    select_accessibility_bus()
    if sys.argv[1] == "focus":
        focus_prompt()
    else:
        send_prompt()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(error, file=sys.stderr)
        raise SystemExit(1)
