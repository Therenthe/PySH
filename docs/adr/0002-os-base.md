# 0002 — OS base

Date: 2026-10-02. Status: Proposed.

Context: ținta discutată este Raspberry Pi OS Lite 64-bit; auditul vechi arată un sistem cu desktop, derivat Debian 13.4.

Decision proposed: validați Lite 64-bit pe o imagine de test, inclusiv DSI, touch, compositor, BlueZ, NetworkManager, PipeWire și Chromium. Fixați imaginea și checksumul după probe.

Consequences: nu declarăm Lite instalat și nu suprascriem cardul existent. Versiunea și proveniența imaginii finale rămân deschise.
