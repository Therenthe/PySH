# Local media formats verified on PySH

Native candidate: runtime `670c8155227b`, implementation source `beab133f81aa3de7d09c4901faef64efb952c0bb`, Raspberry Pi4, Debian13 ARM64, Chromium kiosk800×480.

| File extension | Encoding verified |
|---|---|
| WAV | PCM16 |
| MP3 | MPEG audio layer3 |
| AAC | AAC in ADTS |
| M4A | AAC |
| FLAC | FLAC |
| OGG, OGA | Vorbis |
| OPUS | Opus |
| MP4, M4V, MKV, MOV | H264 video and AAC audio |
| WebM | VP9 video and Opus audio |

The approved local library recognizes these extensions. A container extension does not guarantee every codec, profile, resolution or damaged file. Eight audio encodings were selected through the actual native library in EN/RO and both themes; audio position advanced. Five video containers decoded480×270 fixtures, and a separate H264/AAC720p24 sample advanced with working controls. This is bounded format evidence, not certification of all media or a sustained performance benchmark.

Pause, seek, resume, previous/next audio queue, stop, natural audio EOF/replay and recovery from corrupt/missing files were exercised. Selected-file errors identify the filename; an unknown queue target uses a generic message and Retry repeats the queue command. Returning to the library and selecting a valid file remains available after errors.

These native probes were muted and controlled through CDP. Physical touchscreen gestures and audible local playback remain to be accepted. Complete MEDIA-02/product acceptance remains OPEN. Private native reports and limitations are recorded in [the recovery evidence](evidence/media-missing-target-2026-10-04.md); no media files, account data or browser profiles are published.
