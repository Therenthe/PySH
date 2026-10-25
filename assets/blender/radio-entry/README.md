# Blender radio entrance

An original 2.5-second, 60-frame, 24fps camera approach through the existing
city-v3 diorama toward the radio building at world x3.0/y0.64. The editable
source retains the original city, introduces a physically modeled Art Deco
entrance, and keys a perspective camera, hinged double doors, two road vehicles,
a four-car metro passage and two walking coat silhouettes. This is a rendered
3D scene with parallax and object animation, rather than a transformed city PNG.

The building's exact original source is protected by SHA-256 during the build.
The source city and all existing runtime assets are never overwritten. Small
review keys, contract, mesh and motion reports live here. Full native frames,
encoding probes and logs remain in ignored `.runtime/radio-entry-authoring`.

The two runtime WebM assets use VP8 with alpha, 800×480, no audio. They contain
architecture and street life only; their transparent sky preserves the actual
weather and celestial scene below. They contain no service-status beacons or
invented audio activity. The threshold becomes dark and opaque for the Radio
page handoff. The camera takes a small rightward arc to clear the existing
planter without deleting city architecture or foliage.

The day clip is 618,278 bytes and the night clip 613,531 bytes, both below the
2MiB per-theme target. Both decode completely through libvpx as 60 frames at
24fps and 2.5 seconds. The decoded first-frame sky has alpha 0, foreground alpha
255, and the sampled final-frame viewport is fully opaque. Exact hashes and
the bounded offline verification are in the build and alpha reports.

The first frame approximates the Home lower-city composition with a perspective
camera; it does not pretend to match the earlier orthographic raster pixel for
pixel. UI entry blending, reduced-motion bypass, timeout/error recovery,
repeat-activation ownership, cancellation and real device decode performance
are integration responsibilities. The actual sun state selects the clip; a
manual dark UI is not evidence of nighttime weather.

Run the builder in Blender 5.2.2 LTS, headless with factory startup and
`--python-exit-code 1`, then pass `--root REPO`. Use `--preview-only` to inspect
the authored key poses before rendering the complete sequence. A complete build
also takes `--ffmpeg PATH` to an existing full FFmpeg build with PNG/image2 input
and libvpx VP8 alpha support. No encoder download or installation is required.
The slim Playwright capture encoder cannot decode PNG frames; it is unsuitable
for this input despite advertising libvpx. The accepted full encoder requires
both `-auto-alt-ref 0` and `-lag-in-frames 0` for alpha encoding.

The new closed props pass the Blender expert render-profile gate individually;
the preexisting city retains its own documented architectural gate. The motion
report records camera samples, actual moving rigs, beats and frame timing.
These authoring checks do not certify playback, alpha compositing, GPU/CPU
performance or physical device acceptance.
