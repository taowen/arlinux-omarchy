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

# Pin the community repository trust root before the phone ever contacts it.
cn=archlinuxcn-keyring-20260505-1-any.pkg.tar.zst
cn_sha=f8ed39c21babdf8fccfc36f603bc6d99c808332238d7e5297714a0f1f624e17a
if [[ ! -f "$cache/$cn" ]]; then
    curl -fL --retry 2 "https://mirrors.tuna.tsinghua.edu.cn/archlinuxcn/aarch64/$cn" -o "$cache/$cn.part"
    mv "$cache/$cn.part" "$cache/$cn"
fi
echo "$cn_sha  $cache/$cn" | sha256sum -c -
tar --zstd -xf "$cache/$cn" -C "$out" \
    usr/share/pacman/keyrings/archlinuxcn.gpg \
    usr/share/pacman/keyrings/archlinuxcn-trusted \
    usr/share/pacman/keyrings/archlinuxcn-revoked

python3 - "$out" <<'PY'
import pathlib, shutil, sys
root = pathlib.Path(sys.argv[1])
shutil.rmtree(root / 'usr/lib/firmware', ignore_errors=True)
for package in (root / 'var/lib/pacman/local').iterdir():
    desc = package / 'desc'
    if not desc.is_file(): continue
    lines = desc.read_text(errors='replace').splitlines()
    try: name = lines[lines.index('%NAME%') + 1]
    except (ValueError, IndexError): continue
    if name == 'linux-aarch64' or name == 'linux-firmware' or name.startswith('linux-firmware-'):
        shutil.rmtree(package)
PY

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

# The shipped shell source is immutable at runtime. Apply the Android AT-SPI
# adaptation and install its icon font while the rootfs is assembled.
patch --batch --forward --fuzz=0 -p1 -d "$out/usr/share/omarchy" \
    < "$product/guest/shell-accessibility.patch"
install -Dm644 "$out/usr/share/omarchy/default/fonts/omarchy/omarchy.ttf" \
    "$out/usr/share/fonts/omarchy/omarchy.ttf"
