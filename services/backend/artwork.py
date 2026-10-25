"""Bounded known radio logos; public DNS is verified on every redirect."""
import asyncio
from http.client import HTTPConnection, HTTPSConnection
from html.parser import HTMLParser
import ipaddress
import socket
import time
from urllib.parse import urlsplit, urljoin

from .content import ContentError

MAX_ARTWORK = 256 * 1024
MIME_TYPES = {'image/png', 'image/jpeg', 'image/webp', 'image/gif', 'image/x-icon', 'image/vnd.microsoft.icon'}


class IconLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag != 'link' or len(self.links) >= 16:
            return
        values = dict(attrs)
        rel = (values.get('rel') or '').lower().split()
        href = values.get('href') or ''
        if len(href) <= 2048 and {'icon', 'apple-touch-icon', 'apple-touch-icon-precomposed'} & set(rel):
            self.links.append((0 if 'apple-touch-icon' in rel or '.png' in href.lower() else 1, href))


class Artwork:
    def __init__(self):
        self.cache = {}

    async def get(self, url):
        return await self.cached(url, lambda: self.fetch(url))

    async def homepage(self, url):
        return await self.cached('homepage:' + url, lambda: self.fetch_homepage(url))

    async def cached(self, url, fetch):
        cached = self.cache.get(url)
        if cached and cached[0] > time.monotonic():
            return cached[1:]
        result = await asyncio.to_thread(fetch)
        if len(self.cache) >= 128:
            self.cache.pop(next(iter(self.cache)))
        self.cache[url] = (time.monotonic() + 600, *result)
        return result

    @staticmethod
    def request(url, html=False, redirects=0, deadline=None):
        connection = None
        deadline = deadline or time.monotonic() + 12
        try:
            if not isinstance(url, str) or len(url) > 2048 or any(ord(c) < 33 for c in url):
                raise ValueError()
            parsed = urlsplit(url)
            if parsed.scheme not in {'http', 'https'} or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
                raise ValueError()
            port = parsed.port or (443 if parsed.scheme == 'https' else 80)
            if port not in {80, 443}:
                raise ValueError()
            addresses = socket.getaddrinfo(parsed.hostname, port, type=socket.SOCK_STREAM)
            if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global or ipaddress.ip_address(item[4][0]).is_multicast for item in addresses):
                raise ValueError()
            # Pin the connection to the already verified public DNS result. Keep
            # original hostname for TLS certificate verification/SNI and Host.
            public_ip = addresses[0][4][0]
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ValueError()
            connection = (HTTPSConnection if parsed.scheme == 'https' else HTTPConnection)(parsed.hostname, port, timeout=min(5, remaining))
            connection._create_connection = lambda address, timeout, source_address=None: socket.create_connection((public_ip, port), timeout, source_address)
            connection.request('GET', (parsed.path or '/') + ('?' + parsed.query if parsed.query else ''), headers={'Accept': 'text/html' if html else ', '.join(sorted(MIME_TYPES)), 'User-Agent': 'PiSmartHub/1.0'})
            response = connection.getresponse()
            if response.status in {301, 302, 303, 307, 308}:
                location = response.getheader('Location', '')
                if redirects >= 3 or not location:
                    raise ValueError()
                target = urljoin(url, location)
                if parsed.scheme == 'https' and urlsplit(target).scheme != 'https':
                    raise ValueError()
                connection.close()
                connection = None
                return Artwork.request(target, html, redirects + 1, deadline)
            mime = response.getheader('Content-Type', '').split(';')[0].lower()
            if response.status != 200 or mime not in ({'text/html', 'application/xhtml+xml'} if html else MIME_TYPES):
                raise ValueError()
            raw = response.read(64 * 1024 if html else MAX_ARTWORK + 1)
            if not raw or not html and len(raw) > MAX_ARTWORK:
                raise ValueError()
            return raw, mime, url
        except Exception as error:
            raise ContentError('artwork_unavailable') from error
        finally:
            if connection is not None:
                connection.close()

    @staticmethod
    def fetch(url, deadline=None):
        raw, mime, _ = Artwork.request(url, deadline=deadline)
        magic = ((mime == 'image/png' and raw.startswith(b'\x89PNG\r\n\x1a\n'))
                 or (mime == 'image/jpeg' and raw.startswith(b'\xff\xd8\xff'))
                 or (mime == 'image/gif' and raw[:6] in {b'GIF87a', b'GIF89a'})
                 or (mime == 'image/webp' and raw[:4] == b'RIFF' and raw[8:12] == b'WEBP')
                 or (mime in {'image/x-icon', 'image/vnd.microsoft.icon'} and len(raw) >= 22 and raw[:4] == b'\0\0\1\0' and 1 <= int.from_bytes(raw[4:6], 'little') <= 64))
        if not magic:
            raise ContentError('artwork_unavailable')
        return raw, mime

    @staticmethod
    def fetch_homepage(url):
        deadline = time.monotonic() + 12
        raw, _, page = Artwork.request(url, html=True, deadline=deadline)
        parser = IconLinks()
        parser.feed(raw.decode('utf-8', errors='replace'))
        links = [urljoin(page, href) for _, href in sorted(parser.links)]
        links.append(urljoin(page, '/favicon.ico'))
        for target in list(dict.fromkeys(links))[:3]:
            try:
                return Artwork.fetch(target, deadline=deadline)
            except ContentError:
                continue
        raise ContentError('artwork_unavailable')
