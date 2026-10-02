# Pi Smart Hub integrations: feasibility notes

Scope: Raspberry Pi 4 (4 GB), Debian 13 arm64, 800×480 touchscreen. Research only; no packages or system settings changed.

## Recommended shape

Use a local touchscreen web UI in a Chromium kiosk, backed by a small local service. Keep UI and device-control boundaries explicit: the web UI calls a local API; the service owns privileged system-bus interactions. Prefer Python with `dbus-next` or GLib/libnm bindings for the service. A static frontend plus a small API avoids a desktop shell dependency and fits a 4 GB Pi. Run it in the active logged-in user session so PipeWire/WirePlumber and touchscreen input are available.

For external streaming services, open the service's own website in the kiosk browser (or a managed browser window/tab) so login, cookies, EME/DRM, and service UI remain first-party. Do not proxy, repackage, embed, or claim playback success based only on a launch action. For local music and radio streams, use `mpv` (or VLC) as a player process and expose transport/status through IPC; it is a reliable boundary for local files and stream URLs. Radio station availability and codecs still depend on the chosen station URLs.

## Device integrations

- **Wi-Fi and Ethernet:** use NetworkManager as the sole network manager. Its system D-Bus API supports device/status inspection, Wi-Fi access point scans, saved profiles, and activation/deactivation; Ethernet is managed as a wired device. `nmcli` is a good diagnostic and fallback CLI, but the app should use D-Bus/libnm for structured state and avoid shelling out with credentials. If NetworkManager is not already managing the interfaces on the target image, make that a setup prerequisite and avoid running competing network managers.
- **Bluetooth discovery and pairing:** use BlueZ D-Bus (`Adapter1.StartDiscovery`, `Device1.Pair`, `Device1.Connect`, and `Device1.Disconnect`) and subscribe to object/property changes for the UI. A pairing wizard needs an Agent1/AgentManager1 agent to handle passkey display/input/confirmation and authorization. On this touch-only 800×480 display, present numeric comparison and passkey-entry flows clearly; do not silently auto-accept confirmations. Pairing is separate from routing audio.
- **Bluetooth audio:** use Debian's PipeWire + WirePlumber + BlueZ stack, including the Bluetooth SPA plugin. WirePlumber's BlueZ monitor creates audio device/node objects for connected Bluetooth audio devices. Enumerate the resulting PipeWire sinks in the UI and set the selected sink as default (e.g. through WirePlumber/wpctl or PulseAudio-compatible PipeWire control). Configure and test the intended profile (usually A2DP for output to a Bluetooth speaker/headphones). If the requirement also means receiving a phone's audio into the Pi, explicitly test the A2DP *sink* role; it is a distinct direction from sending Pi audio to a paired speaker.
- **Local media and radio:** `mpv` is available in Debian 13 arm64. Use it for local audio and direct radio stream URLs, with its IPC socket for play/pause/seek/status. Keep local media browsing constrained to configured removable/local media roots.
- **Service launcher:** YouTube, Netflix, and other music services should be represented as browser launchers to their own origins. Test playback on the exact target image and display resolution, with a real account and real stream; launcher success and page load are not playback success.

## Hard gate: Netflix / protected playback

Netflix's current help page lists Linux as potentially supported, but explicitly says Linux configurations are not guaranteed and Linux devices are outside customer support. Its Linux table gives browser versions/resolution ceilings, but does not certify Raspberry Pi, Debian arm64, Chromium, hardware decode, or any particular Widevine/CDM build. Google now documents Chrome for 64-bit ARM Linux and offers an arm64 Linux package; this removes the older browser-availability blocker but does not certify Netflix DRM on this Pi. Google's Widevine docs list Linux Chrome and Chromium as supported browser families while also stating that a Widevine product license is required and device integration/provisioning is platform-specific. Therefore Netflix is **unverified until real protected content plays on this exact image and output path**. Do not ship a fake “DRM ready” state or bundle a CDM from unofficial sources. If the test fails, label Netflix unavailable on this build and offer its website only as best-effort, or pick a vendor-supported streaming device.

The 800×480 panel can show a browser page, but many service pages are designed for larger screens and may have tiny controls. For services, a responsive shell around a first-party browser page is safer than trying to clone the service UI; validate touch navigation and text scaling on the panel.

## Minimum runtime packages to validate on Debian 13 arm64

- UI: Chromium kiosk package available for the chosen Debian/Raspberry Pi image, plus the image's graphics stack and touch input support.
- Network: `network-manager` (and its Wi-Fi supplicant/firmware dependencies if not already present); optional `gir1.2-nm-1.0` for libnm via Python GI.
- Bluetooth: `bluez`, plus Python D-Bus bindings/library for the local service.
- Audio: `pipewire-audio`, `wireplumber`, `libspa-0.2-bluetooth`, and `pipewire-pulse` if a PulseAudio-compatible application API is useful.
- Playback: `mpv`.
- App service: Python 3 and a small HTTP/API framework only if useful; avoid a full desktop environment or heavyweight database unless product scope requires it.

Exact package names and service defaults vary by the Debian-derived image; confirm on the target before provisioning. Debian 13 uses WirePlumber 0.5's JSON configuration system, so do not copy older WirePlumber 0.4 Lua snippets.

## Primary sources

- Raspberry Pi 4 hardware brief: https://pip-assets.raspberrypi.com/categories/545-raspberry-pi-4-model-b/documents/RP-008344-DS-5-raspberry-pi-4-product-brief.pdf
- BlueZ Adapter1 discovery API: https://github.com/bluez/bluez/blob/master/doc/org.bluez.Adapter.rst
- BlueZ Device1 pairing/connection API: https://github.com/bluez/bluez/blob/master/doc/org.bluez.Device.rst
- BlueZ agent and authentication overview in bluetoothctl docs: https://github.com/bluez/bluez/blob/master/doc/bluetoothctl.rst
- NetworkManager D-Bus/API overview: https://www.networkmanager.dev/docs/developers/
- NetworkManager D-Bus specification: https://www.networkmanager.dev/docs/api/latest/spec.html
- NetworkManager connection profiles: https://www.networkmanager.dev/docs/api/latest/nm-settings-dbus.html
- WirePlumber Bluetooth configuration and roles: https://pipewire.pages.freedesktop.org/wireplumber/daemon/configuration/bluetooth.html
- WirePlumber node priority/default routing: https://pipewire.pages.freedesktop.org/wireplumber/daemon/configuration/priorities.html
- Debian 13 PipeWire notes, including WirePlumber 0.5 migration: https://wiki.debian.org/PipeWire
- Debian 13 arm64 package pages: https://packages.debian.org/trixie/arm64/pipewire ; https://packages.debian.org/trixie/arm64/libspa-0.2-bluetooth ; https://packages.debian.org/trixie/arm64/wireplumber ; https://packages.debian.org/trixie/arm64/mpv
- Google Chrome Linux requirements and arm64 package path: https://support.google.com/chrome/answer/95346
- Netflix supported browsers / Linux caveat: https://help.netflix.com/en/node/30081
- Widevine overview, supported browser families and license/platform integration note: https://developers.google.com/widevine/drm/overview
- Chromium FAQ notes that Chromium does not bundle all Chrome proprietary components, including Widevine CDM in ChromiumOS: https://www.chromium.org/chromium-os/chromium-os-faq/
