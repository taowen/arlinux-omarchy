#!/usr/bin/python3
"""Focus or submit OpenCode's prompt using its standard AT-SPI interface."""

from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys
import time


def select_accessibility_bus() -> None:
    os.environ["NO_AT_BRIDGE"] = "0"
    result = subprocess.run(["xprop", "-root", "AT_SPI_BUS"],
                            capture_output=True, text=True, timeout=3, check=True)
    match = re.search(r'AT_SPI_BUS\(STRING\) = "([^"]+)"', result.stdout)
    if not match:
        raise RuntimeError("desktop accessibility bus not published")
    os.environ["AT_SPI_BUS_ADDRESS"] = match.group(1)


def descendants(root, reverse: bool = False):
    stack = [root]
    while stack:
        node = stack.pop()
        yield node
        try:
            count = node.childCount
        except Exception:
            continue
        indices = range(count) if reverse else range(count - 1, -1, -1)
        for index in indices:
            try:
                stack.append(node[index])
            except Exception:
                pass


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


def raise_opencode() -> None:
    windows = subprocess.run(
        ["xdotool", "search", "--onlyvisible", "--name", "^OpenCode$"],
        capture_output=True, text=True,
    ).stdout.split()
    if not windows:
        raise RuntimeError("OpenCode window is not ready yet")
    subprocess.run(["xdotool", "windowactivate", windows[-1]], check=True)


def find_named(root, role: str, name: str):
    import pyatspi

    for node in descendants(root, reverse=role == "entry" and name == "Prompt"):
        try:
            if (node.getRoleName() == role and node.name == name
                    and node.getState().contains(pyatspi.STATE_SHOWING)):
                return node
        except Exception:
            pass
    raise RuntimeError(f"OpenCode {name!r} {role} not found")


def visible_dialog(root):
    import pyatspi

    # Electron appends overlays after the main page in its web document.
    # Do not walk a potentially huge conversation just to check for a modal.
    document = find_named(root, "document web", "OpenCode")
    for index in range(document.childCount - 1, 0, -1):
        for node in descendants(document[index]):
            try:
                if (node.getRoleName() == "dialog"
                        and node.getState().contains(pyatspi.STATE_SHOWING)):
                    return node
            except Exception:
                pass
    return None


def open_prompt():
    """Return the current composer, leaving Home or a modal if necessary."""
    app = find_opencode()
    dialog = visible_dialog(app)
    if dialog is not None:
        try:
            find_named(dialog, "page tab", "General")
        except RuntimeError:
            raise RuntimeError("close the OpenCode dialog before voice input")
        subprocess.run(["xdotool", "key", "--clearmodifiers", "Escape"], check=True)
        time.sleep(0.2)
        app = find_opencode()
    try:
        return find_named(app, "entry", "Prompt")
    except RuntimeError:
        pass
    # Home and Settings have no composer. Reuse an open new-session tab when
    # possible, preserving its draft instead of making a duplicate session.
    try:
        target = find_named(app, "link", "New session")
    except RuntimeError:
        target = find_named(app, "button", "New session")
    if not any(activate(target, name) for name in ("jump", "press", "click", "open")):
        raise RuntimeError("could not open OpenCode session")
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        try:
            return find_named(find_opencode(), "entry", "Prompt")
        except RuntimeError:
            time.sleep(0.1)
    raise RuntimeError("OpenCode session opened without a prompt")


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
    raise_opencode()
    prompt = open_prompt()
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
    raise_opencode()
    state = Path(os.environ.get("TMPDIR", "/tmp")) / "opencode-voice-baseline"
    if not state.exists():
        raise RuntimeError("voice prompt was not prepared")
    baseline = state.read_text(encoding="utf-8")
    deadline = time.monotonic() + 22
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
        if current.replace("\u200b", "").strip() and current != baseline:
            if current != changed:
                changed = current
                stable_since = time.monotonic()
            elif time.monotonic() - stable_since >= 1.5:
                # Chromium advertises a Send.click AT-SPI action but returns
                # false without invoking it. Submit through the semantically
                # focused prompt's standard Enter binding instead.
                app = find_opencode()
                if visible_dialog(app) is not None:
                    raise RuntimeError("OpenCode opened a dialog during voice input")
                prompt = find_named(app, "entry", "Prompt")
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
                state.unlink(missing_ok=True)
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
