#!/usr/bin/env python3
"""Check clean application, repeat startup and refusal of modified QML."""
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

product = Path(__file__).resolve().parents[1]
paths = re.findall(r'^--- a/(.+)$', (product / 'guest/shell-accessibility.patch').read_text(), re.M)
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    guest = root / 'usr/lib/arlinux/guest'
    guest.parent.mkdir(parents=True)
    guest.symlink_to(product / 'guest')
    source = root / 'omarchy'
    def reset():
        for path in paths:
            dest = source / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(product / 'third_party/omarchy' / path, dest)
    def snapshot():
        return {path: (source / path).read_bytes() for path in paths}
    def apply():
        return subprocess.run(['python3', str(guest / 'bin/omarchy-apply-accessibility')],
            env=dict(os.environ, BIONICX_ROOTFS=str(root), OMARCHY_PATH=str(source)),
            capture_output=True, text=True)
    reset()
    original = snapshot()
    result = apply()
    assert result.returncode == 0, result.stderr
    adapted = snapshot()
    assert all(adapted[p] != original[p] for p in paths)
    assert apply().returncode == 0
    assert snapshot() == adapted
    reset()
    target = source / paths[-1]
    target.write_text('user replacement\n')
    modified = snapshot()
    assert apply().returncode != 0
    assert snapshot() == modified, 'Failure partly overwrote the desktop'
print('Accessibility patch: clean apply, idempotency and conflict preservation passed')
