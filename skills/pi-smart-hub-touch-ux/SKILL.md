---
name: pi-smart-hub-touch-ux
description: Design and review Pi Smart Hub's bilingual touchscreen experience at 800x480, including E-Ink/night themes, Bluetooth setup and media recovery states. Use for this project's UI implementation and visual acceptance.
---

# Pi Smart Hub touch UX

Read project PRODUCT and DoD first. Design for the physical 7-inch 800x480 landscape panel, not a shrunk desktop dashboard. E-Ink is a visual theme on an LCD, not an electrophoretic display.

- Use a restrained monochrome foundation with intentional color accents; night mode must cover dialogs, keyboard, sliders and errors. Avoid gratuitous glow/blur that costs rendering performance or obscures text.
- Keep the clock, weather and one contextual primary card clear. Use a small stable navigation model, not many equally prominent dashboard tiles. Home should not scroll accidentally.
- Primary touch targets at least 48x48 CSS pixels; default body text at least 16px, secondary text normally at least 14px. Text contrast at least 4.5:1 (large text 3:1), functional control boundaries/states at least 3:1. Color is never the sole status signal.
- Never require hover or a physical keyboard. Provide in-app text entry where needed. Test long Romanian labels and diacritics; keep cancel/back visible with keyboard open. No nested modal chains.
- Distinguish action pending from success. Pairing, audio routing, buffering and Wi-Fi activation are separate states. Show genuine disconnected/offline/no-speaker states and recovery, not simulated green indicators. A Pi analog audio endpoint does not prove physical speakers exist.
- Keep a reliable way home and an intentional exit-to-desktop flow, including when first-party streaming sites are open. Do not put third-party controls in fake screenshots.
- Validate screenshots at exact 800x480 in both languages and themes for all key states, then inspect on the Pi. Browser screenshots cannot prove touch feel, speaker output or DRM.
- Review with concrete defects: clipped text, overlaps, offscreen actions, unreadable contrast, ambiguous state, excessive taps, accidental activation. Fix highest-impact defects and recapture changed screens. Do not award a "premium" score based on adjectives.
- Proposed performance budgets are in the DoD and must be measured on Pi. Respect reduced motion, avoid perpetual animations, and verify the UI still responds during media playback and failed network calls.
