# Network UI regression — 2026-10-02

Corrected nested buttons in saved network rows. Each profile now has one labelled Forget network action; the surrounding row is not interactive. Open/secured network labels are translated consistently in settings and the quick dialog. Network secondary text uses 14px and saved rows retain a full touch target with room for the action.

Automated checks: 39 Python tests passed; TypeScript and Vite build passed. Four Playwright Chromium tests cover EN/RO × E-Ink/Night at exactly 800×480 with touch taps. They verify network scan results, translated security labels, profile-id forget request and state refresh, no nested buttons or browser errors, and the dialog/actions inside the viewport. API fixtures exist only in the test suite; they do not prove real network operations.

Screenshots of the settings and dialog flows are generated under test-results/ and were visually inspected. CI now installs Chromium and runs these tests; failure artifacts retain screenshots and traces. Physical touch, actual NetworkManager changes and the rest of the product acceptance matrix remain OPEN.
