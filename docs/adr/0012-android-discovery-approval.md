# 0012 — Local Android discovery and screen approval

Accepted. Android App Control is managed from PySH Settings. A local supervisor
binds one private IPv4 interface and advertises `_pysh-control._tcp` through
Avahi, with a persistent hub UUID and protocol version 2. Address changes rebind
the listener without replacing the certificate or paired-device store. Disabling
the service closes its listener and advertisement; the owner can enable it again
from the local screen. Avahi is an explicit OS runtime dependency; Python uses
the existing locked dbus-next dependency.

The remote unit adds only AF_NETLINK to its existing address-family restriction
because iproute2 reads interface/route data through netlink. NoNewPrivileges
remains enabled. The updater accepts only this exact addition to the verified
previous unit, preserves ownership/mode and restores both unit and code on failure.

Android discovers in the foreground on Wi-Fi/Ethernet. Initial public identity
bootstrap sends no credentials or commands. The phone creates an ephemeral
RSA3072 key, requests pairing and polls a short-lived secret-bound request.
Only the local authenticated API can approve or deny it. The hub shows the
phone's supplied name with explicit Yes/No actions, default focus No. Approved
credentials are encrypted with RSA-OAEP SHA256/MGF1 SHA256 for that phone.
The Android Keystore protects the persisted token and certificate identity.

The initial bootstrap is trust on first use. A self-reported phone name and
Yes/No approval alone do not provide independent protection against an active
attacker during first pairing. Subsequent discovery requires both the saved hub
UUID and certificate pin; it never silently accepts a replaced certificate.
Mutations with an uncertain result are never replayed after address recovery.
No internet discovery, account, port forwarding or public listener is added.

Pair requests expire after two minutes and are bounded/rate limited. Local
approval, enable/disable and device revocation routes are absent from the LAN
gateway allowlist. Existing CLI pairing remains an administrative compatibility
path; the app exposes no manual IP, certificate or pairing-code fields.

Search, approval and navigation transitions explain the current phase. Reduced
motion follows Android system animation settings and browser preferences.
Automated fixtures prove contracts/layout; real discovery/pairing and address
recovery require separate device observations and do not certify full hardware
acceptance or a real DHCP lease change.
