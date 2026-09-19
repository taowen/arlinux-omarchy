#!/usr/bin/env bash
set -euo pipefail
product="$(cd "$(dirname "$0")/.." && pwd)"
out="${1:?rootfs output required}"
cache="${ARLINUX_DOWNLOAD_CACHE:-/var/cache/arlinux/downloads}"
mkdir -p "$cache" "$out"
python3 - "$product" "$cache" <<'PY'
import hashlib, json, pathlib, subprocess, sys
p, cache = map(pathlib.Path, sys.argv[1:]); lock = json.loads((p / 'rootfs.lock.json').read_text())
archive = cache / ('rootfs-' + lock['sha256'] + '.tar.gz')
if not archive.is_file():
    partial = archive.with_suffix('.part')
    subprocess.run(['curl', '-fL', '--retry', '2', lock['url'], '-o', str(partial)], check=True)
    partial.replace(archive)
with archive.open('rb') as source:
    actual = hashlib.file_digest(source, 'sha256').hexdigest()
if actual != lock['sha256']:
    raise SystemExit('Rootfs hash changed; review and update rootfs.lock.json before building')
PY
archive="$(python3 -c 'import json,sys; x=json.load(open(sys.argv[1])); print(sys.argv[2]+"/rootfs-"+x["sha256"]+".tar.gz")' "$product/rootfs.lock.json" "$cache")"
tar --delay-directory-restore --no-same-owner --exclude=./dev --exclude=./proc --exclude=./sys \
    --exclude=./boot --exclude=./usr/lib/modules -xzf "$archive" -C "$out"
cp "$product/guest/mirrorlist" "$out/etc/pacman.d/mirrorlist"

python3 - "$product" "$out" <<'PYSEED'
import json, pathlib, subprocess, sys
product, out = map(pathlib.Path, sys.argv[1:])
source = product / 'third_party/omarchy'
expected = json.loads((product / 'rootfs.lock.json').read_text())['omarchyCommit']
actual = subprocess.check_output(['git', '-C', source, 'rev-parse', 'HEAD'], text=True).strip()
if actual != expected:
    raise SystemExit('Omarchy checkout does not match rootfs.lock.json')
destination = out / 'usr/share/omarchy'
destination.mkdir(parents=True)
archive = subprocess.Popen(['git', '-C', source, 'archive', expected], stdout=subprocess.PIPE)
try:
    subprocess.run(['tar', '-xf', '-', '-C', destination], stdin=archive.stdout, check=True)
finally:
    archive.stdout.close()
if archive.wait(): raise SystemExit('Omarchy source archive failed')
# Hosted WeChat Input replaces Omarchy's Linux input-method service.
for relative in (
    'default/environment.d/10-omarchy-fcitx.conf',
    'default/systemd/user/omarchy-fcitx5.service',
    'bin/omarchy-restart-xcompose',
    'migrations/1785167800.sh',
):
    path = destination / relative
    if path.exists(): path.unlink()
config = destination / 'config/fcitx5'
if config.exists():
    import shutil
    shutil.rmtree(config)
autostart = destination / 'config/autostart/org.fcitx.Fcitx5.desktop'
if autostart.exists(): autostart.unlink()
packages = destination / 'install/omarchy-base.packages'
packages.write_text('\n'.join(
    line for line in packages.read_text().splitlines()
    if not line.startswith('fcitx5')
) + '\n')
units = destination / 'install/user/first-run/enable-user-units.sh'
units.write_text('\n'.join(
    line for line in units.read_text().splitlines()
    if 'omarchy-fcitx5.service' not in line
) + '\n')
PYSEED
