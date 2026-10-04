# Ambient graphics provenance — 2026-10-04

Two original raster outputs generated with the built-in imagegen tool, copied unchanged into app/ui/public/ambient. No third-party photos or character cutouts were imported. Sky and facades are opaque RGB. The starfield and city materials are decorative illustration, not a real star catalogue, satellite image or live city. Sun/Moon positions and phase remain independently computed. The city texture is clipped to the exact existing SVG roof path.

## night-starfield-v1.png

SHA256: `f4b17c2733e4010f85b7558a85537579299226a53cf09ef8a5819bb159be726a`. Tool: `image_gen.imagegen`. Transparent background: `false`.

Final prompt:

```text
Use case: photorealistic-natural. Asset type: a premium cinematic night-sky texture for the background of a small ambient touchscreen, decorative rather than a star chart. Generate a landscape panorama with aspect ratio 3:2, ideally1536×1024. Scene: clear deep near-black navy nocturnal starfield, many varied naturally distributed pin-point stars with a few larger but still small sharp warm-white and cool-white stars; no repeated grid or pattern. Include very faint broad Milky Way dust only in the upper two thirds, restrained contrast, photorealistic long-exposure clarity without sci-fi nebula colors. The lower25 percent should be mostly quiet dark navy with few faint stars, for a separately composited city. Finished, mature film matte-painting realism, visually delicate and natural. NO Sun, Moon, planets, clouds, city, buildings, aircraft, characters, foreground, text, watermark, frames or borders. Opaque texture; no transparency.
```

## city-facades-v1.png

SHA256: `a1746d0b8ed60f2a0f9894fafb1ade0800dd0bcd185295f7646ee4bdaa6dc01a`. Tool: `image_gen.imagegen`. Transparent background: `false`.

Final prompt:

```text
Use case: photorealistic-natural. Asset type: a panoramic CITY FACADE material texture for clipping into an existing skyline silhouette. Produce a wide landscape panorama, ideally1536×512 or comparably wide. Entire canvas consists of the frontal facades of a distant night city: layered realistic graphite concrete, charcoal steel and dark glass building facades, crisp small architectural rhythms, varying building widths and floor heights. Sparse tiny warm amber and cool ivory windows indicate a few occupied floors; most windows dark. Very restrained cool moonlit edge reflections, deep shadows, premium cinematic architectural matte painting with believable texture, no exaggerated neon or glowing outlines. Straight-on distant city perspective with verticals upright and no lens tilt; no foreground ground or street. Buildings/facade materials fill EVERY pixel including top and bottom, as this will be clipped inside a separately maintained skyline path. NO sky, Moon, Sun, clouds, people, heroes, brands, signage, readable text, logos, watermark, borders or skyline-shaped transparent cutout. Opaque architectural material texture, no transparency.
```

The superhero proposal was cancelled by the owner. No superhero, signal, Batplane asset or related animation is shipped. This document records only the independent ambient background assets.
