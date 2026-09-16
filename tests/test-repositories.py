#!/usr/bin/env python3
"""Exercise repository bootstrap, APK updates and failed-keyring retries."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

product = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory) / 'root'
    commands = Path(directory) / 'bin'
    commands.mkdir()
    (root / 'etc').mkdir(parents=True)
    config = root / 'etc/pacman.conf'
    config.write_text('[options]\nSigLevel = Required DatabaseOptional\n[core]\nServer = https://example.invalid/core\n')
    guest = root / 'usr/lib/arlinux/guest'
    shutil.copytree(product / 'guest', guest)
    platform = root / 'usr/lib/arlinux-platform'
    platform.mkdir(parents=True)
    (root / 'usr/bin').mkdir()
    ldconfig = platform / 'ldconfig'
    ldconfig.write_text('#!/bin/sh\nexit 0\n')
    ldconfig.chmod(0o755)
    state = Path(directory) / 'installed.json'
    state.write_text('[]')
    log = Path(directory) / 'commands.jsonl'
    helper = '''
import json, os, pathlib, sys
name = pathlib.Path(sys.argv[0]).name
args = sys.argv[1:]
with open(os.environ['TEST_COMMAND_LOG'], 'a') as out:
    out.write(json.dumps([name, *args]) + '\\n')
if name == 'bsdtar':
    print('test CLI payload')
    sys.exit(0)
if name != 'pacman': sys.exit(0)
if args[0] == '-Spdd':
    print('hyprland-test-aarch64.pkg.tar.zst')
    sys.exit(0)
if args[0] == '-Sddw': sys.exit(0)
state = pathlib.Path(os.environ['TEST_INSTALLED'])
installed = set(json.loads(state.read_text()))
if args[0] == '-Q': sys.exit(0 if all(p in installed for p in args[1:]) else 1)
if 'archlinuxcn-keyring' in args and os.environ.get('TEST_FAIL_KEYRING') == '1': sys.exit(17)
installed.update(a for a in args[1:] if not a.startswith('-'))
state.write_text(json.dumps(sorted(installed)))
'''
    for name in ('pacman', 'pacman-key', 'gpgconf', 'bsdtar'):
        executable = commands / name
        executable.write_text(f'#!{sys.executable}\n' + helper)
        executable.chmod(0o755)
    env = {**os.environ, 'BIONICX_ROOTFS': str(root),
           'PATH': str(commands) + ':' + str(root / 'usr/bin') + ':' + os.environ['PATH'],
           'TEST_INSTALLED': str(state), 'TEST_COMMAND_LOG': str(log)}
    def run(**extra):
        log.write_text('')
        result = subprocess.run(['sh', str(guest / 'first-boot.sh')],
                                env={**env, **extra}, capture_output=True, text=True)
        calls = [json.loads(line) for line in log.read_text().splitlines()]
        return result, calls
    result, calls = run(TEST_FAIL_KEYRING='1')
    assert result.returncode == 17, result.stderr
    assert not any(c[:2] == ['pacman', '-Syyu'] for c in calls)
    assert config.read_text().count('[archlinuxcn]') == 1
    assert config.read_text().index('[archlinuxcn]') < config.read_text().index('[core]')
    result, calls = run()
    assert result.returncode == 0, result.stderr
    trust = calls.index(['pacman-key', '--populate', 'archlinux'])
    keyring = next(i for i, c in enumerate(calls) if c[:2] == ['pacman', '-Sy'])
    upgrade = next(i for i, c in enumerate(calls) if c[:2] == ['pacman', '-Syyu'])
    assert trust < keyring < upgrade
    assert 'hyprland' not in json.loads(state.read_text())
    assert (root / 'usr/bin/hyprctl').read_text() == 'test CLI payload\n'
    assert ['pacman', '-Sddw', '--noconfirm', 'hyprland'] in calls
    assert 'SigLevel = Required DatabaseOptional' in config.read_text()
    assert 'SigLevel = Never' not in config.read_text()
    assert calls[-1][0] == 'gpgconf', 'bootstrap left its signing agent running'
    config.write_text(config.read_text().replace(
        'https://mirrors.tuna.tsinghua.edu.cn/archlinuxcn/$arch',
        'https://custom.example/archlinuxcn/$arch'))
    before = config.read_bytes()
    result, calls = run()
    assert result.returncode == 0, result.stderr
    assert config.read_bytes() == before, 'APK refresh replaced repository settings'
    assert ['pacman-key', '--populate', 'archlinuxarm', 'archlinux', 'archlinuxcn'] in calls
    assert not any(c[0] == 'pacman' and c[1].startswith('-S') for c in calls)
    # Existing desktops gain the default repository on APK update too.
    text = config.read_text()
    start = text.index('[archlinuxcn]')
    end = text.index('[core]', start)
    config.write_text(text[:start] + text[end:])
    result, calls = run()
    assert result.returncode == 0, result.stderr
    assert config.read_text().count('[archlinuxcn]') == 1
    assert config.read_text().index('[archlinuxcn]') < config.read_text().index('[core]')
print('PASS: trust order, signature policy, failed install retry, idempotent update and custom mirror preservation')
