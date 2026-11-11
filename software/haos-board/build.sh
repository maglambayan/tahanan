#!/usr/bin/env bash
# Reproducible Home Assistant OS image for the Tahanan Hub.
# Needs: Linux x86_64 or arm64 build host, Docker, ~60 GB disk, 2-4 hours. Not runnable on macOS.
# The image is the upstream rpi5_64 target (which supports CM5) plus this board's overlay, kernel options,
# config.txt block and root file system additions. Nothing else in Home Assistant OS is modified.
#
# Written against the tree layout of Home Assistant OS 18.5. Every upstream file this script touches is
# checked first, so a release that moved things fails here with a message instead of building a wrong image.
# Status: the tree preparation was dry-run against the 18.5 file layout. The image itself has NOT been built.
set -euo pipefail
HAOS_TAG="${HAOS_TAG:-18.5}"
HERE="$(cd "$(dirname "$0")" && pwd)"; SW="$HERE/.."; WORK="${WORK:-$HERE/work}"
mkdir -p "$WORK"; cd "$WORK"
[ -d operating-system ] || git clone --recurse-submodules --branch "$HAOS_TAG" https://github.com/home-assistant/operating-system.git
cd operating-system
EXT=buildroot-external
BOARD=$EXT/board/raspberrypi/rpi5-64
DEFCONFIG=$EXT/configs/rpi5_64_defconfig
for f in "$BOARD/haos-hook.sh" "$BOARD/config.txt" "$DEFCONFIG"; do
    test -f "$f" || { echo "$f not found in $HAOS_TAG: the upstream layout changed, update this script."; exit 1; }
done
grep -q '^BR2_LINUX_KERNEL_CONFIG_FRAGMENT_FILES=".*"$' "$DEFCONFIG" || { echo "Kernel fragment list not found in $DEFCONFIG."; exit 1; }
if [ -e .tahanan-applied ]; then
    echo "This tree already has the Tahanan changes. Delete $WORK/operating-system to start again."; exit 1
fi
# 1. kernel options: a fragment of our own, added to the end of the fragment list
cp "$HERE/kernel-tahanan.config" "$BOARD/kernel-tahanan.config"
sed -i.orig 's|^\(BR2_LINUX_KERNEL_CONFIG_FRAGMENT_FILES=".*\)"$|\1 $(BR2_EXTERNAL_HAOS_PATH)/board/raspberrypi/rpi5-64/kernel-tahanan.config"|' "$DEFCONFIG"
rm -f "$DEFCONFIG.orig"
grep -q 'kernel-tahanan.config' "$DEFCONFIG"
# 2. amixer on the host, used once at boot by tahanan-audio-init
printf 'BR2_PACKAGE_ALSA_UTILS=y\nBR2_PACKAGE_ALSA_UTILS_AMIXER=y\n' >> "$DEFCONFIG"
# 3. device tree overlay source. The patch in step 6 compiles it during the image build
mkdir -p "$BOARD/tahanan" && cp "$SW/dts/tahanan-overlay.dts" "$BOARD/tahanan/"
# 4. config.txt block
cat "$SW/boot/config.txt.tahanan" >> "$BOARD/config.txt"
# 5. root file system additions (udev names, mixer defaults and the unit that applies them)
mkdir -p "$BOARD/rootfs-overlay" && cp -a "$SW/rootfs/." "$BOARD/rootfs-overlay/"
# 6. image hook that compiles the overlay with the kernel's dtc and include path
for p in "$HERE"/patches/*.patch; do git apply "$p"; done
touch .tahanan-applied
echo "Tree prepared from Home Assistant OS $HAOS_TAG. Build with:  sudo scripts/enter.sh make rpi5_64"
echo "Output: output/images/haos_rpi5-64-*.img.xz  ->  flash to the NVMe SSD (see docs/recovery-and-update.md)"
