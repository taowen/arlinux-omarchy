#!/usr/bin/env bash
set -euo pipefail
product="$(cd "$(dirname "$0")/.." && pwd)"
out="${1:?rootfs output required}"
mkdir -p "$product/build/cache" "$out"
python3 - "$product" <<'PY'
import hashlib, json, pathlib, subprocess, sys
p = pathlib.Path(sys.argv[1]); lock = json.loads((p / 'rootfs.lock.json').read_text())
archive = p / 'build/cache/rootfs.tar.gz'
if not archive.is_file():
    subprocess.run(['curl', '-fL', '--retry', '2', lock['url'], '-o', str(archive)], check=True)
with archive.open('rb') as source:
    actual = hashlib.file_digest(source, 'sha256').hexdigest()
if actual != lock['sha256']:
    raise SystemExit('Rootfs hash changed; review and update rootfs.lock.json before building')
PY
tar --delay-directory-restore --no-same-owner --exclude=./dev --exclude=./proc --exclude=./sys \
    --exclude=./boot --exclude=./usr/lib/modules -xzf "$product/build/cache/rootfs.tar.gz" -C "$out"
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
PYSEED
