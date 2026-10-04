# Dependency and license inventory

Reviewed 2026-10-03. DEL-01 and DEL-02 remain **OPEN**. This inventory records what is present and what still needs review; metadata and retained notices do not establish complete redistribution compliance.

The inspected, unflashed image has source `20f19b907359da5aede58b933888c0eb7a5f5be6`, runtime `4ce1a5fe6390`, and raw SHA256 `dcc40256ff08ee195bc39616a3829d7773c1402bfb0409ee680f973f347790eb`. Installed runtime `934d0d338e66` is a separate artifact; the existing image comparison identifies three font/license text files differing only in line endings. This inventory does not certify a subsequent runtime or image.

The [machine-readable evidence](evidence/dependency-inventory-2026-10-03.json) contains versions, metadata/notice paths and SHA256 hashes, all 569 installed OS package records, source-package fields and the concrete gaps. Inspection used read-only ext4 access to the independently verified raw image, the image's package inventory and local dependency manifests. No device or account data was read. Paths under `/opt/pysh` and `/usr/share` below refer to files in that image.

## Application runtime

The Python virtual environment contains all 14 distributions pinned in `requirements.lock`, with matching versions, plus its retained pip installer. Each inspected `.dist-info` directory contains at least one license/notice file; full paths and hashes are in the evidence. Reported license identifiers below come from bundled metadata, with license classifiers used where an expression is absent. They are not an exhaustive audit of vendored code.

| Distribution | Version | Reported license |
|---|---|---|
| annotated-doc | 0.0.5 | MIT |
| annotated-types | 0.8.0 | MIT |
| anyio | 4.15.1 | MIT |
| click | 8.5.0 | BSD-3-Clause |
| dbus-next | 0.2.3 | MIT |
| fastapi | 0.141.1 | MIT |
| h11 | 0.16.0 | MIT |
| idna | 3.20 | BSD-3-Clause |
| pydantic | 2.13.5 | MIT |
| pydantic_core | 2.46.5 | MIT |
| starlette | 1.7.0 | BSD-3-Clause |
| typing_extensions | 4.16.0 | PSF-2.0 |
| typing-inspection | 0.4.4 | MIT |
| uvicorn | 0.54.0 | BSD-3-Clause |
| pip, installer retained in venv | 25.1.1 | MIT; includes separate vendored notices |

The browser bundle includes React `19.3.0`, react-dom `19.3.0` and scheduler `0.28.0`, whose installed packages report MIT. Exact bundled upstream notice copies are retained for review in [React](licenses/react-19.3.0-LICENSE.txt), [react-dom](licenses/react-dom-19.3.0-LICENSE.txt) and [scheduler](licenses/scheduler-0.28.0-LICENSE.txt). Each has SHA256 `da6d3703ed11cbe42bd212c725957c98da23cbff1998c05fa4b3d976d1a58e93`.

**Distribution gap in the earlier inspected image:** its `dist/assets/index-BxLI0OhW.js` contains no copyright fragment, `LICENSE` reference or full MIT permission text. That39-file image/runtime has no separate React/react-dom/scheduler notice. Successor package `4a133daa7278` includes `dist/THIRD_PARTY_NOTICES.txt`, copied by Vite from `app/ui/public/THIRD_PARTY_NOTICES.txt`. Independent archive verification checks all40 manifest hashes, the three full upstream notice texts and that all39 earlier runtime files remain byte-identical. It is now installed and checked by the public update tool; the notice asset is also independently verified inside imagec8ac9c709acb/source3ca7e4e, which is not yet written or booted. [Native update and successor-image evidence](evidence/appliance-update-and-sd-image-2026-10-03.md). This closes that concrete notice-asset omission on these artifacts, not the broader DEL-01/DEL-02 licensing and delivery gates. Copies in repository documentation alone do not repair an older distributed runtime.

The image retains 11 font files and the three upstream SIL Open Font License 1.1 texts at `dist/fonts/dmmono-LICENSE.txt`, `dmsans-LICENSE.txt` and `manrope-LICENSE.txt`. Their inspected hashes are in the evidence. Font family/weight mapping is in `dist/fonts/fonts.css`; do not discard the notices when repackaging assets.

## Operating system

The package inventory has **569 installed packages**, distinct from Python's application virtual environment. Read-only inspection verified a nonempty `/usr/share/doc/<package>/copyright` for every record, resolving 23 package/document symlink paths. `/usr/share/common-licenses` also retains the common license texts listed in the evidence. A symlink is not a missing notice. Debian copyright `License:` labels are recorded when present; older or non-machine-readable copyright formats may have no extracted labels.

Representative packages actually present:

| Component | Package version |
|---|---|
| Chromium / chromium-common | 1:154.0.8037.92-1~deb13u1+rpt1 |
| Linux rpi-v8 image | 1:6.18.50-1+rpt1 |
| labwc | 0.20.2-1~bpo13+1 |
| greetd | 0.10.3-4 |
| wvkbd | 0.15-1 |
| mpv | 0.40.0-3+deb13u1 |
| PipeWire family | 1.4.2-1+rpt3 |
| WirePlumber | 0.5.8-2 |
| BlueZ | 5.82-1.1+rpt2 |
| NetworkManager | 1.52.1-1+rpt4 |
| raspi-firmware | 1:1.20260915-1 |
| firmware-brcm80211 | 1:20260519-1~bpo13+1+rpt1 |
| bluez-firmware | 1.2-13+rpt2 |

These packages can contain multiple licenses, embedded third-party libraries and separate firmware conditions. Their copyright files are the primary local review material; the table does not assign a single license to each complex package. Package source names in the evidence are provenance inputs, not proof that corresponding source or an adequate source offer accompanies a redistribution.

Widevine is not an application dependency in `requirements.lock` or `pnpm-lock.yaml` and no Widevine Debian package appears in this image package inventory. Chromium's official component updater obtains the CDM for a service profile at first use. Installed-profile readiness tests are separate evidence and do not establish permission to redistribute that downloaded component; the release must not silently copy private service profiles or CDM caches into an image.

## Build and test tools

Node, pnpm, TypeScript, Vite and Playwright run in development/CI; they are not installed as a PySH runtime on the Pi. `package.json` pins direct development dependencies: `@playwright/test 1.63.0`, `@types/node 24.19.0`, `@types/react 19.3.0`, `@types/react-dom 19.3.0`, `@vitejs/plugin-react 6.1.1`, `typescript 7.0.2` and `vite 8.3.1`. `pnpm-lock.yaml` also records their transitive resolution. Python build/test tools are pinned separately in `requirements-dev.lock`.

This review inventories the direct JavaScript development dependencies, but does not claim a completed license review of every transitive build/test tool, downloaded test browser, image-builder tool or vendored subcomponent. Any tool redistributed in a delivery bundle needs its own notice/source review; runtime dependency closure and toolchain closure are different scopes.

## Required delivery work

1. Include the three browser runtime MIT notices in the actual release and verify their hashes after packaging, image creation and installation.
2. Establish the permissions/license for original PySH code. The repository currently has no project `LICENSE`; this inventory does not choose one on the author's behalf or imply that third-party MIT licenses cover PySH itself.
3. Review component-specific corresponding-source/source-offer requirements for OS packages, firmware distribution conditions, codec-related conditions and downloaded CDM terms for the intended delivery. Preserve the actual notices. A package name, license classifier or retained copyright file alone cannot close this review.
4. Finish the build-tool inventory if those tools are part of the distributed artifact, and account for vendored components where package-level metadata is insufficient. The JSON is an evidence inventory, not a complete SPDX/CycloneDX SBOM or legal assurance.
5. Regenerate and verify this inventory for the final candidate. DEL-01 additionally needs the clean-install and update/rollback procedure repeated; DEL-02 needs the final release manifest, limitations, backup/restore evidence and package review. This document supplies only part of those gates.
