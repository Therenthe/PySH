# Weather-alert content negotiation repair

## Observed defect and external contract

The official [Meteoalarm feed directory](https://feeds.meteoalarm.org/) still lists
the [Romania Atom feed](https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-romania).
The provider's [subscription page](https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-romania/subscribe)
identifies Atom as the maintained replacement for retired RSS. No new service,
account, relay or API key is needed for this existing integration.

Live requests on24 October2026 reproduced a concrete transport defect: the exact
adapter's `Accept: application/atom+xml,application/cap+xml` received HTTP406.
Each explicit XML media type tested separately also received406. On the same
verified HTTPS URL, with the same application User-Agent, `Accept: */*` received
HTTP200 and the correct `application/atom+xml` document. The existing adapter
converted406 into the honest but persistent unavailable state seen by the user.

## Minimal repair

Only the request's Accept header changes. Trusted HTTPS host/path checks,
redirect refusal, timeout,2MB response bound, XML/namespace checks, prohibited
entities, local area matching, active dates, updates/cancellations, language
selection, cache and stale/unavailable semantics remain unchanged. Accepting
the transport response does not accept arbitrary HTML or mark failed data as
an empty warning list. No location coordinates are transmitted to this feed.

The API contract stays unchanged:

- `available` with an empty alert list means a verified current country-feed
  snapshot has no applicable warning. It is not a guarantee that no hazard exists.
- `available` with alerts retains the matched official records; `partial` can
  indicate incomplete verification of other entries.
- `stale` retains eligible cached records after failed refresh or an old feed;
  stale data must not be presented as current.
- `unavailable` covers failed/unverifiable data without a usable current snapshot.
  Missing or unsupported coverage must never be displayed as verified clear.

## Verification and limits

73/73 targeted backend cases pass in `test_weather_alerts.py` and
`test_alert_integration.py`. Two added cases exercise the actual `_fetch`
boundary under the provider's observed406 negotiation rule: verified empty
Atom feed and linked CAP warning. Two additional parser cases reject HTML and
wrong-namespace XML as unavailable rather than clear. Existing
coverage includes expiry, future timestamps, malformed geometry, canceled or
updated warnings, stale/offline data, source restrictions and location races.

A real PC-venv snapshot after the repair at11:38:29UTC on24 October2026 returned
`available`, no error, and zero alerts from a feed updated at11:35:25UTC. The
unchanged adapter had returned unavailable immediately before the repair.
This is live provider/backend evidence for that instant, not proof of an active
Romanian severe-weather event or a native UI/device test. Linked active CAP
handling is exercised with isolated fixtures; the real Romanian feed was empty.
Raw response, headers and probe receipts remain private under `.runtime/`.

The serial device owner independently reproduced the same failure on the
installed Pi runtime `eaa8c82585e4` at11:40:28UTC: the old XML Accept header
returned406, while wildcard Accept returned200 with a genuine Atom feed updated
at11:35:25UTC and zero entries. The installed alert state was unavailable;
both application services were active, Ethernet connected and radio playing.
This confirms the transport root cause on the actual device. It does not certify
the candidate fix as installed or grant a new native UI/product acceptance.

This file records a candidate change. Final installed build, UI state and native
provider confirmation are recorded by the serial delivery owner after deployment.
Whole-product acceptance remains OPEN.

## Installed recovery

Runtime `ca9ff15300c7`, published source `aa2f5e07db7fe2debd9c3ea942632a7ebab7501e`,
was installed with a verified separate-PC backup. Actual kiosk API returned
`available`, no error, no partial result and zero applicable alerts, updated
at13:35:53UTC. The native Home capture no longer has the unavailable warning
trigger. No TLS/source/parser/location/cache guard was relaxed. An active
severe-weather event was not observed live; isolated CAP cases remain fixture
evidence. Full product acceptance stays OPEN.
