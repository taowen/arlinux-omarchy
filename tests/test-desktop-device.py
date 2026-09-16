#!/usr/bin/env python3
"""Restart this product and exercise its desktop; closes the test app windows."""
import argparse
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import time

product = Path(__file__).resolve().parents[1]
core = Path(os.environ.get('ARLINUX_DIR', product / '../..')).resolve()
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--serial', required=True)
p.add_argument('--reuse-session', action='store_true', help='Use an already empty running desktop')
a = p.parse_args()
package = json.loads((product / 'product.json').read_text())['applicationId']
out = product / 'build' / ('desktop-' + a.serial)
out.mkdir(parents=True, exist_ok=True)
adb = ['adb', '-s', a.serial]
client = ['python3', str(core / 'tools/product-device.py'), '--serial', a.serial, '--product', str(product)]
results = {}


def guest(command, timeout=30):
    run = subprocess.run(client + ['exec', '/usr/bin/bash', '-c',
        'source "$XDG_RUNTIME_DIR/omarchy-session.env"; ' + command],
        text=True, capture_output=True, timeout=timeout)
    if run.returncode:
        raise RuntimeError(run.stdout + run.stderr)
    return run.stdout.strip()


def until(command, predicate, seconds=30):
    deadline = time.monotonic() + seconds
    last = ''
    while time.monotonic() < deadline:
        try:
            last = guest(command, timeout=5)
            if predicate(last):
                return last
        except (RuntimeError, subprocess.TimeoutExpired) as e:
            last = str(e)
        time.sleep(0.5)
    raise RuntimeError('Desktop did not reach expected state: ' + last)


def screenshot(name):
    time.sleep(1)
    (out / (name + '.png')).write_bytes(subprocess.check_output(adb + ['exec-out', 'screencap', '-p']))


def dispatch(lua):
    return guest('hyprctl dispatch ' + shlex.quote(lua))


def launch(command, app_class, name):
    dispatch('hl.dsp.exec_cmd(' + json.dumps(command) + ')')
    raw = until('hyprctl -j clients', lambda x: any(
        w['class'].lower() == app_class.lower() and w['mapped'] for w in json.loads(x)))
    results[name] = json.loads(raw)
    screenshot(name)
    # This test starts with no clients and opens one application at a time.
    dispatch('hl.dsp.window.close()')
    until('hyprctl -j clients', lambda x: not json.loads(x))


if not a.reuse_session:
    subprocess.run(adb + ['shell', 'am', 'force-stop', package], check=True)
    subprocess.run(client + ['start'], check=True)
until('omarchy-shell shell ping', lambda x: x == 'ok', seconds=90)
monitors = json.loads(until('hyprctl -j monitors', lambda x: bool(json.loads(x))))
assert monitors[0]['activeWorkspace']['id'] > 0
assert not monitors[0]['disabled']
assert json.loads(guest('hyprctl -j clients')) == [], 'Startup opened an application window'
results['monitors'] = monitors
results['startupClients'] = []
results['font'] = guest('fc-match -f "%{family}" omarchy')
assert results['font'] == 'omarchy'
results['clock'] = guest('date +"%Y-%m-%d %H:%M %Z"')
results['renderer'] = re.sub(r'\x1b\[[0-9;]*m', '', guest(
    'grep "OpenGL VENDOR:" "$XDG_RUNTIME_DIR/omarchy-shell.log" | head -1'))
assert 'zink' in results['renderer'].lower(), results['renderer']
screenshot('desktop')

# Exercise the real shell overlays, keeping menu and application-list evidence.
guest('omarchy-shell shell summon omarchy.menu \'{"menu":"root"}\'')
screenshot('menu')
guest('omarchy-shell shell summon omarchy.menu \'{"menu":"apps"}\'')
screenshot('apps')
guest('omarchy-shell shell hide omarchy.menu')

for workspace in (2, 1):
    dispatch('hl.dsp.focus({ workspace = "' + str(workspace) + '" })')
    until('hyprctl -j activeworkspace', lambda x: json.loads(x)['id'] == workspace)
results['workspaceSwitch'] = [2, 1]
launch('omarchy-launch-nautilus', 'thunar', 'files')
launch('omarchy-launch-browser https://example.com', 'io.taowen.arlinux.browser', 'browser')
launch('omarchy-launch-terminal', 'XTerm', 'terminal')

# Use bundled themes only; verify application of both palette and background.
for theme in ('catppuccin', 'tokyo-night'):
    guest('omarchy-theme-set ' + shlex.quote(theme), timeout=60)
    assert guest('cat "$XDG_STATE_HOME/omarchy/current/theme.name"') == theme
    assert guest('test -f "$XDG_STATE_HOME/omarchy/current/background" && echo ok') == 'ok'
    assert guest('omarchy-shell shell ping') == 'ok'
    screenshot('theme-' + theme)
results['themeSwitch'] = ['catppuccin', 'tokyo-night']
# Native compositor launches must also reap their bionicx-exec supervisor.
host_pid = subprocess.check_output(adb + ['shell', 'pidof', package], text=True).strip()
processes = subprocess.check_output(adb + ['shell', 'ps', '-A', '-o', 'PID,PPID,STAT,NAME'], text=True)
zombies = [line for line in processes.splitlines() if len(line.split()) >= 4
           and line.split()[1] == host_pid and line.split()[2].startswith('Z')]
assert not zombies, 'Unreaped compositor children: ' + str(zombies)
results['unreapedChildren'] = zombies
assert not json.loads(guest('hyprctl -j clients'))
(out / 'result.json').write_text(json.dumps(results, indent=2) + '\n')
print(out / 'result.json')
