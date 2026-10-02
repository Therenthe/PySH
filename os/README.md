# OS integration

Reserved for the appliance integration in ADR-0001–0004. No bootable image or Lite migration has been implemented. Existing graphical-session installation remains in scripts/install-session.sh until its replacement is validated.

image/ owns image manifests/build; systemd/ owns future static service definitions; udev/ owns narrowly scoped device rules; boot/ owns boot/session configuration; packages/ owns OS package lists; branding/ owns OS branding. Do not add speculative scripts or enable them automatically.
