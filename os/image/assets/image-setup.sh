#!/bin/bash
# Build-time genimage hook. No live block devices are modified.
set -euo pipefail
source "${IGconf_image_outputdir}/img_uuids"
[[ "$ROOT_UUID" =~ ^[0-9a-fA-F]{8}(-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$ ]]
[[ "$BOOT_UUID" =~ ^[0-9a-fA-F]{4}-[0-9a-fA-F]{4}$ ]]
case "${1:?partition label required}" in
  ROOT)
    test "${IGconf_image_rootfs_type}" = ext4
    cat > "${IMAGEMOUNTPATH}/etc/fstab" <<EOF
UUID=$ROOT_UUID / ext4 rw,relatime,errors=remount-ro,commit=30 0 1
UUID=$BOOT_UUID /boot/firmware vfat defaults,rw,noatime,errors=remount-ro 0 2
EOF
    ;;
  BOOT)
    # Refuse an unexpected upstream cmdline rather than emitting an unbootable image.
    test "$(grep -oE '(^|[[:space:]])root=[^[:space:]]+' "${IMAGEMOUNTPATH}/cmdline.txt" | wc -l)" -eq 1
    sed -i -E "s#(^|[[:space:]])root=[^[:space:]]+#\1root=UUID=$ROOT_UUID#" "${IMAGEMOUNTPATH}/cmdline.txt"
    ;;
  *) echo "Unexpected partition label: $1" >&2; exit 1 ;;
esac
