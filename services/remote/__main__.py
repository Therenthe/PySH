"""Local-only setup, pairing and revocation CLI: python -m services.remote."""
import argparse
import ipaddress
import json
import os
from pathlib import Path
import ssl
import subprocess

from .gateway import DeviceStore, LanServer, atomic_json, certificate_pin, lan_address


def main(argv=None):
    parser = argparse.ArgumentParser(description="PySH private LAN remote gateway")
    parser.add_argument("command", choices=("init", "serve", "pair", "devices", "revoke", "info"))
    parser.add_argument("--data", type=Path, default=Path.home() / ".local/share/pi-smart-hub/remote")
    parser.add_argument("--host", help="Explicit private LAN IP (required for init)")
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--device-id", help="Phone UUID to revoke")
    args = parser.parse_args(argv)
    directory = args.data.resolve()
    config_path = directory / "config.json"
    if args.command == "init":
        if not args.host or not lan_address(args.host) or not 1024 <= args.port <= 65535:
            parser.error("init requires an explicit private LAN --host and an unprivileged port")
        if config_path.exists() or (directory / "certificate.pem").exists() or (directory / "private-key.pem").exists():
            parser.error("Existing certificate/configuration retained; use a new private directory for reinitialization")
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        if os.name != "nt":
            directory.chmod(0o700)
        address = str(ipaddress.ip_address(args.host)).split("%", 1)[0]
        try:
            subprocess.run([
                "openssl", "req", "-x509", "-newkey", "rsa:3072", "-sha256", "-nodes",
                "-days", "3650", "-keyout", str(directory / "private-key.pem"),
                "-out", str(directory / "certificate.pem"), "-subj", "/CN=PySH LAN Remote",
                "-addext", "subjectAltName=IP:" + address,
                "-addext", "basicConstraints=critical,CA:FALSE",
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except (OSError, subprocess.CalledProcessError):
            parser.error("OpenSSL certificate generation failed; install the OS openssl package and retry in a fresh directory")
        if os.name != "nt":
            (directory / "private-key.pem").chmod(0o600)
            (directory / "certificate.pem").chmod(0o600)
        atomic_json(config_path, {"host": args.host, "port": args.port})
        atomic_json(directory / "devices.json", {"devices": []})
    if not config_path.exists():
        parser.error("Initialize the gateway first with init --host <private-IP>")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    store = DeviceStore(directory)
    if args.command in {"init", "info", "pair"}:
        host = config["host"]
        endpoint = f"https://[{host}]:{config['port']}" if ":" in host else f"https://{host}:{config['port']}"
        print("Endpoint: " + endpoint)
        print("Certificate SHA256: " + certificate_pin(directory / "certificate.pem"))
    if args.command == "pair":
        print("Pairing code (5 minutes, one phone): " + store.begin_pairing())
        print("Verify the certificate fingerprint shown here in the Android app before pairing.")
    elif args.command == "devices":
        print(json.dumps([{key: item[key] for key in ("deviceId", "name")} for item in store.read()["devices"]], ensure_ascii=False, indent=2))
    elif args.command == "revoke":
        if not args.device_id:
            parser.error("revoke requires --device-id <UUID>")
        print("Revoked" if store.revoke(args.device_id) else "Device not found")
    elif args.command == "serve":
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.load_cert_chain(directory / "certificate.pem", directory / "private-key.pem")
        server = LanServer(config["host"], config["port"], context, store)
        print("PySH LAN remote gateway ready", flush=True)
        try:
            server.serve_forever(poll_interval=0.5)
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()


if __name__ == "__main__":
    main()
