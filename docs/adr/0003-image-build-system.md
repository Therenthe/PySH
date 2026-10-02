# 0003 — Image build system

Date: 2026-10-02. Status: Proposed.

Context: rpi-image-gen a fost propus în conversație; proiectul local nu conține builder sau imagine verificată.

Decision proposed: evaluați rpi-image-gen după validarea bazei OS; fixați versiunea, manifestul de pachete și intrările build-ului. Comparați costul cu integrarea existentă înainte de adoptare.

Consequences: os/image/ este locul rezervat; CI actual construiește aplicația, nu o imagine de sistem. Nu promitem reproducibilitate până la două build-uri comparate și boot real.
