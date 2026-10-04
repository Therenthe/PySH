# Corrected PySH OS cold-power boot checks — 2026-10-03

Candidate runtime `a32c29065d6d`, image source `d61ec8d23c4c025167bd009a67e9cfcab4193a72`. Owner performs physical power removal/reconnection after controlled `systemctl poweroff`; original SD stays out and retained. A normal OS reboot is recorded separately and is not counted.

| Cold cycle | Boot ID | Successful audit at boot uptime | Result |
|---|---|---|---|
| 1, initial corrected USB installation | 7ced882f-dfa4-48e5-be77-8655baedb2ff | 162.76 s | Installed manifest, real display and services verified; owner confirmed touch. |
| 2 | 4154e1c4-b38a-4190-93cb-887533fbe115 | 43.54 s | All 33 runtime hashes, API, native 800×480/180°, pysh.service active, zero failed system services. |
| 3 | 5d12f7cb-b03c-4d44-a490-bc3661c77449 | 41.42 s | Same checks passed; graphical user session active at 11.196066 s. |
| 4 | 8f0ada7e-5cac-4aad-b00e-1ec8fdde9d60 | 23.74 s | Same checks passed; graphical user session active at 11.228363 s. |
| 5, LAN disconnected before power-on | 881691e8-7a80-41cd-b0b2-418403a2175e | 69.96 s after LAN return | Owner confirmed Home and touch Settings→Home offline. Return audit passed all 33 hashes, native output, API and services. |

These are upper bounds at which inspection found a running candidate, not exact Home-render times. Native compositor captures are stored separately by boot ID. No debug listener, no runtime or system package repair between these cycles. Firmware: release `a86983925695a7e63166327d7c002d64040ed31d`, built 2026-09-14 14:49:30. Actual target Pi 4 Model B Rev 1.5, MemTotal 3,885,804 kB, Debian 13 arm64, kernel 6.18.50+rpt-rpi-v8.

Before the offline cycle, NetworkManager listed only an Ethernet profile and loopback; no saved Wi-Fi profile. On cycle 5, the real monotonic journal records graphical user session active at 11.216624 s and API startup complete at 14.730066 s. Ethernet carrier appeared only at 47.904731 s; IPv4 activated at 48.140058 s, without application restart. Owner confirmed the offline Home and touch Settings→Home before reconnecting LAN. No Wi-Fi activation occurred. The instructed wait was approximately a minute; the actual journal establishes that physical LAN return occurred at 47.90 s, so this record uses that observed timing.

BOOT-01 passes for the identified candidate and this physical scope. Distinct native Home captures from cycles 2–5 were transferred to PC and visually reviewed. The [fresh-candidate capture and evidence](os-a32c29065d6d-acceptance-2026-10-03.md) identify the same installed runtime; boot-specific private captures and journals are retained outside Git. Review found overflowing forecast content in the populated Home weather card. UX-02 is FAIL pending repair; successful boot does not imply visually accepted UI. Exact Home-render latency and continuous eight-hour stability remain separate and unverified.
