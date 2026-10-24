# Selected floating city wayfinding — reproducible authoring

This source reproduces the retained research design: Barlow Semi Condensed Regular400, measured14.454px cap height, true building-centered positions, thin physical contrast rim, fine directional stems, six genuine Blender intro frames and a quiet81-sample projected float. The original city/camera, beacon artwork and original fonts are immutable inputs. No recorded weather, audio, service/account state or device data is baked into the new labels.

The font is bundled under fonts/ with its original SIL Open Font License and pinned Google/fonts git-blob/SHA provenance. Both Barlow OFL.txt and the existing Manrope manrope-LICENSE.txt are retained beside the authoring font. All packed-font filepaths are normalized to portable //fonts/<basename> immediately before saving, without changing font bytes or rendered geometry. It is an authoring input and is packed in the editable Blender source; the kiosk displays the rendered PNGs and does not need to load this TTF.

## Rebuild

Use Blender5.2.2 with Cycles/OPTIX on a suitable NVIDIA GPU (the measured research host used an RTX5060Ti). UI/device playback never runs Blender. From the repository:

    blender --factory-startup -b --threads 8 --python-exit-code 1 --python scripts/blender/build_city_wayfinding.py -- --root <repository> --out <new-output-directory> --final

The output must be a NEW explicit directory outside app/, assets/, scripts/ and .git. The builder never deletes evidence or writes over original/public source inputs. --preview is available for four static locale/palette authoring comparisons; it is not promotable final animation evidence.

Full geometry, Unicode,14–16px cap, minimum48px hit separation, protected-beacon/neon, viewport, camera/source-input and atlas-dimension checks retain the evaluated V2 logic. An optional explicit --mesh-audit <path-to-bx_audit.py> runs the same full external mesh audit as research. There is no personal default path or automatic installation. If omitted, the contract honestly records full_mesh_audit=NOT_RUN and mesh_errors=null; it does not manufacture a new mesh PASS. Retained frozen research mesh evidence is separate. Publication validation should run the explicit audit where available.

After inspecting a fresh final render and verifying hashes, copy ONLY the14 PNG filenames allowlisted in contract.json.assets to app/ui/public/ambient/. Keep raw pose renders, logs and evidence private. Save the editable source.blend and the validated contract with these authoring sources as a separate reviewed promotion step.

Generate the small UI module using:

    python scripts/blender/export_city_wayfinding_data.py --contract <new-output-directory>/contract.json --output app/ui/src/CityWayfindingData.ts

The helper requires all eight structural/render gates explicitly true, rejects preview contracts, malformed geometry and incomplete motion data, then verifies every actual allowlisted atlas beside the contract by byte count, SHA256 and PNG RGBA8 header dimensions BEFORE writing the UI module. Missing files and mismatches are errors. Full mesh NOT_RUN is not falsely converted into PASS. It requires --replace explicitly when updating an existing generated module. It copies no assets and changes no app controller.

## Projection and animation contract

crop and final_face_rect refer to the original1600×570 city, with negative Y allowed. The renderer uses a1600×1024 transparent overscan canvas and verifies unchanged X/+227Y camera projection. At800×480: x=crop.x/2, y=272+crop.y*208/570, width=crop.width/2, height=crop.height*208/570. Atlas width is frame_count×crop.width. Runtime touch targets must retain at least48×48 CSS pixels.

The300ms intro uses six actual rendered3D poses, reversing on Close. The4s float is pure world-space translation sampled from81 Blender location keys through the unchanged orthographic camera; CSS translation therefore reproduces that movement without a live3D context. It does not simulate rotating3D geometry. Reduced motion holds the final pose and disables float; animation pauses/removes when hidden or outside Explore. The app owns lifecycle, focus and accessible full names.

Editable geometry and float location keys are stored in source.blend. Finite intro pose parameters remain reproducible in design.py via the builder. Original source identity, font audit, per-asset SHA/size/dimensions, all EN/RO palettes, research ancestry and the NEW public builder/design hashes are recorded in the output contract. Re-render noise may change isolated8-bit RGB values; do not assert byte identity without checking it.

The public design differs from winning research candidate548eaea784fbe20bf8283a9e409a8bda894c1b052707243914108c42dbbbadb3 only in its bundled-font path. The public builder is derived from evaluated rendererV2 d226347af6b37f1604ee02c8759647fb09c4399e523297b54d6dc7e4cf099aaf. Path/output/audit plumbing changes create transparent new hashes; they are not a new design experiment or proof of hardware acceptance.

Git normalizes repository Python sources to LF. `authoring-provenance.json` explicitly records both the Windows render-byte hashes retained in `contract.json` and the equivalent LF repository hashes. Normalization changes only CRLF endings; it does not change the rendered design or Python parser semantics. The saved packed-font paths are kept relative with `relative_remap=False` and independently checked after reopening the Blender file.
