#!/bin/bash
# Only for an ephemeral Linux build host. This never flashes a block device.
set -euo pipefail
cd /workspace
test "$(uname -m)" = aarch64
test -f os/image/payload/source.json
free_kib="$(df -Pk /workspace | awk 'NR==2 {print $4}')"
test "$free_kib" -ge 10000000 || { echo 'Need at least 10 GB free build storage'; exit 1; }
apt-get update
apt-get install -y --no-install-recommends ca-certificates git sudo curl
git clone https://github.com/raspberrypi/rpi-image-gen.git /tmp/pysh-image-gen
git -C /tmp/pysh-image-gen checkout --detach 262d4df5a9f9d4133370465399a7958a7c22cdc7
test "$(git -C /tmp/pysh-image-gen rev-parse HEAD)" = 262d4df5a9f9d4133370465399a7958a7c22cdc7
bash /tmp/pysh-image-gen/install_deps.sh
mkdir -p .runtime/os-build
bash /tmp/pysh-image-gen/rpi-image-gen build -S /workspace/os/image \
  -c /workspace/os/image/config/pysh-pi4.yaml -B /workspace/.runtime/os-build \
  2>&1 | tee /workspace/.runtime/os-build/build.log
find /workspace/.runtime/os-build -type f -name 'pysh-pi4-candidate.img' -print -quit > /workspace/.runtime/os-build/image-path.txt
image="$(cat /workspace/.runtime/os-build/image-path.txt)"
test -n "$image" && test -s "$image"
mkdir -p /workspace/.runtime/os-artifact
gzip -1 -c "$image" > /workspace/.runtime/os-artifact/pysh-pi4-candidate.img.gz
cp os/image/payload/source.json /workspace/.runtime/os-artifact/source.json
cp os/image/payload/manifest.json /workspace/.runtime/os-artifact/runtime-manifest.json
cd /workspace/.runtime/os-artifact
sha256sum pysh-pi4-candidate.img.gz > SHA256SUMS
printf '%s\n' 'EXPERIMENTAL: do not flash. Recovery provisioning, real boot and full product acceptance are pending.' > NOT-FLASH-READY.txt
