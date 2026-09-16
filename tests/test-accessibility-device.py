#!/usr/bin/env python3
"""Exercise the running Omarchy desktop through standard AT-SPI interfaces.

Start with an empty desktop and closed menu. Hyprland IPC is used only to
observe results and close the test terminal; all tested actions use AT-SPI.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import shlex
import sys

product = Path(__file__).resolve().parents[1]
core = Path(os.environ.get('ARLINUX_DIR', product / '../..')).resolve()
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--serial', required=True)
a = p.parse_args()
client = [sys.executable, str(core / 'tools/product-device.py'), '--serial', a.serial,
          '--product', str(product)]
payload = r'''
import json, subprocess, time
import pyatspi
from gi.repository import GLib
ctx = GLib.MainContext.default()
pyatspi.Registry.registerEventListener(lambda e: None,
    'object:children-changed', 'object:state-changed', 'object:text-changed')
def walk(node):
    yield node
    for child in node:
        if child is not None:
            yield from walk(child)
def nodes():
    while ctx.pending():
        ctx.iteration(False)
    for app in pyatspi.Registry.getDesktop(0):
        if app.name == 'quickshell':
            yield from walk(app)
def find(name, role=None):
    return next((n for n in nodes() if n.name == name and
                 (role is None or n.getRoleName() == role)), None)
def until(fn):
    end = time.monotonic() + 20
    while time.monotonic() < end:
        try:
            value = fn()
            if value:
                return value
        except GLib.Error:
            # Menu transitions can replace accessible objects mid-query.
            # Re-query the tree; action execution itself is never retried.
            pass
        time.sleep(.1)
    raise AssertionError('Timed out waiting for ' + str(fn))
def control(name, role=None):
    return until(lambda: find(name, role))
actions = []
def press(name, role=None):
    def ready_action():
        node = find(name, role)
        if node is None:
            return None
        action = node.queryAction()
        index = next(i for i in range(action.nActions)
                     if action.getName(i).lower() in ('press', 'click', 'activate'))
        return action, index
    action, index = until(ready_action)
    assert action.doAction(index), name
    actions.append(name)
def hypr(query):
    return json.loads(subprocess.check_output(['hyprctl', '-j', query], text=True))
assert not hypr('clients'), 'Start with an empty desktop'
for workspace in (2, 1):
    name = 'Workspace ' + str(workspace)
    press(name, 'page tab')
    until(lambda: hypr('activeworkspace')['id'] == workspace)
    until(lambda: control(name).getState().contains(pyatspi.STATE_SELECTED))
press('Omarchy menu', 'button')
control('Omarchy menu', 'popup menu')
control('Apps', 'menu item')
press('Close menu')
until(lambda: find('Apps', 'menu item') is None)
press('Omarchy menu', 'button')
press('Apps', 'menu item')
control('Thunar File Manager', 'menu item')
search = control('Search menu', 'text')
assert search.queryEditableText().setTextContents('Omarchy Terminal')
control('Omarchy Terminal', 'menu item')
until(lambda: find('Thunar File Manager', 'menu item') is None)
assert search.queryEditableText().setTextContents('')
control('Thunar File Manager', 'menu item')
assert search.queryEditableText().setTextContents('Omarchy Terminal')
until(lambda: find('Thunar File Manager', 'menu item') is None)
press('Omarchy Terminal', 'menu item')
clients = until(lambda: [w for w in hypr('clients')
                        if w['class'].lower() == 'xterm' and w['mapped']])
until(lambda: find('Omarchy Terminal', 'menu item') is None)
subprocess.run(['hyprctl', 'dispatch', 'hl.dsp.window.close()'], check=True,
               stdout=subprocess.DEVNULL)
until(lambda: not hypr('clients'))
control('Omarchy menu', 'button')
print(json.dumps({'actions': actions, 'editableText': 'filter, clear, filter',
                  'launchedClass': clients[0]['class'],
                  'remainingClients': hypr('clients')}, indent=2))
'''
run = subprocess.run(client + ['exec', '/usr/bin/bash', '-c',
    'source "$XDG_RUNTIME_DIR/omarchy-session.env"; python3 -c ' + shlex.quote(payload)],
    text=True, capture_output=True, timeout=150)
if run.returncode:
    raise SystemExit(run.stdout + run.stderr)
result = json.loads(run.stdout)
out = product / 'build' / ('accessibility-' + a.serial + '.json')
out.write_text(json.dumps(result, indent=2) + '\n')
print(out)
