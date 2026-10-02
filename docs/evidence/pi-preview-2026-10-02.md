# Raspberry Pi preview — 2026-10-02

Source: da783dda36a119a42e0091d756b158c84d25e715 (PR #1). Runtime build: 568c2b0c43de. Archive SHA-256: 6f28027f91d5278f5e9c464e3906e3eb0914fe1d8ea3bbe65c2d7871cfab87bb. All 33 extracted runtime file hashes matched the PC manifest. Documentation-only follow-ups do not change this runtime payload.

## Observed results

- Existing Pi 4 / Debian 13.4 ARM64 graphical session retained. No networking, OS, boot or autostart changes.
- Isolated preview service `pysh-preview-568c2b0c43de.service` launched successfully and reported active. Release path: `~/pi-smart-hub/releases/568c2b0c43de`; separate data: `~/.local/share/pysh-preview-568c2b0c43de`.
- Real compositor screenshot, taken with grim and inspected on PC, is 800×480 landscape. Romanian first-run language selection and Continue controls are visible. This proves this screen, not the entire UI matrix.
- API reports actual wired and Wi-Fi connections, available BlueZ and PipeWire adapters with no integration errors. Active connection was preserved.
- Existing speaker `ML-DAC-SPKBT-QC15` was already paired and connected. PipeWire exposed it as the active Bluetooth sink; API audio.ready was true. No new pairing was performed.
- A newly generated 15-second, intermittent 440 Hz WAV file was played using `/api/play` with source `local`. PipeWire volume was set to 25% through `/api/audio`. At two seconds, mpv state was `playing`, position about 1.52 s, duration 15 s, error null. mpv's own gain remained 100%; effective sink gain was 25%.
- User explicitly confirmed: "Da, s-a auzit din boxă". This is an audible local-file integration result; it does not prove radio playback, pairing, reconnect, mute or recovery.
- Generated test media retained at `~/Music/PySH-preview-568c2b0c43de/audio-test.wav`. Runtime, browser profiles and session tokens are excluded from Git.
- GitHub Actions run 37035042904 passed frontend build + four EN/RO theme browser tests and backend checks on Python 3.12 and 3.13.

- User completed the first-run wizard by touch and opened Settings / Bluetooth, confirming that buttons responded and the named speaker was visible. A second real 800x480 compositor capture shows the Romanian Bluetooth settings, connected speaker and disconnect control. This is a bounded physical touch check, not the complete UX checklist.

## Remaining acceptance

Full physical touch tour, all screens/themes/locales, radio, pairing/error/reconnect, mute/output recovery, cold boot, installation/rollback and long-running stability remain unverified. All 30 product criteria remain OPEN; these observations are partial evidence, not release acceptance. Known Home/Radio translation and clipping issues are recorded in STATUS.

## Preview lifecycle

The transient service runs only in the existing user session. Stop with `systemctl --user stop pysh-preview-568c2b0c43de.service`. Relaunch with:

```bash
systemd-run --user --unit=pysh-preview-568c2b0c43de --collect \
  --working-directory=/home/therenthe/pi-smart-hub/releases/568c2b0c43de \
  --setenv=PI_HUB_DATA=/home/therenthe/.local/share/pysh-preview-568c2b0c43de \
  --setenv=WAYLAND_DISPLAY=wayland-0 --setenv=DISPLAY=:0 \
  /home/therenthe/pi-smart-hub/.venv/bin/python \
  /home/therenthe/pi-smart-hub/releases/568c2b0c43de/scripts/run-hub.py
```

No persistent activation was performed. Legacy source/releases and preferences remain separate.
