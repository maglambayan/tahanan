#!/usr/bin/env bash
# Reproducible Home Assistant OS image for the Tahanan Hub.
# Needs: Linux x86_64 or arm64 build host, Docker, ~60 GB disk, 2-4 hours. Not runnable on macOS.
# The image is the upstream rpi5_64 target (which supports CM5) plus this board's overlay, kernel options,
# config.txt block and root file system additions. Nothing else in Home Assistant OS is modified.
set -euo pipefail
HAOS_TAG="${HAOS_TAG:?set HAOS_TAG to the Home Assistant OS release to build, e.g. the current stable tag}"
HERE="$(cd "$(dirname "$0")" && pwd)"; SW="$HERE/.."; WORK="${WORK:-$HERE/work}"
mkdir -p "$WORK"; cd "$WORK"
[ -d operating-system ] || git clone --recurse-submodules --branch "$HAOS_TAG" https://github.com/home-assistant/operating-system.git
cd operating-system
BOARD=buildroot-external/board/raspberrypi/rpi5-64
test -d "$BOARD" || { echo "Board directory $BOARD not found in $HAOS_TAG: check the upstream layout and update this script."; exit 1; }
# 1. kernel options
cat "$HERE/kernel-tahanan.config" >> "$BOARD/kernel.config"
# 2. device tree overlay: compiled out of tree and installed into the boot partition overlays directory
mkdir -p "$BOARD/tahanan" && cp "$SW/dts/tahanan-overlay.dts" "$BOARD/tahanan/"
# 3. config.txt block
cat "$SW/boot/config.txt.tahanan" >> "$BOARD/config.txt"
# 4. root file system additions (udev names, mixer defaults)
mkdir -p buildroot-external/rootfs-overlay && cp -a "$SW/rootfs/." buildroot-external/rootfs-overlay/
# 5. post-image hook that compiles the overlay with the kernel's dtc and include path
for p in "$HERE"/patches/*.patch; do [ -e "$p" ] && git apply "$p"; done
echo "Tree prepared. Build with:  sudo scripts/enter.sh make rpi5_64"
echo "Output: output/images/haos_rpi5-64-*.img.xz  ->  flash to the NVMe SSD (see docs/recovery-and-update.md)"
