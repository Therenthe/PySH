"""Provenance boundaries, exact identities, and honest missing-evidence handling."""
import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

import pytest

spec = importlib.util.spec_from_file_location("image_provenance", Path(__file__).resolve().parents[1] / "os/image/collect-provenance.py")
provenance = importlib.util.module_from_spec(spec)
spec.loader.exec_module(provenance)


class Reader:
    def __init__(self, files):
        self.files = files

    def read(self, path):
        if path not in self.files:
            raise FileNotFoundError(path)
        return self.files[path]

    def resolve(self, path):
        return path

    def list(self, path):
        prefix = path + "/"
        return sorted({name[len(prefix):].split("/")[0] for name in self.files if name.startswith(prefix)})

    def is_dir(self, path):
        return bool(self.list(path))


def inputs():
    source = {"source": "a" * 40, "runtime_build": "b" * 12, "builder": "c" * 40}
    files = {
        "/etc/pysh-build.json": json.dumps(source).encode(),
        "/opt/pysh/current/requirements.lock": b"demo==1\n",
        "/var/lib/dpkg/status": b"Package: firmware-demo\nStatus: install ok installed\nVersion: 1.2-3\nArchitecture: arm64\nSource: source-demo (1.2)\n",
        "/var/lib/dpkg/info/firmware-demo.list": b"/usr/lib/firmware-demo/kernel8.img\n",
        "/usr/lib/firmware-demo/kernel8.img": b"actual kernel bytes",
        "/usr/share/doc/firmware-demo/copyright": b"Upstream retained copyright\n",
        "/opt/pysh/venv/lib/python3.13/site-packages/demo-1.dist-info/METADATA": b"Name: demo\nVersion: 1\n",
        "/opt/pysh/venv/lib/python3.13/site-packages/demo-1.dist-info/licenses/vendor/NOTICE": b"nested vendor notice",
        "/var/lib/apt/lists/repository_InRelease": b"-----BEGIN PGP SIGNED MESSAGE-----\nHash: SHA256\n\nOrigin: Vendor\nSuite: trixie\n",
    }
    manifest = {"build": source["runtime_build"], "files": {"requirements.lock": provenance.digest(files["/opt/pysh/current/requirements.lock"])}}
    return Reader(files), manifest, source, {"kernel8.img": b"actual kernel bytes"}


def test_exact_inventory_relocated_firmware_and_nested_notice():
    result = provenance.collect(*inputs())
    assert result["runtime_verified_files"] == 1
    package = result["os_packages"][0]
    assert (package["source"], package["source_version"]) == ("source-demo", "1.2")
    assert package["copyright"]["sha256"] == provenance.digest(b"Upstream retained copyright\n")
    assert result["python_distributions"][0]["notice_files"][0]["sha256"] == provenance.digest(b"nested vendor notice")
    assert result["boot_files"][0]["owning_packages"] == ["firmware-demo"]
    release = result["cached_apt_metadata"][0]
    assert release["observed_release_fields"]["Origin"] == "Vendor"
    assert release["signature_verification"] == "NOT_PERFORMED_BY_COLLECTOR"
    assert any(gap["kind"] == "installed_package_checksum_unavailable" for gap in result["gaps"])
    assert result["acceptance"] == "EXPERIMENTAL, NOT FLASH-READY"


def test_mismatched_runtime_and_required_inputs_abort():
    reader, manifest, source, boot = inputs()
    reader.files["/opt/pysh/current/requirements.lock"] = b"changed"
    with pytest.raises(ValueError, match="Runtime hash mismatch"):
        provenance.collect(reader, manifest, source, boot)
    reader, manifest, source, boot = inputs()
    source["runtime_build"] = "d" * 12
    with pytest.raises(ValueError, match="identity mismatch"):
        provenance.collect(reader, manifest, source, boot)
    reader, manifest, source, boot = inputs()
    del reader.files["/var/lib/dpkg/status"]
    with pytest.raises(FileNotFoundError):
        provenance.collect(reader, manifest, source, boot)


def test_missing_notice_and_different_relocated_bytes_are_gaps():
    reader, manifest, source, boot = inputs()
    del reader.files["/usr/share/doc/firmware-demo/copyright"]
    boot["kernel8.img"] = b"different bytes with same basename"
    result = provenance.collect(reader, manifest, source, boot)
    assert result["os_packages"][0]["copyright"] is None
    assert result["boot_files"][0]["owning_packages"] == []
    assert {gap["kind"] for gap in result["gaps"]} >= {"missing_retained_notice", "boot_file_package_mapping_unknown"}


def test_matching_cached_checksum_records_index_without_claiming_signature():
    reader, manifest, source, boot = inputs()
    paragraph = b"Package: firmware-demo\nVersion: 1.2-3\nArchitecture: arm64\nFilename: pool/f/firmware.deb\nSHA256: " + b"d" * 64 + b"\n"
    reader.files["/var/lib/apt/lists/repository_Packages"] = paragraph
    with patch.object(provenance.subprocess, "check_output", return_value=paragraph):
        result = provenance.collect(reader, manifest, source, boot)
    assert result["available_installed_package_checksums"][0]["SHA256"] == "d" * 64
    assert not any(g["kind"] == "installed_package_checksum_unavailable" for g in result["gaps"])
    assert any(g["kind"] == "apt_signature_chain_not_verified" for g in result["gaps"])


@pytest.mark.parametrize("path", ["/etc/../shadow", "relative", "/file name", "/file;command"])
def test_image_path_injection_and_root_escape_rejected(path):
    with pytest.raises(ValueError):
        provenance.safe_path(path)


@pytest.mark.parametrize("architecture,checksum", [("amd64", "d" * 64), ("arm64", "invalid")])
def test_foreign_architecture_or_invalid_checksum_cannot_close_provenance_gap(architecture, checksum):
    reader, manifest, source, boot = inputs()
    reader.files["/var/lib/apt/lists/repository_Packages"] = (
        f"Package: firmware-demo\nVersion: 1.2-3\nArchitecture: {architecture}\nSHA256: {checksum}\n"
    ).encode()
    result = provenance.collect(reader, manifest, source, boot)
    assert any(g["kind"] == "installed_package_checksum_unavailable" for g in result["gaps"])


def test_symlink_escape_and_cycles_fail_without_host_reads():
    reader = provenance.Ext4Reader(Path("root.ext4"))
    reader.command = lambda command: 'Type: symlink\nFast link dest: "../../outside"'
    with pytest.raises(ValueError, match="escapes"):
        reader.resolve("/link")
    reader = provenance.Ext4Reader(Path("root.ext4"))
    reader.command = lambda command: 'Type: symlink\nFast link dest: "/loop"'
    with pytest.raises(ValueError, match="depth"):
        reader.resolve("/loop")
