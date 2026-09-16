#!/usr/bin/env python3
"""Check XTerm background pixels after typing, Backspace and readline clear.

Requires Pillow on the host and a running desktop. Uses an empty workspace,
closes its own terminal and restores the original workspace. Keep the pointer
outside the terminal's first two lines during the screenshot comparisons.
"""
import argparse
import io
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time
from PIL import Image, ImageChops

product = Path(__file__).resolve().parents[1]
core = Path(os.environ.get('ARLINUX_DIR', product / '../..')).resolve()
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--serial', required=True)
p.add_argument('--negative-control', action='store_true',
               help='Disable the fix on the test window; this run must fail')
a = p.parse_args()
adb = ['adb', '-s', a.serial]
client = [sys.executable, str(core / 'tools/product-device.py'), '--serial', a.serial,
          '--product', str(product)]
out = product / 'build' / ('terminal-render-' + a.serial + ('-negative' if a.negative_control else ''))
out.mkdir(parents=True, exist_ok=True)
def guest(command):
    return subprocess.check_output(client + ['exec', '/usr/bin/bash', '-c',
        'source "$XDG_RUNTIME_DIR/omarchy-session.env"; ' + command], text=True).strip()
def query(what):
    return json.loads(guest('hyprctl -j ' + what))
def dispatch(expression):
    guest('hyprctl dispatch ' + shlex.quote(expression))
def key(*codes):
    subprocess.run(adb + ['shell', 'input', 'keyevent', *map(str, codes)], check=True)
def shot(name):
    time.sleep(.6)
    data = subprocess.check_output(adb + ['exec-out', 'screencap', '-p'])
    (out / (name + '.png')).write_bytes(data)
    return Image.open(io.BytesIO(data)).convert('RGB')
original = query('activeworkspace')['id']
workspace = max([w['id'] for w in query('workspaces')] + [90]) + 1
name = 'Arlinux terminal erase regression'
window = None
try:
    dispatch('hl.dsp.focus({workspace=' + json.dumps(str(workspace)) + '})')
    command = shlex.join(['omarchy-launch-terminal', '-title', name, '-e', 'env',
        'PS1=Erase test> ', 'PROMPT_COMMAND=printf "\\033[?25l"',
        'bash', '--noprofile', '--norc'])
    dispatch('hl.dsp.exec_cmd(' + json.dumps(command) + ')')
    for _ in range(60):
        window = next((w for w in query('clients') if w['initialTitle'] == name), None)
        if window:
            break
        time.sleep(.2)
    assert window, 'Test terminal did not map'
    time.sleep(1)
    if a.negative_control:
        dispatch('hl.dsp.window.set_prop({prop="force_rgbx",value="0"})')
    monitor = next(m for m in query('monitors') if m['id'] == window['monitor'])
    before = shot('before')
    # The Android display occupies the right side beside the landscape cutout.
    scale = monitor['scale']
    x = before.width - monitor['width'] + round(window['at'][0] * scale)
    y = round(window['at'][1] * scale)
    width = round(window['size'][0] * scale)
    band = (x + 4, y + 4, x + width - 4, y + round(40 * scale))
    key(29)  # a
    typed = shot('typed-a')
    assert ImageChops.difference(before.crop(band), typed.crop(band)).getbbox(), 'Key did not reach XTerm'
    key(67)  # Backspace
    erased = shot('backspace')
    subprocess.run(adb + ['shell', 'input', 'keycombination', '113', '40'], check=True)  # Ctrl+L
    cleared = shot('clear')
    result = {}
    for label, picture in [('backspace', erased), ('clear', cleared)]:
        delta = ImageChops.difference(before.crop(band), picture.crop(band))
        changed = sum(max(pixel) > 16 for pixel in delta.getdata())
        result[label + 'ChangedPixels'] = changed
        assert changed < 20, f'{label}: {changed} background pixels changed'
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(out / 'result.json')
finally:
    if window:
        dispatch('hl.dsp.window.close({address=' + json.dumps(window['address']) + '})')
    dispatch('hl.dsp.focus({workspace=' + json.dumps(str(original)) + '})')
