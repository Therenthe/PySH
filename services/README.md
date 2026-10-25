# Local services

backend/ is the existing Python API and device adapters. Run from repository root using `python -m uvicorn services.backend.app:app --host 127.0.0.1 --port 8765`. No cloud or separate automation service is required by this migration.

`remote/` is the optional native Android LAN bridge requested by the owner. It binds only an explicit private IP over HTTPS, pairs phones through a local code and certificate fingerprint, and forwards a fixed route allowlist to the unchanged loopback API. Setup, revocation, systemd user unit and protocol are documented in [ANDROID_REMOTE](../docs/ANDROID_REMOTE.md) and [ADR-0010](../docs/adr/0010-android-lan-remote.md).
