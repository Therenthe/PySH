"""Loopback API. No shell, credentials in logs, or network-visible admin port."""
import asyncio
import contextlib
from datetime import datetime, timezone
import hmac
import hashlib
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import secrets
import shutil
import sys
from typing import Literal
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .preferences import PreferenceStore, Station
from .device import Device, DeviceError
from .content import Content, ContentError
from .player import Player, PlayerError

ROOT = Path(__file__).resolve().parents[2]
DATA = Path(os.environ.get("PI_HUB_DATA", str(Path.home() / ".local/share/pi-smart-hub")))
VERSION = "1.0.0-candidate.1"
ALLOWED_HOSTS = {"127.0.0.1:8765", "localhost:8765", "127.0.0.1:5173", "localhost:5173"}
ALLOWED_ORIGINS = {"http://" + host for host in ALLOWED_HOSTS}
log = logging.getLogger("hub")


class StrictBody(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Power(StrictBody):
    enabled: bool


class BTAction(StrictBody):
    address: str = Field(pattern=r"^(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$")
    action: Literal["pair", "connect", "disconnect", "forget"]


class BTReply(StrictBody):
    id: str = Field(max_length=100)
    accept: bool
    value: str | None = Field(default=None, max_length=16)


class NetworkConnect(StrictBody):
    ssid: str = Field(min_length=1, max_length=32)
    password: str = Field(default="", max_length=128, repr=False)


class NetworkForget(StrictBody):
    id: str = Field(min_length=1, max_length=200)


class Audio(StrictBody):
    volume: int | None = Field(default=None, ge=0, le=100)
    mute: bool | None = None
    output: str | None = Field(default=None, max_length=200)


class Play(StrictBody):
    source: Literal["radio", "local"]
    url: str = Field(default="", max_length=2048)
    path: str = Field(default="", max_length=4096)
    title: str = Field(default="", max_length=300)


class Transport(StrictBody):
    action: Literal["pause", "resume", "toggle", "stop", "seek", "next", "previous"]
    value: float | None = Field(default=None, ge=0, le=864000)


class Favorite(StrictBody):
    station: Station
    remove: bool = False


class External(StrictBody):
    service: Literal["youtube", "netflix", "spotify"]


def validate_stream_url(url):
    parsed = urlsplit(url)
    # mpv supports powerful protocols; only explicit public web URLs are accepted.
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise ContentError("invalid_url")
    if any(ch in url for ch in ("\r", "\n", "\x00")):
        raise ContentError("invalid_url")
    return url


class Hub:
    def __init__(self, directory=DATA):
        self.store = PreferenceStore(directory)
        self.device = Device()
        self.content = Content(directory / "cache")
        self.player = Player()
        self.token = secrets.token_urlsafe(32)
        self.weather = None
        self.tasks = []
        self.external = None
        self.appliance = os.environ.get("PI_HUB_APPLIANCE") == "1"
        self.service_mode = False
        self.snapshots = {"network": {"available": False, "state": "initializing"}, "bluetooth": {"available": False, "devices": [], "prompts": []}, "audio": {"available": False, "outputs": []}}
        self.last_output = None
        self.audio_selected = False
        self._audio_restored = None
        self._device_lock = asyncio.Lock()
        self._weather_generation = 0
        self.queue = []
        self.queue_index = -1
        self.started = datetime.now(timezone.utc).isoformat()

    async def safe(self, name, function):
        try:
            return await asyncio.wait_for(function(), timeout=8)
        except Exception:
            return {"available": False, "error": name + "_unavailable"}

    async def refresh_device(self):
        async with self._device_lock:
            await self._refresh_device()

    async def _refresh_device(self):
        results = await asyncio.gather(self.safe("network", self.device.network_status), self.safe("bluetooth", self.device.bluetooth_status), self.safe("audio", self.device.audio_status))
        self.snapshots = dict(zip(("network", "bluetooth", "audio"), results))
        audio = self.snapshots["audio"]
        output = audio.get("output")
        outputs = audio.get("outputs", [])
        saved = self.store.value.audioOutput
        preferred = next((item for item in outputs if str(item.get("id")) == saved), None)
        restore_target = preferred or next((item for item in outputs if str(item.get("id")) == str(output) and item.get("bluetooth")), None)
        if restore_target and self._audio_restored != str(restore_target["id"]):
            try:
                restored = await asyncio.wait_for(self.device.audio_set(output=restore_target["id"], volume=self.store.value.volume, mute=self.store.value.mute), timeout=8)
                if restored.get("available") and not restored.get("error"):
                    audio = self.snapshots["audio"] = restored
                    output, outputs = audio.get("output"), audio.get("outputs", [])
                    self._audio_restored = str(restore_target["id"])
            except Exception:
                log.info("Saved audio settings unavailable")
        elif not restore_target:
            self._audio_restored = None
        active = next((item for item in outputs if str(item.get("id")) == str(output)), None)
        # An analog endpoint is not evidence of speakers. It must be selected explicitly.
        self.audio_selected = bool(active and (active.get("bluetooth") or str(active.get("id")) == self.store.value.audioOutput))
        if self.last_output is not None and (str(output) != str(self.last_output) or not self.audio_selected):
            with contextlib.suppress(Exception):
                await self.player.command("pause")
        self.last_output = output if self.audio_selected else None
        audio["ready"] = self.audio_selected

    async def monitor(self):
        while True:
            await self.refresh_device()
            await asyncio.sleep(2)

    async def refresh_weather(self):
        self._weather_generation += 1
        generation = self._weather_generation
        location = self.store.value.location
        identity = location.model_dump() if location else None
        if location:
            try:
                result = await self.content.weather(identity)
            except Exception:
                result = {**(self.weather or {}), "stale": True, "error": "weather_unavailable"}
        else:
            result = None
        current = self.store.value.location
        if generation == self._weather_generation and identity == (current.model_dump() if current else None):
            self.weather = result
        return self.weather

    async def weather_loop(self):
        while True:
            await self.refresh_weather()
            await asyncio.sleep(900)

    def background(self, coroutine):
        task = asyncio.create_task(coroutine)
        self.tasks.append(task)
        task.add_done_callback(lambda done: self.tasks.remove(done) if done in self.tasks else None)
        return task

    async def start(self):
        self.background(self.initialize_runtime())

    async def initialize_runtime(self):
        for operation in (self.device.initialize, self.player.start):
            try:
                await asyncio.wait_for(operation(), 10)
            except Exception:
                log.warning("Runtime component unavailable")
        self.background(self.monitor())
        self.background(self.weather_loop())

    async def close(self):
        tasks = list(self.tasks)
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        for operation in (self.player.close, self.device.close):
            with contextlib.suppress(Exception):
                await operation()
        if self.external and self.external.returncode is None:
            self.external.terminate()


@contextlib.asynccontextmanager
async def lifespan(app):
    DATA.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(DATA / "hub.log", maxBytes=256 * 1024, backupCount=3, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    log.setLevel(getattr(logging, os.environ.get("PI_HUB_LOG_LEVEL", "INFO").upper(), logging.INFO))
    log.addHandler(handler)
    app.state.hub = Hub()
    await app.state.hub.start()
    log.info("Hub started version=%s", VERSION)
    try:
        yield
    finally:
        await app.state.hub.close()
        log.removeHandler(handler)
        handler.close()


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)


@app.middleware("http")
async def boundary(request: Request, call_next):
    if request.headers.get("host") not in ALLOWED_HOSTS:
        return JSONResponse({"error": "forbidden_origin"}, status_code=403)
    origin = request.headers.get("origin")
    if origin and origin not in ALLOWED_ORIGINS:
        return JSONResponse({"error": "forbidden_origin"}, status_code=403)
    if request.url.path.startswith("/api/"):
        if request.headers.get("sec-fetch-site") == "cross-site":
            return JSONResponse({"error": "forbidden_origin"}, status_code=403)
        if request.method not in {"GET", "HEAD"}:
            token = request.headers.get("x-hub-token", "")
            if not hmac.compare_digest(token, request.app.state.hub.token):
                return JSONResponse({"error": "session_expired"}, status_code=403)
            if int(request.headers.get("content-length", "0")) > 65536:
                return JSONResponse({"error": "invalid_request"}, status_code=413)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; media-src 'self' blob:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; object-src 'none'"
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.exception_handler(RequestValidationError)
@app.exception_handler(ValidationError)
async def invalid_request(request, error):
    # Pydantic errors can contain submitted passwords. Never serialize them.
    return JSONResponse({"error": "invalid_request"}, status_code=422)


@app.exception_handler(DeviceError)
@app.exception_handler(ContentError)
@app.exception_handler(PlayerError)
async def integration_error(request, error):
    code = getattr(error, "code", "operation_failed")
    log.info("Integration result=%s", code)
    return JSONResponse({"error": code}, status_code=409)


@app.exception_handler(Exception)
async def unexpected_error(request, error):
    log.error("Request failed type=%s", type(error).__name__)
    return JSONResponse({"error": "operation_failed"}, status_code=500)


@app.get("/api/session")
async def session(request: Request):
    return {"token": request.app.state.hub.token, "version": VERSION}


@app.get("/api/state")
async def state(request: Request):
    hub = request.app.state.hub
    playback = await hub.player.status()
    local = playback.get("kind") == "audio" and bool(playback.get("url"))
    playback.update(canPrevious=local and hub.queue_index > 0, canNext=local and 0 <= hub.queue_index < len(hub.queue) - 1)
    return {"version": VERSION, "preferences": hub.store.export(), **hub.snapshots, "player": playback, "weather": hub.weather, "recovered": hub.store.recovered, "appliance": hub.appliance, "serviceMode": hub.service_mode}


@app.patch("/api/preferences")
async def preferences(request: Request, patch: dict):
    hub = request.app.state.hub
    result = hub.store.update(patch)
    if "location" in patch:
        hub.weather = None
        hub.background(hub.refresh_weather())
    return result


@app.post("/api/bluetooth/power")
async def bluetooth_power(request: Request, body: Power):
    return await request.app.state.hub.device.bluetooth_power(body.enabled)


@app.post("/api/bluetooth/scan")
async def bluetooth_scan(request: Request):
    return await request.app.state.hub.device.bluetooth_scan()


@app.post("/api/bluetooth/action")
async def bluetooth_action(request: Request, body: BTAction):
    hub = request.app.state.hub
    if body.action in {"disconnect", "forget"}:
        with contextlib.suppress(Exception):
            await hub.player.command("pause")
    result = await hub.device.bluetooth_action(body.address, body.action)
    await hub.refresh_device()
    return result


@app.post("/api/bluetooth/reply")
async def bluetooth_reply(request: Request, body: BTReply):
    return await request.app.state.hub.device.bluetooth_reply(body.id, body.accept, body.value)


@app.post("/api/network/scan")
async def network_scan(request: Request):
    return await request.app.state.hub.device.network_scan()


@app.post("/api/network/connect")
async def network_connect(request: Request, body: NetworkConnect):
    result = await request.app.state.hub.device.network_connect(body.ssid, body.password)
    await request.app.state.hub.refresh_device()
    return result


@app.post("/api/network/forget")
async def network_forget(request: Request, body: NetworkForget):
    return await request.app.state.hub.device.network_forget(body.id)


@app.post("/api/audio")
async def audio(request: Request, body: Audio):
    hub = request.app.state.hub
    result = await hub.device.audio_set(**body.model_dump(exclude_none=True))
    if not result.get("error"):
        patch = {}
        if body.volume is not None:
            patch["volume"] = body.volume
        if body.mute is not None:
            patch["mute"] = body.mute
        if body.output is not None:
            patch["audioOutput"] = body.output
        if patch:
            hub.store.update(patch)
        await hub.refresh_device()
    return result


@app.get("/api/geocode")
async def geocode(request: Request, q: str = ""):
    return {"results": await request.app.state.hub.content.geocode(q[:160])}


@app.post("/api/weather/refresh")
async def weather_refresh(request: Request):
    return await request.app.state.hub.refresh_weather()


@app.get("/api/radio")
async def radio(request: Request, q: str = "", country: str = "", language: str = ""):
    return await request.app.state.hub.content.radio_search(q[:160], country[:100], language[:100])


@app.post("/api/favorites")
async def favorite(request: Request, body: Favorite):
    hub = request.app.state.hub
    values = [item.model_dump() for item in hub.store.value.favorites if item.uuid != body.station.uuid]
    if not body.remove:
        values.append(body.station.model_dump())
    return hub.store.update({"favorites": values})


@app.get("/api/media")
async def media(request: Request, path: str = ""):
    return await request.app.state.hub.content.media_list(path)


@app.get("/api/media/file")
async def media_file(request: Request, path: str):
    canonical = request.app.state.hub.content.resolve_media(path)
    return FileResponse(canonical)


@app.post("/api/play")
async def play(request: Request, body: Play):
    hub = request.app.state.hub
    await hub.refresh_device()
    if not hub.audio_selected:
        return JSONResponse({"error": "no_audio_output"}, status_code=409)
    await hub.player.select_output(hub.snapshots["audio"]["output"])
    source = validate_stream_url(body.url) if body.source == "radio" else str(hub.content.resolve_media(body.path))
    if body.source == "local":
        listing = await hub.content.media_list(str(Path(source).parent))
        hub.queue = [item for item in listing["items"] if item["kind"] == "audio"]
        hub.queue_index = next((i for i, item in enumerate(hub.queue) if item["path"] == source), -1)
    else:
        hub.queue = []
        hub.queue_index = -1
        hub.store.update({"lastStation": {"uuid": hashlib.sha256(source.encode()).hexdigest(), "name": body.title or "Radio", "url": source}})
    return await hub.player.play(source, title=body.title, kind=body.source)


@app.post("/api/player")
async def player(request: Request, body: Transport):
    hub = request.app.state.hub
    if body.action in {"resume", "toggle"} and not hub.audio_selected:
        return JSONResponse({"error": "no_audio_output"}, status_code=409)
    if body.action in {"resume", "toggle", "next", "previous"} and hub.audio_selected:
        await hub.player.select_output(hub.snapshots["audio"]["output"])
    if body.action in {"previous", "next"}:
        if not hub.audio_selected:
            return JSONResponse({"error": "no_audio_output"}, status_code=409)
        next_index = hub.queue_index + (1 if body.action == "next" else -1)
        if not 0 <= next_index < len(hub.queue):
            return JSONResponse({"error": "no_more_tracks"}, status_code=409)
        item = hub.queue[next_index]
        target = str(hub.content.resolve_media(item["path"]))
        result = await hub.player.play(target, title=item["name"], kind="local")
        hub.queue_index = next_index
        return result
    return await hub.player.command(body.action, body.value)


@app.post("/api/external")
async def external(request: Request, body: External):
    hub = request.app.state.hub
    executable = shutil.which("chromium")
    if sys.platform != "linux" or not executable:
        return JSONResponse({"error": "browser_unavailable"}, status_code=409)
    if hub.external and hub.external.returncode is None:
        return JSONResponse({"error": "service_already_open"}, status_code=409)
    with contextlib.suppress(Exception):
        await hub.player.command("pause")
    urls = {"youtube": "https://www.youtube.com", "netflix": "https://www.netflix.com", "spotify": "https://open.spotify.com"}
    hub.external = await asyncio.create_subprocess_exec(executable, "--ozone-platform=wayland", "--no-first-run", "--start-maximized", "--user-data-dir=" + str(DATA / "services-browser"), "--load-extension=" + str(ROOT / "app" / "browser-extension"), "--app=" + urls[body.service], stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
    return {"opened": True, "service": body.service}


@app.post("/api/exit")
async def exit_hub(request: Request):
    hub = request.app.state.hub
    if hub.appliance:
        # Do not leave media playing behind the recovery screen. If stopping a
        # running player fails, retain the normal UI so its controls stay usable.
        playback = await hub.player.status()
        if playback.get("state") not in {"idle", "ended", "error"}:
            await hub.player.command("stop")
        if hub.external and hub.external.returncode is None:
            hub.external.terminate()
            try:
                await asyncio.wait_for(hub.external.wait(), timeout=3)
            except asyncio.TimeoutError:
                hub.external.kill()
                await hub.external.wait()
        hub.service_mode = True
        return {"exiting": False, "mode": "service"}
    if not os.environ.get("PI_HUB_SUPERVISED"):
        return JSONResponse({"error": "desktop_exit_unavailable"}, status_code=409)
    (DATA / "exit-request").write_text("exit", encoding="utf-8")
    return {"exiting": True}


@app.post("/api/service/return")
async def return_from_service(request: Request):
    hub = request.app.state.hub
    if not hub.appliance:
        return JSONResponse({"error": "unavailable"}, status_code=409)
    hub.service_mode = False
    return {"mode": "hub"}


@app.get("/api/diagnostics")
async def diagnostics(request: Request):
    hub = request.app.state.hub
    # Deliberate allowlist: no IP/MAC/SSID, paths, station URLs, tokens or raw logs.
    payload = {"version": VERSION, "started": hub.started, "python": sys.version.split()[0], "platform": sys.platform, "services": {key: {"available": value.get("available", False), "error": value.get("error")} for key, value in hub.snapshots.items()}, "preferencesRecovered": hub.store.recovered, "weatherStale": hub.weather.get("stale") if hub.weather else None}
    return JSONResponse(payload, headers={"Content-Disposition": 'attachment; filename="pi-smart-hub-diagnostics.json"'})


if (ROOT / "dist").is_dir():
    app.mount("/", StaticFiles(directory=ROOT / "dist", html=True), name="frontend")
