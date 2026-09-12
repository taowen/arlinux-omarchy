#!/usr/bin/env python3
"""Exercise native ALPM install, upgrade, scriptlets and removal on Android."""
import argparse
import io
import json
import os
from pathlib import Path
import shlex
import subprocess
import tarfile

product = Path(__file__).resolve().parents[1]
core = Path(os.environ.get('ARLINUX_DIR', product / 'third_party/arlinux')).resolve()
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--serial', required=True)
a = p.parse_args()
package = json.loads((product / 'product.json').read_text())['applicationId']
build = product / 'build/pacman-test'; build.mkdir(parents=True, exist_ok=True)
adb = ['adb', '-s', a.serial]
base = [str(core / 'tools/product-device.py'), '--serial', a.serial, '--product', str(product)]

def guest(*args, check=True):
    return subprocess.run(base + ['exec', *args], check=check, text=True, capture_output=True)

def archive(version):
    out = build / ('arlinux-package-gate-' + version + '-1-aarch64.pkg.tar.gz')
    files = {
        '.PKGINFO': f'pkgname = arlinux-package-gate\npkgver = {version}-1\npkgdesc = Arlinux ALPM regression\nurl = https://github.com/taowen/arlinux-omarchy\nbuilddate = 0\npackager = Arlinux test\nsize = 100\narch = aarch64\nlicense = GPL\n',
        '.INSTALL': '''post_install() {
    /usr/bin/bash -c 'id -u > /var/lib/arlinux-package-gate/uid'
}
post_upgrade() {
    post_install
    echo upgraded > /var/lib/arlinux-package-gate/upgrade
}
post_remove() {
    echo removed > /tmp/arlinux-package-gate-removed
}
''',
        'var/lib/arlinux-package-gate/version': version + '\n',
    }
    with tarfile.open(out, 'w:gz') as tar:
        for name, data in files.items():
            raw = data.encode(); info = tarfile.TarInfo(name)
            info.size = len(raw); info.mode = 0o644
            tar.addfile(info, io.BytesIO(raw))
    remote = '/data/local/tmp/' + out.name
    subprocess.run(adb + ['push', str(out), remote], check=True)
    script = 'cp ' + shlex.quote(remote) + ' files/rootfs/var/tmp/' + out.name
    subprocess.run(adb + ['shell', shlex.join(['run-as', package, 'sh', '-c', script])], check=True)
    return '/var/tmp/' + out.name

guest('/usr/bin/bash', '-c',
      'before=$(id -u); test "$before" != 0; pacman --version >/dev/null; test "$(id -u)" = "$before"')
if guest('/usr/bin/pacman', '-Q', 'arlinux-package-gate', check=False).returncode == 0:
    raise SystemExit('Remove an existing arlinux-package-gate test package before running')
try:
    for version in ('1.0', '2.0'):
        result = guest('/usr/bin/pacman', '-U', '--noconfirm', archive(version))
        print(result.stdout, end=''); print(result.stderr, end='')
        assert guest('/usr/bin/cat', '/var/lib/arlinux-package-gate/version').stdout.strip() == version
        assert guest('/usr/bin/cat', '/var/lib/arlinux-package-gate/uid').stdout.strip() == '0'
    assert guest('/usr/bin/cat', '/var/lib/arlinux-package-gate/upgrade').stdout.strip() == 'upgraded'
finally:
    result = guest('/usr/bin/pacman', '-Rns', '--noconfirm', 'arlinux-package-gate', check=False)
    print(result.stdout, end=''); print(result.stderr, end='')
assert guest('/usr/bin/pacman', '-Q', 'arlinux-package-gate', check=False).returncode != 0
assert guest('/usr/bin/cat', '/tmp/arlinux-package-gate-removed').stdout.strip() == 'removed'
guest('/usr/bin/bash', '-c', 'rm -rf /var/lib/arlinux-package-gate /tmp/arlinux-package-gate-removed /var/tmp/arlinux-package-gate-*.pkg.tar.gz')
print('PASS pacman install / upgrade / scriptlet virtual UID / removal')
