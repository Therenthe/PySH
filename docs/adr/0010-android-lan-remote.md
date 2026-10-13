# 0010 — Android remote over authenticated private LAN HTTPS

Status: Accepted for the owner's requested Android/LAN scope; implementation and
local protocol tests prepared, physical phone/Pi acceptance pending.
Date: 2026-10-13.

The owner explicitly requested a native Android application with full PySH
control, superior UI/UX, and communication on LAN only, without internet remote
control. This extends the earlier product scope that deliberately exposed no
network-visible administration port. It does not authorize exposing the existing
API, adding a cloud relay, weakening browser/origin checks, or device deployment
without following the existing delivery/operations workflow.

Keep the backend bound to `127.0.0.1:8765`. Add a separately enabled gateway under
`services/remote`, bound to one explicitly configured private LAN IP, normally
port 8766. Only RFC1918 IPv4, ULA and link-local IPv6 are valid listener/peer
addresses. Refuse public, wildcard, loopback, hostname and IPv4-mapped IPv6 binding.
Use the same unprivileged graphical-session user, the existing runtime/venv, and
a separate hardened systemd user unit. A DHCP reservation keeps the listener IP
stable; an unavailable IP causes a visible service failure, never wildcard fallback.

Use HTTPS with a locally generated certificate and Android pinning over SHA-256
of its full DER X.509 certificate. Display the fingerprint and one-time 8-digit
pairing code through a local CLI. Pairing expires after five minutes, permits five
attempts, and is consumed after one phone. Each phone receives an independent
random bearer token; persist only its hash. Allow local enumeration/revocation
with immediate effect and retain identities across gateway/PySH restart. Pairing
state, certificate/private key and hashes live outside source/release files in
the user's protected application-data directory.

Forward a method/path allowlist to the constant loopback API. Never forward the
phone bearer header, browser headers or an arbitrary target URL. The gateway
obtains the backend mutation token internally through `/api/session`; that route
is never available remotely. Retry a mutation only after the existing boundary
returns `session_expired`, which means it was denied before execution. Do not
retry uncertain/time-out operations automatically. Exclude file downloads,
static browser assets and internal DRM reports; playback and browser sessions
remain on Pi. Native-phone commands include Bluetooth prompt replies and Wi-Fi
configuration with their existing backend validations.

Bound bodies, responses, per-peer/global request rates, pairing attempts, TLS
handshake time and concurrent worker count. Do not log request URLs, device names,
Wi-Fi credentials, submitted bodies, pairing codes or tokens. No generic shell,
root helper, remote desktop, UPnP, internet service, account or tunnel is added.
Private-address filtering cannot detect WAN traffic rewritten by a router into a
private source address; LAN-only operation also requires no port forwarding, DMZ,
public reverse proxy or tunnel. This operational boundary is documented explicitly.

Alternatives: exposing FastAPI directly would broaden and weaken the trusted
loopback/browser boundary; cleartext HTTP would expose control credentials to LAN
observers; a cloud relay contradicts the owner's requirement; manually shared
permanent passwords do not provide independent revocable phone identities.

Consequences: the Android client needs the Pi address and locally observed pin
for first pairing, supports only documented API capabilities, and must explain
offline, revoked, expired-code and unavailable-hardware states. "Full control"
covers supported hub commands; no implementation can claim that arbitrary input
inside third-party account/browser pages or unimplemented backend functionality
has been provided. Source, unit/protocol checks and an APK do not certify actual
phone/Pi operation. Installation and hardware acceptance remain explicit steps.

See [setup and wire contract](../ANDROID_REMOTE.md) and
`tests/test_remote_gateway.py` for scoped evidence.
