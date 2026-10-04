# Compact Arrange and exact edge placement

Requirement: arrange collapsed cards; allow placement at the rightmost canvas edge; keep the saved edge after Done, expansion, automatic collapse and reload. Expansion should use free space inward. Covered cards remain selectable and intentional overlap is allowed.

The usability auditor executed 48 real-time Playwright cases at 800×480: weather, forecast, playback and visualizer × three visualizer sizes × EN/RO × Ink/Night. All passed. Right/bottom offsets at the selected canvas boundary are within2px, saved right/bottom anchors remain unchanged, and grown cards stay inside the canvas. Playback deliberately collapses into the signal; tapping the signal restores the card at its saved edge, and Arrange re-entry shows its compact footprint.

The visual auditor inspected seven representative captures; the root inspected the Romanian night weather capture. No new clipping was identified in the moved cards. These are browser fixtures and do not certify a physical finger gesture or complete application usability.

An earlier test accelerated the JavaScript clock during CSS transitions and reported a10px bottom mismatch. Eight real-time cases, followed by the full48case matrix, passed on unchanged source. The automated-clock result was not reproduced in ordinary timing, so no speculative source change was made.

Home.tsx, HomeLayout.tsx and ambient-home.css are unchanged from installed source `060d57be00472fa7c1c81b77ad87ab7473e01e44` through the later installed source `204ff1b2117fcf4b07394ad660912edbf5e7acd6`, runtime `6676b558fe06`. Independent native checks verified all48runtime hashes and confirmed nine saved preferences match the pre-update backup, including homePositions. That proves source identity and preference preservation, not new native editor interactions. Physical touch and final product acceptance remain OPEN.
