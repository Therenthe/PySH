# OS integration

Appliance integration follows ADR-0001–0006. An experimental image definition and build workflow now exist in image/; no bootable artifact or Lite migration has yet been validated. Existing graphical-session installation remains in scripts/install-session.sh until its replacement is validated.

image/ owns image manifests/build; systemd/ owns future static service definitions; udev/ owns narrowly scoped device rules; boot/ owns boot/session configuration; packages/ owns OS package lists; branding/ owns OS branding. Do not add speculative scripts or enable them automatically.
