"""Inventory build image files without mounting them or accessing a running root.

Retained notices and APT metadata are evidence, not a redistribution approval,
signature verification, corresponding-source offer, or reproducibility claim.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def records(data):
    """Parse Debian control paragraphs, including continued fields."""
    for paragraph in re.split(r"\n\s*\n", data.decode().strip()):
        item = {}
        field = None
        for line in paragraph.splitlines():
            if line.startswith((" ", "\t")) and field:
                item[field] += "\n" + line[1:]
            elif ":" in line:
                field, value = line.split(":", 1)
                item[field] = value.strip()
        if item:
            yield item


def safe_path(path):
    value = PurePosixPath(path)
    if not value.is_absolute() or ".." in value.parts or not re.fullmatch(r"/[A-Za-z0-9_./:+@~-]+", path):
        raise ValueError("Unsafe image path")
    return path


def unpack_index(name, data):
    if name.endswith("Packages"):
        return data
    with tempfile.TemporaryDirectory(prefix="pysh-apt-index-") as folder:
        cached = Path(folder) / name
        cached.write_bytes(data)
        return subprocess.check_output(["/usr/lib/apt/apt-helper", "cat-file", str(cached)], timeout=60)


class Ext4Reader:
    """debugfs has no -w option here. All output goes to private temporary files."""
    def __init__(self, image):
        self.image = image
        self.links = {}

    def command(self, command):
        result = subprocess.run(["debugfs", "-R", command, str(self.image)],
                                check=True, capture_output=True, timeout=30)
        return result.stdout.decode(errors="replace")

    def resolve(self, path, depth=0):
        if depth > 12:
            raise ValueError("Image symlink depth exceeded")
        safe_path(path)
        parts = PurePosixPath(path).parts[1:]
        resolved = PurePosixPath("/")
        for component in parts:
            candidate = str(resolved / component)
            if candidate not in self.links:
                status = self.command("stat " + candidate)
                if "Type: symlink" in status:
                    match = re.search(r'Fast link dest: "([^"]+)"', status)
                    if not match:
                        raise ValueError("Unsupported non-fast image symlink")
                    self.links[candidate] = match[1]
                else:
                    self.links[candidate] = None
            target = self.links[candidate]
            if target:
                # Normalize relative doc/license links while preventing root escape.
                components = []
                raw = PurePosixPath(target) if target.startswith("/") else resolved / target
                for part in raw.parts[1:]:
                    if part == "..":
                        if not components:
                            raise ValueError("Symlink escapes image root")
                        components.pop()
                    elif part != ".":
                        components.append(part)
                resolved = PurePosixPath("/", *components)
                safe_path(str(resolved))
                resolved = PurePosixPath(self.resolve(str(resolved), depth + 1))
            else:
                resolved /= component
        return str(resolved)

    def read(self, path):
        path = self.resolve(path)
        if "Type: regular" not in self.command("stat " + path):
            raise FileNotFoundError("Required regular image file unavailable: " + path)
        with tempfile.TemporaryDirectory(prefix="pysh-image-read-") as folder:
            output = Path(folder) / "data"
            self.command(f"dump {path} {output}")
            if not output.is_file():
                raise FileNotFoundError(path)
            return output.read_bytes()

    def list(self, path):
        rows = self.command("ls -p " + safe_path(path)).splitlines()
        return [row.split("/")[5] for row in rows
                if row.startswith("/") and len(row.split("/")) >= 7 and row.split("/")[5] not in (".", "..")]

    def is_dir(self, path):
        return "Type: directory" in self.command("stat " + self.resolve(path))


def collect(reader, manifest, source, boot_files):
    if not re.fullmatch(r"[a-f0-9]{40}", source.get("source", "")) or not re.fullmatch(r"[a-f0-9]{40}", source.get("builder", "")):
        raise ValueError("Required committed source/builder identity missing")
    if not re.fullmatch(r"[a-f0-9]{12}", manifest.get("build", "")):
        raise ValueError("Required runtime build identity missing")
    if not manifest.get("files") or manifest.get("build") != source.get("runtime_build"):
        raise ValueError("Required source/runtime manifest identity mismatch")
    if json.loads(reader.read("/etc/pysh-build.json")) != source:
        raise ValueError("Image source differs from build input")
    for name, expected in manifest["files"].items():
        safe_path("/opt/pysh/current/" + name)
        if not re.fullmatch(r"[a-f0-9]{64}", expected):
            raise ValueError("Invalid runtime SHA256")
        if digest(reader.read("/opt/pysh/current/" + name)) != expected:
            raise ValueError("Runtime hash mismatch: " + name)
    packages = [item for item in records(reader.read("/var/lib/dpkg/status"))
                if item.get("Status") == "install ok installed"]
    if not packages:
        raise ValueError("Required installed OS inventory is empty")
    gaps = []
    ownership = {}
    for name in reader.list("/var/lib/dpkg/info"):
        if name.endswith(".list"):
            for filename in reader.read("/var/lib/dpkg/info/" + name).decode().splitlines():
                ownership.setdefault(filename, []).append(name[:-5])

    def notice(path, owner):
        try:
            data = reader.read(path)
            if not data:
                raise ValueError("Empty retained notice")
            return {"path": path, "resolved_path": reader.resolve(path), "bytes": len(data), "sha256": digest(data)}
        except (FileNotFoundError, ValueError) as error:
            gaps.append({"kind": "missing_retained_notice", "component": owner, "path": path, "reason": type(error).__name__})
            return None

    os_inventory = []
    for item in packages:
        name = item["Package"]
        source_field = item.get("Source", name)
        match = re.fullmatch(r"([^ ()]+)(?: \(([^)]+)\))?", source_field)
        if not match:
            raise ValueError("Malformed package Source")
        os_inventory.append({"name": name, "version": item["Version"], "architecture": item["Architecture"],
                             "source": match[1], "source_version": match[2] or item["Version"],
                             "copyright": notice("/usr/share/doc/" + name + "/copyright", name)})
    python_inventory = []
    for lib in reader.list("/opt/pysh/venv/lib"):
        if not re.fullmatch(r"python3\.\d+", lib):
            continue
        site = "/opt/pysh/venv/lib/" + lib + "/site-packages"
        for folder in reader.list(site):
            if not folder.endswith(".dist-info"):
                continue
            base = site + "/" + folder
            metadata = next(records(reader.read(base + "/METADATA")))
            names = reader.list(base)
            notices = []
            for filename in names:
                if re.match(r"(?i)^(license|copying|notice)(?:[._-].*)?$", filename):
                    notices.append(notice(base + "/" + filename, metadata["Name"]))
            if "licenses" in names:
                def license_files(directory, depth=0):
                    if depth > 12:
                        raise ValueError("License directory depth exceeded")
                    for filename in reader.list(directory):
                        child = directory + "/" + filename
                        if reader.is_dir(child):
                            yield from license_files(child, depth + 1)
                        else:
                            yield child
                for filename in license_files(base + "/licenses"):
                    notices.append(notice(filename, metadata["Name"]))
            if not any(notices):
                gaps.append({"kind": "missing_python_notice_group", "component": metadata["Name"]})
            python_inventory.append({"name": metadata["Name"], "version": metadata["Version"],
                                     "metadata_sha256": digest(reader.read(base + "/METADATA")), "notice_files": notices})
    if not python_inventory:
        raise ValueError("Required Python runtime inventory is empty")
    apt_metadata = []
    available = []
    installed = {(p["name"], p["version"], p["architecture"]) for p in os_inventory}
    for name in reader.list("/var/lib/apt/lists"):
        if not (name.endswith("InRelease") or name.endswith("Release") or "Packages" in name):
            continue
        path = "/var/lib/apt/lists/" + name
        data = reader.read(path)
        entry = {"path": path, "bytes": len(data), "sha256": digest(data)}
        if name.endswith(("InRelease", "Release")):
            # These fields are observed cached content, not authenticated by us.
            entry["observed_release_fields"] = {key: value for paragraph in records(data) for key, value in paragraph.items()
                                                if key in ("Origin", "Label", "Suite", "Codename", "Date", "Valid-Until")}
            entry["signature_verification"] = "NOT_PERFORMED_BY_COLLECTOR"
        else:
            unpacked = unpack_index(name, data)
            entry["uncompressed_sha256"] = digest(unpacked)
            for item in records(unpacked):
                if (item.get("Package"), item.get("Version"), item.get("Architecture")) in installed:
                    available.append({key: item[key] for key in ("Package", "Version", "Architecture", "Filename", "SHA256", "Source") if key in item} | {"index": path})
        apt_metadata.append(entry)
    for package in os_inventory:
        if not any(p.get("Package") == package["name"] and p.get("Version") == package["version"]
                   and p.get("Architecture") == package["architecture"]
                   and re.fullmatch(r"[a-fA-F0-9]{64}", p.get("SHA256", "")) for p in available):
            gaps.append({"kind": "installed_package_checksum_unavailable", "component": package["name"], "version": package["version"]})
    gaps.append({"kind": "apt_signature_chain_not_verified", "reason": "Cached file hashes are not proof of authenticated origins"})
    firmware = []
    for path, data in sorted(boot_files.items()):
        owners = ownership.get("/boot/firmware/" + path, [])
        # Match relocated vendor firmware only by complete bytes, never basename alone.
        if not owners:
            for candidate, candidate_owners in ownership.items():
                if candidate.startswith("/usr/lib/") and PurePosixPath(candidate).name == PurePosixPath(path).name:
                    try:
                        if digest(reader.read(candidate)) == digest(data):
                            owners = sorted(set(owners + candidate_owners))
                    except (FileNotFoundError, ValueError):
                        pass
        firmware.append({"boot_path": path, "bytes": len(data), "sha256": digest(data), "owning_packages": owners,
                         "ownership_basis": "exact_package_path_or_identical_relocated_bytes" if owners else "UNKNOWN"})
        if not owners:
            gaps.append({"kind": "boot_file_package_mapping_unknown", "path": path})
    if not any(PurePosixPath(path).name.startswith("kernel") for path in boot_files):
        raise ValueError("Required boot kernel file missing")
    return {"schema": 1, "source": source, "runtime_manifest_canonical_json_sha256": digest(json.dumps(manifest, sort_keys=True).encode()),
            "runtime_verified_files": len(manifest["files"]), "os_packages": os_inventory,
            "python_distributions": python_inventory, "cached_apt_metadata": apt_metadata,
            "available_installed_package_checksums": available, "boot_files": firmware,
            "gaps": gaps, "acceptance": "EXPERIMENTAL, NOT FLASH-READY",
            "limitations": ["No signature/source-offer/licensing compliance or reproducibility certification",
                            "No profiles, accounts, user preferences, live root or block devices inspected"]}


def main():
    parser = argparse.ArgumentParser()
    for option in ("root-image", "boot-image", "manifest", "source", "output"):
        parser.add_argument("--" + option, required=True, type=Path)
    args = parser.parse_args()
    for path in (args.root_image, args.boot_image, args.manifest, args.source):
        if not path.is_file() or path.is_symlink():
            raise ValueError("Required regular build input missing")
    if args.root_image.name != "root.ext4" or args.boot_image.name != "boot.vfat":
        raise ValueError("Only generated image filesystem files are accepted")
    if args.output.exists():
        raise ValueError("Refuse overwrite of provenance evidence")
    names = subprocess.check_output(["mdir", "-b", "-s", "-i", str(args.boot_image), "::/"], text=True, timeout=30)
    boot = {}
    for name in names.splitlines():
        if name.endswith("/"):
            continue
        relative = name.removeprefix("::/")
        safe_path("/" + relative)
        if relative.endswith(".pub"):
            raise ValueError("Generic image contains a provisioning key")
        boot[relative] = subprocess.check_output(["mtype", "-i", str(args.boot_image), "::/" + relative], timeout=30)
    result = collect(Ext4Reader(args.root_image), json.loads(args.manifest.read_bytes()), json.loads(args.source.read_bytes()), boot)
    result["input_manifest_sha256"] = digest(args.manifest.read_bytes())
    result["source_file_sha256"] = digest(args.source.read_bytes())
    with args.output.open("x", encoding="utf-8") as output:
        json.dump(result, output, indent=2)
        output.write("\n")
    print(json.dumps({"runtime_verified_files": result["runtime_verified_files"], "os_packages": len(result["os_packages"]),
                      "python_distributions": len(result["python_distributions"]), "gaps": len(result["gaps"])}))


if __name__ == "__main__":
    main()
