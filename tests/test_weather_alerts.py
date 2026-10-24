"""Official-warning parsing, local matching and failure states; no live requests."""
import asyncio
from datetime import datetime, timedelta, timezone
from html import escape
import json

import pytest

from services.backend import weather_alerts as alerts_module
from services.backend.weather_alerts import WeatherAlerts, FEED, LIMIT, _cap_url, _xml, _NoRedirect

NOW = datetime(2026, 10, 23, 16, tzinfo=timezone.utc)
CAP = "urn:oasis:names:tc:emergency:cap:1.2"
URL = "https://feeds.meteoalarm.org/api/v1/warnings/feeds-romania/12345678-1234-1234-1234-123456789abc"
LOCATION = {"name": "București · Sector 5", "latitude": 44.38808, "longitude": 26.07144}


def values(**changes):
    return {"identifier": "official-warning-1", "status": "Actual", "scope": "Public", "message_type": "Alert",
            "sent": (NOW-timedelta(hours=1)).isoformat(), "effective": (NOW-timedelta(hours=1)).isoformat(),
            "onset": (NOW-timedelta(minutes=30)).isoformat(), "expires": (NOW+timedelta(hours=1)).isoformat(),
            "severity": "Severe", "event": "Wind warning", "areaDesc": "București", **changes}


def tags(data):
    return "".join(f"<cap:{key}>{escape(str(value))}</cap:{key}>" for key,value in data.items())


def feed(*entries, updated=NOW):
    return f'<feed xmlns="http://www.w3.org/2005/Atom" xmlns:cap="{CAP}"><updated>{updated.isoformat()}</updated>{"".join(entries)}</feed>'


def entry(data=None, *, link=None, hazard="1"):
    link_xml = f'<link type="application/cap+xml" href="{escape(link)}"/>' if link else ""
    return f'<entry>{tags(data or values())}{link_xml}<cap:parameter><cap:valueName>awareness_type</cap:valueName><cap:value>{hazard}; source label</cap:value></cap:parameter></entry>'


def cap(*, shape='<cap:polygon>44,25 45,25 45,27 44,27 44,25</cap:polygon>', identifier="official-warning-1"):
    envelope = values(identifier=identifier)
    envelope["msgType"] = envelope.pop("message_type")
    return f'<cap:alert xmlns:cap="{CAP}">{tags({k:envelope[k] for k in ("identifier","status","scope","sent","msgType")})}<cap:info>{tags({k:envelope[k] for k in ("onset","expires","effective","severity","event")})}<cap:language>ro-RO</cap:language><cap:headline>Ploaie &amp; vânt</cap:headline><cap:description>&lt;b&gt;Text oficial&lt;/b&gt;</cap:description><cap:area><cap:areaDesc>București</cap:areaDesc>{shape}</cap:area></cap:info></cap:alert>'


def adapter(tmp_path, monkeypatch, source, document=None):
    alerts = WeatherAlerts(tmp_path)
    calls = []
    def fetch(url):
        calls.append(url)
        if url == FEED:
            return source
        if document is None:
            raise OSError("private transport detail")
        return document
    monkeypatch.setattr(alerts, "_fetch", fetch)
    return alerts, calls


def snapshot(alerts, location=LOCATION, now=NOW):
    return asyncio.run(alerts.snapshot(location, now=now))


@pytest.mark.parametrize("name", ["București", "București · Sector 5", "Bucharest Sector 1", "Bucarest - Sector 6"])
def test_exact_bucharest_fallback_has_real_source_no_coordinates_in_requests(tmp_path, monkeypatch, name):
    alerts,calls = adapter(tmp_path,monkeypatch,feed(entry()))
    result = snapshot(alerts,{**LOCATION,"name":name})
    assert result["state"] == "available" and result["error"] is None
    assert result["alerts"][0]["hazard"] == "wind"
    assert result["alerts"][0]["severity"] == "severe"
    assert result["alerts"][0]["url"] == FEED
    assert calls == [FEED]


@pytest.mark.parametrize("location,area", [
    ({**LOCATION,"name":"Bucureștii Noi"},"București"),
    (LOCATION,"Bucureștii Noi"), (LOCATION,"Ilfov"),
    ({"name":"Cluj-Napoca","country":"Romania","latitude":46.77,"longitude":23.59},"Cluj"),
])
def test_unknown_region_never_means_no_alerts(tmp_path,monkeypatch,location,area):
    alerts,_ = adapter(tmp_path,monkeypatch,feed(entry(values(areaDesc=area))))
    result=snapshot(alerts,location)
    assert result["state"] == "unavailable" and result["partial"] is True and result["alerts"] == []


def test_verified_local_warning_survives_unverifiable_other_area(tmp_path,monkeypatch):
    alerts,_=adapter(tmp_path,monkeypatch,feed(entry(),entry(values(identifier="other-warning",areaDesc="Unverified region"))))
    result=snapshot(alerts)
    assert result["state"] == "available" and result["partial"] is True
    assert result["error"] == "weather_alerts_unavailable"
    assert [a["id"] for a in result["alerts"]] == ["official-warning-1"]


@pytest.mark.parametrize("kind", ["Cancel","Update"])
def test_actual_public_references_supersede_predecessor_before_matching(tmp_path,monkeypatch,kind):
    reference='sender,official-warning-1,'+values()['sent']
    replacement=values(identifier='replacement',message_type=kind,references=reference)
    alerts,calls=adapter(tmp_path,monkeypatch,feed(entry(link=URL),entry(replacement)))
    result=snapshot(alerts)
    assert result['state']=='available'
    assert [a['id'] for a in result['alerts']]==([] if kind=='Cancel' else ['replacement'])
    assert calls==[FEED]


@pytest.mark.parametrize("changes", [{"status":"Test"},{"status":"Draft"},{"scope":"Unknown"},
    {"sent":(NOW+timedelta(minutes=1)).isoformat()}, {"references":"malformed"},
    {"references":"sender,official-warning-1,2025-01-01T00:00:00Z"}])
def test_untrusted_future_or_wrong_reference_cannot_cancel_local_warning(tmp_path,monkeypatch,changes):
    cancellation=values(**{'identifier':'cancellation','message_type':'Cancel','references':'sender,official-warning-1,'+values()['sent'],**changes})
    alerts,_=adapter(tmp_path,monkeypatch,feed(entry(),entry(cancellation)))
    assert [a['id'] for a in snapshot(alerts)['alerts']]==['official-warning-1']


@pytest.mark.parametrize("event,hazard", [("Tornado warning","tornado"),("Avertizare de tornadă","tornado"),("Wind warning","wind"),("Thunderstorm warning","wind")])
def test_tornado_requires_explicit_source_word_not_wind_or_thunderstorm(tmp_path,monkeypatch,event,hazard):
    alerts,_=adapter(tmp_path,monkeypatch,feed(entry(values(event=event))))
    assert snapshot(alerts)['alerts'][0]['hazard']==hazard


@pytest.mark.parametrize("shape,inside", [
    ('<cap:polygon>44,25 45,25 45,27 44,27 44,25</cap:polygon>',True),
    ('<cap:polygon>46,20 47,20 47,21 46,21 46,20</cap:polygon>',False),
    ('<cap:circle>44.38808,26.07144 1</cap:circle>',True),
    ('<cap:circle>46,20 1</cap:circle>',False),
])
def test_cap_polygon_and_circle_match_locally(tmp_path,monkeypatch,shape,inside):
    alerts,calls=adapter(tmp_path,monkeypatch,feed(entry(link=URL)),cap(shape=shape))
    result=snapshot(alerts)
    assert result["state"] == "available"
    assert bool(result["alerts"]) is inside
    if inside:
        assert result["alerts"][0]["description"] == "Text oficial"
        assert result["alerts"][0]["headline"] == "Ploaie & vânt"
    assert calls == [FEED,URL]


@pytest.mark.parametrize("shape", ['<cap:polygon>44,25 45,25 45,27</cap:polygon>',
    '<cap:circle>44,26 -1</cap:circle>', '<cap:circle>nan,26 5</cap:circle>',
    '<cap:polygon>44,25 450,25 45,27 44,25</cap:polygon>'])
def test_malformed_geometry_not_silently_replaced_by_area_alias(tmp_path,monkeypatch,shape):
    alerts,_=adapter(tmp_path,monkeypatch,feed(entry(link=URL)),cap(shape=shape))
    result=snapshot(alerts)
    assert result["state"] == "unavailable" and result["alerts"] == []


@pytest.mark.parametrize("changes", [{"status":"Test"},{"status":"Draft"},{"message_type":"Cancel"},
    {"expires":(NOW-timedelta(seconds=1)).isoformat()}, {"onset":(NOW+timedelta(minutes=1)).isoformat()},
    {"effective":(NOW+timedelta(minutes=1)).isoformat()}])
def test_noncurrent_or_nonpublic_warnings_are_not_shown(tmp_path,monkeypatch,changes):
    alerts,_=adapter(tmp_path,monkeypatch,feed(entry(values(**changes))))
    assert snapshot(alerts)["alerts"] == []


@pytest.mark.parametrize("changes", [{"scope":"Unknown"},{"severity":"Unknown"},{"expires":"garbage"},
    {"sent":(NOW+timedelta(seconds=1)).isoformat()},{"identifier":""},{"status":"Unknown"}])
def test_unverified_active_metadata_is_unavailable_not_false_clear(tmp_path,monkeypatch,changes):
    alerts,_=adapter(tmp_path,monkeypatch,feed(entry(values(**changes))))
    assert snapshot(alerts)["state"] == "unavailable"


def test_cap_mismatch_cannot_override_feed_warning(tmp_path,monkeypatch):
    alerts,_=adapter(tmp_path,monkeypatch,feed(entry(link=URL)),cap(identifier="another-warning"))
    result=snapshot(alerts)
    assert result["state"] == "unavailable" and result["alerts"] == []


def test_all_cap_infos_are_matched_before_language_preference(tmp_path,monkeypatch):
    import xml.etree.ElementTree as ET
    first=ET.fromstring(cap(shape='<cap:circle>46,20 1</cap:circle>'))
    other=ET.fromstring(cap())
    other_info=other.find(f'{{{CAP}}}info')
    other_info.find(f'{{{CAP}}}language').text='en-GB'
    first.append(other_info)
    alerts,_=adapter(tmp_path,monkeypatch,feed(entry(link=URL)),ET.tostring(first,encoding='unicode'))
    result=snapshot(alerts)
    assert result["state"] == "available" and len(result["alerts"]) == 1


def test_five_minute_cache_and_offline_expiry_are_not_current(tmp_path,monkeypatch):
    alerts,calls=adapter(tmp_path,monkeypatch,feed(entry()))
    assert snapshot(alerts)["state"] == "available"
    assert snapshot(alerts,now=NOW+timedelta(seconds=299))["state"] == "available"
    assert calls == [FEED]
    monkeypatch.setattr(alerts,"_fetch",lambda url: (_ for _ in ()).throw(OSError("private credential detail")))
    stale=snapshot(alerts,now=NOW+timedelta(minutes=6))
    assert stale["state"] == "stale" and len(stale["alerts"]) == 1
    expired=snapshot(alerts,now=NOW+timedelta(hours=2))
    assert expired["state"] == "stale" and expired["alerts"] == []
    assert "private" not in str(expired)


def test_disk_cache_is_used_only_as_stale_after_network_failure(tmp_path,monkeypatch):
    alerts,_=adapter(tmp_path,monkeypatch,feed(entry()))
    snapshot(alerts)
    restored=WeatherAlerts(tmp_path)
    monkeypatch.setattr(restored,"_fetch",lambda url: (_ for _ in ()).throw(OSError()))
    result=snapshot(restored,now=NOW+timedelta(minutes=6))
    assert result["state"] == "stale" and len(result["alerts"]) == 1


def test_empty_feed_is_available_but_old_feed_is_stale(tmp_path,monkeypatch):
    alerts,_=adapter(tmp_path,monkeypatch,feed())
    assert snapshot(alerts)["state"] == "available"
    alerts,_=adapter(tmp_path/'old',monkeypatch,feed(updated=NOW-timedelta(days=2)))
    assert snapshot(alerts)["state"] == "stale"


def test_future_feed_timestamp_rejected(tmp_path,monkeypatch):
    alerts,_=adapter(tmp_path,monkeypatch,feed(updated=NOW+timedelta(seconds=1)))
    assert snapshot(alerts)["state"] == "unavailable"


def test_native_feed_shape_expired_warnings_are_not_fetched_or_marked_partial(tmp_path,monkeypatch):
    data=values(areaDesc="Timiș",event="awareness_type=1, awareness_level=2",expires=(NOW-timedelta(days=1)).isoformat(),
                sent=(NOW-timedelta(days=2)).isoformat())
    alerts,calls=adapter(tmp_path,monkeypatch,feed(entry(data,link=URL)))
    result=snapshot(alerts)
    assert result["state"] == "available" and result["alerts"] == []
    assert calls == [FEED]


def test_native_awareness_event_uses_official_title_and_hazard(tmp_path,monkeypatch):
    xml=entry(values(event="awareness_type=10, awareness_level=2"),hazard="10").replace('<entry>','<entry><title>Yellow Rain Warning issued for Romania - București</title>')
    alerts,_=adapter(tmp_path,monkeypatch,feed(xml))
    result=snapshot(alerts)
    assert result["alerts"][0]["hazard"] == "rain"
    assert result["alerts"][0]["event"] == "Yellow Rain Warning issued for Romania - București"


def test_cap_fetch_budget_is_four_and_incomplete_matching_is_explicit(tmp_path,monkeypatch):
    entries=[entry(values(identifier=f"warning-{i}",areaDesc="Other"),link=URL.replace("123456789abc",f"123456789a{i:02d}")) for i in range(7)]
    alerts,calls=adapter(tmp_path,monkeypatch,feed(*entries))
    result=snapshot(alerts)
    assert len(calls)==5 and result["state"]=="unavailable" and result["partial"]


@pytest.mark.parametrize("url", ["http://feeds.meteoalarm.org/api/v1/warnings/feeds-romania/x",URL+"?lat=44",URL+"#x",
    URL.replace("feeds.meteoalarm.org","evil.invalid"),URL.replace("feeds.meteoalarm.org","feeds.meteoalarm.org@evil.invalid"),
    URL.replace("feeds-romania","feeds-germany"),URL.replace("feeds.meteoalarm.org","feeds.meteoalarm.org:443")])
def test_cap_allowlist_rejects_redirect_targets_queries_credentials_and_other_regions(url):
    assert not _cap_url(url)


def test_redirect_handler_never_follows_any_redirect():
    with pytest.raises(ValueError,match="redirect"):
        _NoRedirect().redirect_request(None,None,302,None,None,URL)


@pytest.mark.parametrize("raw", [b'<!DOCTYPE feed [<!ENTITY bad "x">]><feed/>',b'<!ENTITY bad SYSTEM "file:///etc/passwd"><feed/>',
    b'<feed/>'.decode().encode('utf-16'),b'x'*(LIMIT+1)], ids=["doctype","entity","utf16","oversize"])
def test_xml_rejects_entities_encodings_and_oversize(raw):
    with pytest.raises(ValueError):
        _xml(raw)


@pytest.mark.parametrize("location", [{**LOCATION,"country":"Germany"},{**LOCATION,"latitude":float("nan")},
    {**LOCATION,"latitude":True},{"name":"Bucharest"}])
def test_invalid_or_foreign_location_never_fetches(tmp_path,monkeypatch,location):
    alerts,calls=adapter(tmp_path,monkeypatch,feed())
    assert snapshot(alerts,location)["state"] == "unavailable" and calls == []


@pytest.mark.parametrize("warning", [False, True], ids=["verified-empty-country-feed", "linked-cap-warning"])
def test_meteoalarm_content_negotiation_through_real_fetch_boundary(tmp_path, monkeypatch, warning):
    """Provider's observed406 behaviour must not be hidden by mocking _fetch."""
    from urllib.error import HTTPError

    calls = []
    documents = {FEED: feed(entry(link=URL)) if warning else feed(), URL: cap()}

    class Response:
        status = 200

        def __init__(self, url):
            self.url = url

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def geturl(self):
            return self.url

        def read(self, limit):
            assert limit == LIMIT + 1
            return documents[self.url].encode("utf-8")

    class Opener:
        def open(self, request, *, timeout):
            assert timeout == 8.0
            assert request.get_header("User-agent") == "PiSmartHub/1.0"
            calls.append(request.full_url)
            if request.get_header("Accept") != "*/*":
                raise HTTPError(request.full_url, 406, "Not Acceptable", {}, None)
            return Response(request.full_url)

    monkeypatch.setattr(alerts_module, "build_opener", lambda handler: Opener())
    result = snapshot(WeatherAlerts(tmp_path))
    assert result["state"] == "available" and result["error"] is None
    assert calls == ([FEED, URL] if warning else [FEED])
    assert len(result["alerts"]) == int(warning)
    if warning:
        assert result["alerts"][0]["description"] == "Text oficial"


@pytest.mark.parametrize("document", ["<html><body>Service unavailable</body></html>", "<feed/>"])
def test_non_atom_xml_never_becomes_verified_empty_coverage(tmp_path, monkeypatch, document):
    alerts, _ = adapter(tmp_path, monkeypatch, document)
    result = snapshot(alerts)
    assert result["state"] == "unavailable" and result["error"] == "weather_alerts_unavailable"
    assert result["updated_at"] is None and result["alerts"] == []
