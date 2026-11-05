"""Real parser/config behavior and public-network trust boundaries; no live I/O."""
from datetime import datetime, timedelta, timezone
import gzip
import json
from pathlib import Path
import socket

import pytest

from services.backend import iptv_catalog as mod
from services.backend.iptv_catalog import (IPTVError, IPTVLibrary, DEFAULT_PLAYLISTS,
    DEFAULT_XMLTV, OFFICIAL_PROTV, OFFICIAL_ANTENA, FAVORITE_NAMES,
    fetch_public_resource, parse_m3u, parse_xmltv, parse_protv, parse_antena,
    public_url, verify_public_url, xmltv_time)

NOW = datetime(2026, 11, 5, 16, tzinfo=timezone.utc)
SOURCE = 'https://example.org/list.m3u'


def playlist(*names):
    return ('#EXTM3U\n' + ''.join(f'#EXTINF:-1 tvg-id="{identifier}" group-title="TV",{name}\nhttps://example.org/{index}.m3u8\n'
                                    for index, (identifier, name) in enumerate(names))).encode()


def xml(*rows, channels=None):
    channels = channels or {'PRO TV.ro': ['PRO TV']}
    return ('<tv>' + ''.join(f'<channel id="{identifier}">' + ''.join(f'<display-name>{name}</display-name>' for name in names) + '</channel>'
                            for identifier, names in channels.items()) + ''.join(rows) + '</tv>').encode()


def programme(channel='PRO TV.ro', start='20261105150000 +0000', end='20261105170000 +0000', title='News'):
    return f'<programme channel="{channel}" start="{start}" stop="{end}"><title>{title}</title><desc>Real description</desc></programme>'


def library(tmp_path, rows=None):
    sources = {source: playlist(*[(name + '.ro', name) for name in FAVORITE_NAMES]) for source in DEFAULT_PLAYLISTS}
    sources[DEFAULT_XMLTV[0]] = xml(*(rows or [programme()]))
    def fetch(source):
        if source not in sources:
            raise OSError('private detail must never escape')
        return sources[source]
    return IPTVLibrary(tmp_path, fetch=fetch), sources


def populate_guide(lib, *, channels=None):
    lib.channels = parse_m3u(playlist(('PROTV.ro@HD', 'PRO TV HD (1080p)')), SOURCE)
    lib.epg_channels, lib.programmes = parse_xmltv(xml(programme(), channels=channels), DEFAULT_XMLTV[0], NOW)
    lib.guide_updated_at = NOW.isoformat()
    lib.source_status = {DEFAULT_XMLTV[0]: {'status': 'ok'}}
    return lib.channels[0]['id']


@pytest.mark.parametrize('url', ['file:///etc/passwd', 'ftp://example.org/x', 'http://127.0.0.1/a',
    'http://192.168.1.1/a', 'http://[::1]/a', 'http://169.254.169.254/', 'http://localhost/',
    'http://thing.local/', 'https://user:secret@example.org/', 'https://example.org/#x',
    'https://example.org/\r\nx:bad', 'https://example.org\\@evil.test/', 'http://example.org:99999/'])
def test_non_public_or_unsafe_syntax_rejected(url):
    with pytest.raises(IPTVError):
        public_url(url)


def test_public_stream_ports_preserved_and_dns_checked_at_use(monkeypatch):
    url = 'http://example.org:9590/live.m3u8'
    assert public_url(url) == url
    monkeypatch.setattr(socket, 'getaddrinfo', lambda *a, **k: [(2, 1, 6, '', ('1.1.1.1', 9590))])
    assert verify_public_url(url) == url
    monkeypatch.setattr(socket, 'getaddrinfo', lambda *a, **k: [(2, 1, 6, '', ('1.1.1.1', 9590)), (2, 1, 6, '', ('10.0.0.1', 9590))])
    with pytest.raises(IPTVError, match='iptv_source_unavailable'):
        verify_public_url(url)


def test_pinned_dns_no_second_resolution_and_redirect_revalidation(monkeypatch):
    calls, pinned = [], []
    def resolve(host, port, **kwargs):
        calls.append(host)
        return [(2, 1, 6, '', ('127.0.0.1' if host == 'private.example' else '1.1.1.1', port))]
    monkeypatch.setattr(socket, 'getaddrinfo', resolve)
    monkeypatch.setattr(socket, 'create_connection', lambda address, timeout, source_address=None: pinned.append(address))
    class Response:
        status = 200
        content = b'hello'
        def getheaders(self):
            return [('Content-Type', 'text/plain')]
        def read1(self, amount):
            result, self.content = self.content[:amount], self.content[amount:]
            return result
    class Connection:
        def __init__(self, host, port, timeout):
            self.host, self.port, self.timeout = host, port, timeout
            self.sock = None
        def request(self, *a, **k):
            self._create_connection((self.host, self.port), self.timeout)
        def getresponse(self):
            return Response()
        def close(self):
            pass
    monkeypatch.setattr(mod, 'HTTPSConnection', Connection)
    raw, final, mime, headers = fetch_public_resource('https://example.org/x')
    assert (raw, final, mime) == (b'hello', 'https://example.org/x', 'text/plain')
    assert calls == ['example.org'] and pinned == [('1.1.1.1', 443)]
    Response.status = 302
    Response.getheaders = lambda self: [('Location', 'https://private.example/x')]
    with pytest.raises(IPTVError):
        fetch_public_resource('https://example.org/x')
    assert calls[-2:] == ['example.org', 'private.example']
    assert pinned[-1] == ('1.1.1.1', 443)


def test_bounded_network_body_and_header_injection(monkeypatch):
    monkeypatch.setattr(socket, 'getaddrinfo', lambda *a, **k: [(2, 1, 6, '', ('1.1.1.1', 443))])
    class Response:
        status = 200
        def getheaders(self): return [('Content-Length', '999999')]
    class Connection:
        def __init__(self, *a, **k): pass
        def request(self, *a, **k): pass
        def getresponse(self): return Response()
        def close(self): pass
    monkeypatch.setattr(mod, 'HTTPSConnection', Connection)
    with pytest.raises(IPTVError, match='too_large'):
        fetch_public_resource('https://example.org/', max_bytes=10)
    with pytest.raises(IPTVError, match='invalid_request'):
        fetch_public_resource('https://example.org/', headers={'Authorization': 'secret'})
    with pytest.raises(IPTVError, match='invalid_request'):
        fetch_public_resource('https://example.org/', headers={'Range': 'bytes=0-9\r\nx:1'})


def test_playlist_quoted_comma_relative_url_and_nonexecuted_options():
    raw = b'''\xef\xbb\xbf#EXTM3U x-tvg-url="https://unrequested.example/guide.xml"
#EXTINF:-1 tvg-id="one.ro" tvg-name="News, World" tvg-logo="file:///private" group-title="A, B",News, World
#EXTVLCOPT:http-user-agent=secret
live/one.m3u8
#EXTINF:-1,Bad
file:///private
#EXTINF:-1,Private
http://127.0.0.1/secret
'''
    channels = parse_m3u(raw, SOURCE)
    assert len(channels) == 1
    assert channels[0]['name'] == 'News, World' and channels[0]['group'] == 'A, B'
    assert channels[0]['url'] == 'https://example.org/live/one.m3u8'
    assert channels[0]['logo'] == '' and 'headers' not in channels[0]
    assert parse_m3u(raw, SOURCE)[0]['id'] == channels[0]['id']


@pytest.mark.parametrize('raw', [b'not m3u', b'#EXTM3U\n', b'#EXTM3U\n#EXTINF:-1,no\nfile:///tmp/no', b'\xff'])
def test_playlist_malformed_or_empty(raw):
    with pytest.raises(IPTVError): parse_m3u(raw, SOURCE)


def test_xmltv_offset_dst_and_gzip():
    assert xmltv_time('20261105180000 +0200') == NOW
    assert xmltv_time('20260705190000 +0300') == datetime(2026, 7, 5, 16, tzinfo=timezone.utc)
    assert xmltv_time('20261105160000') == NOW
    raw = xml(programme(start='20261105170000 +0200', end='20261105190000 +0200'))
    channels, shows = parse_xmltv(gzip.compress(raw), 'https://example.org/epg.xml.gz', NOW)
    assert channels == {'PRO TV.ro': ['PRO TV']}
    assert shows[0]['start'] == '2026-11-05T15:00:00+00:00'
    assert shows[0]['end'] == '2026-11-05T17:00:00+00:00'
    assert shows[0]['description'] == 'Real description'


@pytest.mark.parametrize('raw', [b'<!DOCTYPE tv [<!ENTITY x "oops">]><tv/>',
    b'<tv><!ENTITY x SYSTEM "file:///private"></tv>', b'<tv>\x00</tv>', b'<invalid/>',
    b'<tv><channel', b'\x1f\x8bbroken'])
def test_unsafe_and_invalid_xml(raw):
    with pytest.raises(IPTVError): parse_xmltv(raw, SOURCE, NOW)


def test_xml_bound_decompression_depth_programme_count(monkeypatch):
    monkeypatch.setattr(mod, 'MAX_XML', 200)
    with pytest.raises(IPTVError): parse_xmltv(gzip.compress(b'x' * 201), SOURCE, NOW)
    monkeypatch.setattr(mod, 'MAX_XML', 10000)
    with pytest.raises(IPTVError): parse_xmltv(b'<tv>' + b'<a>' * 13 + b'</a>' * 13 + b'</tv>', SOURCE, NOW)
    monkeypatch.setattr(mod, 'MAX_PROGRAMMES', 1)
    with pytest.raises(IPTVError): parse_xmltv(xml(programme(), programme(title='second')), SOURCE, NOW)


def test_favorites_seed_exact_variants_user_override_and_restart(tmp_path):
    lib, _ = library(tmp_path)
    result = lib.refresh_playlists()
    assert len(result['channels']) == 8  # Four duplicate source URLs merge.
    assert all(c['favorite'] for c in result['channels'])
    assert all(r['status'] == 'listed' for r in result['favorite_requests'])
    first = result['channels'][0]['id']
    lib.set_favorite(first, False)
    restored = IPTVLibrary(tmp_path, fetch=lib.fetch)
    assert not next(c for c in restored.catalogue()['channels'] if c['id'] == first)['favorite']
    result['channels'][1]['name'] = 'mutated caller copy'
    assert lib.catalogue()['channels'][1]['name'] != 'mutated caller copy'


def test_missing_requested_quality_is_not_replaced(tmp_path):
    lib = IPTVLibrary(tmp_path, fetch=lambda url: playlist(('ESPN.us@SD', 'ESPN (United States) (432p)')))
    result = lib.refresh_playlists()
    assert not result['channels'][0]['favorite']
    request = next(r for r in result['favorite_requests'] if r['name'].startswith('ESPN ('))
    assert request['status'] == 'not_in_playlists' and request['channel_id'] is None


def test_refresh_failure_retains_last_good_channels_and_redacts_error(tmp_path):
    lib, sources = library(tmp_path)
    lib.refresh_playlists()
    sources.clear()
    result = lib.refresh_playlists()
    assert len(result['channels']) == 8
    assert all(v['status'] == 'stale' and v['error'] == 'iptv_source_unavailable' for v in result['source_status'].values())
    assert 'private detail' not in json.dumps(result)


def test_config_change_during_network_refresh_cannot_publish_obsolete_result(tmp_path):
    lib, _ = library(tmp_path)
    def fetch(url):
        lib.set_sources('playlists', ['https://new.example/list.m3u'])
        return playlist(('one.ro', 'one'))
    lib.fetch = fetch
    with pytest.raises(IPTVError, match='sources_changed'): lib.refresh_playlists()
    assert lib.channels == []


def test_catalogue_reads_do_not_wait_for_network_lock(tmp_path):
    lib, _ = library(tmp_path)
    assert lib._refresh_lock.acquire(False)
    assert lib.catalogue()['channels'] == []
    with pytest.raises(IPTVError, match='refresh_busy'): lib.refresh_guide()
    lib._refresh_lock.release()


def test_guide_identifier_normalization_and_current_upcoming(tmp_path):
    lib, _ = library(tmp_path)
    channel_id = populate_guide(lib)
    guide = lib.guide(channel_id, NOW)
    assert guide['matched_by'] == 'identifier' and guide['current']['title'] == 'News'
    assert not guide['stale'] and guide['upcoming'] == []


def test_guide_name_match_unambiguous_and_country_preserved(tmp_path):
    lib, _ = library(tmp_path)
    channel_id = populate_guide(lib)
    lib.channels[0]['tvg_id'] = ''
    assert lib.guide(channel_id, NOW)['matched_by'] == 'name'
    lib.epg_channels['Another.ro'] = ['PRO TV']
    assert lib.guide(channel_id, NOW)['matched_by'] is None
    lib.channels[0]['tvg_id'] = 'PROTV.pe@SD'
    assert lib.guide(channel_id, NOW)['current'] is None


def test_official_programme_wins_overlap_without_double_shows(tmp_path):
    lib, _ = library(tmp_path)
    channel_id = populate_guide(lib)
    official = {**lib.programmes[0], 'title': 'Verified official', 'source': OFFICIAL_PROTV}
    lib.programmes.append(official)
    lib.source_status[OFFICIAL_PROTV] = {'status': 'ok'}
    result = lib.guide(channel_id, NOW)
    assert len(result['programmes']) == 1
    assert result['current']['title'] == 'Verified official'
    lib.source_status[OFFICIAL_PROTV] = {'status': 'stale', 'error': 'iptv_source_unavailable'}
    assert lib.guide(channel_id, NOW)['stale']


def test_protv_structured_json_only_and_correct_channel_selection():
    page = {'program': [{'channels': [
        {'id': 2, 'segments': [{'items': [{'title': 'Not PRO TV'}]}]},
        {'id': 1, 'segments': [{'items': [{'title': 'Official', 'start_at': '2026-11-05T17:00:00+02:00', 'end_at': '2026-11-05T19:00:00+02:00'}]}]},
    ]}]}
    channels, shows = parse_protv(('var PageData = ' + json.dumps(page) + '; evil();').encode(), NOW)
    assert channels == {'PRO TV.ro': ['PRO TV']}
    assert len(shows) == 1 and shows[0]['start'] == '2026-11-05T15:00:00+00:00'
    assert shows[0]['source'] == OFFICIAL_PROTV
    with pytest.raises(IPTVError): parse_protv(b'var PageData = evil();', NOW)


def test_antena_dated_heading_overnight_and_no_guessed_last_end():
    raw = '''<div class="sch__day"><h2>Program Antena 1 Joi, 05 Noiembrie</h2>
    <div class="sch__item"><div class="scg__text"><span>23:00</span><span class="sch__title"><a>Night show</a><a class="sch__vezi">(vezi aici)</a></span><p>Real description</p></div></div>
    <div class="sch__item"><div class="scg__text"><span>01:00</span><span class="sch__title">Next show</span></div></div></div>'''.encode()
    _, shows = parse_antena(raw, NOW)
    assert len(shows) == 1 and shows[0]['title'] == 'Night show'
    assert shows[0]['start'] == '2026-11-05T21:00:00+00:00'
    assert shows[0]['end'] == '2026-11-05T23:00:00+00:00'
    assert shows[0]['description'] == 'Real description'
    with pytest.raises(IPTVError): parse_antena(raw.replace(b'Joi', b'Marti'), NOW)
    with pytest.raises(IPTVError): parse_antena(raw.replace(b'05 Noiembrie', b'05 Ianuarie'), NOW)


def test_invalid_configuration_and_torn_cache_do_not_break_startup(tmp_path):
    folder = tmp_path / 'iptv'
    folder.mkdir()
    (folder / 'config.json').write_text('{"favorites": [], "playlists": ["file:///private"]}', encoding='utf-8')
    (folder / 'cache.json').write_text('{incomplete', encoding='utf-8')
    lib = IPTVLibrary(tmp_path)
    assert lib.catalogue()['sources']['playlists'] == list(DEFAULT_PLAYLISTS)
    assert lib.channels == []
    with pytest.raises(IPTVError): lib.set_sources('other', [SOURCE])
    with pytest.raises(IPTVError): lib.set_sources('xmltv', [])
    with pytest.raises(IPTVError): lib.set_sources('xmltv', [SOURCE] * 9)
