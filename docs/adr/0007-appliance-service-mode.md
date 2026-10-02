# 0007 — Appliance service mode

Date: 2026-10-02. Status: Accepted implementation direction; device acceptance pending.

Context: ADR-0004 targets a dedicated graphical session without a desktop. Closing the kiosk in that session would leave a blank panel or trigger a supervisor restart. The original desktop runtime must retain its existing exit path.

Decision: only when explicitly launched with `PI_HUB_APPLIANCE=1`, the confirmed exit action opens a bilingual service screen. It stops active playback and the external browser owned by the hub, keeps diagnostics and the local backend alive, and offers a touch action to return. It preserves preferences. This screen does not expose a shell or grant administrator privileges. A separate authenticated recovery channel remains necessary before OS deployment.

The ordinary desktop runtime keeps its supervised exit-to-desktop behavior. API state identifies the deployment mode so labels and actions describe the actual result. Successful backend reconnection clears its connection error, while unrelated operation errors remain visible.

Consequences: PRODUCT and BOOT-02 distinguish deployment modes explicitly. Automated tests cover cancellation, service entry, protected return, failed playback stop, preferences and EN/RO × themes at 800×480. OS boot, recovery credentials, physical touch and relaunch acceptance remain OPEN.
