"""Validated preferences with atomic writes and a last-known-good backup."""
import json
import os
from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Location(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str = Field(min_length=1, max_length=160)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    country: str = Field(default="", max_length=100)
    admin1: str = Field(default="", max_length=100)
    timezone: str = Field(default="", max_length=100)


class Station(BaseModel):
    model_config = ConfigDict(extra="ignore")
    uuid: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=160)
    url: str = Field(default="", max_length=2048)
    url_resolved: str = Field(default="", max_length=2048)
    country: str = Field(default="", max_length=100)
    language: str = Field(default="", max_length=100)
    tags: str = Field(default="", max_length=1000)
    favicon: str = Field(default="", max_length=2048)
    bitrate: int = Field(default=0, ge=0)
    codec: str = Field(default="", max_length=40)
    homepage: str = Field(default="", max_length=2048)


class Preferences(BaseModel):
    model_config = ConfigDict(extra="forbid")
    language: Literal["ro", "en"] = "ro"
    theme: Literal["ink", "night"] = "ink"
    accent: Literal["sage", "amber", "blue"] = "sage"
    nightEnabled: bool = False
    nightStart: str = Field(default="22:00", pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    nightEnd: str = Field(default="07:00", pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    screensaverMinutes: int = Field(default=5, ge=0, le=120)
    visualizerStyle: Literal["off", "wave", "bars", "orbit"] = "off"
    timezone: str = "Europe/Bucharest"
    location: Location | None = None
    setupComplete: bool = False
    favorites: list[Station] = Field(default_factory=list, max_length=200)
    shortcuts: list[Literal["radio", "media", "bluetooth", "weather"]] = Field(default_factory=lambda: ["radio", "media"], max_length=3)
    volume: int = Field(default=40, ge=0, le=100)
    mute: bool = False
    audioOutput: str | None = None
    lastStation: Station | None = None

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value):
        try:
            ZoneInfo(value)
        except (ValueError, ZoneInfoNotFoundError):
            raise ValueError("invalid_timezone") from None
        return value


class PreferenceStore:
    def __init__(self, directory: Path):
        self.directory = directory
        directory.mkdir(parents=True, exist_ok=True)
        self.path = directory / "preferences.json"
        self.backup = directory / "preferences.backup.json"
        self.recovered = False
        self.value = self._load()

    def _load(self):
        for path in (self.path, self.backup):
            if path.exists():
                try:
                    result = Preferences.model_validate_json(path.read_text(encoding="utf-8"))
                    self.recovered = path == self.backup
                    return result
                except (ValueError, OSError):
                    self.recovered = True
        return Preferences()

    def _atomic(self, path, data):
        temporary = path.with_suffix(".tmp")
        with temporary.open("w", encoding="utf-8") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if os.name != "nt":
            temporary.chmod(0o600)
        os.replace(temporary, path)

    def update(self, patch: dict):
        new = Preferences.model_validate({**self.value.model_dump(), **patch})
        # Backup the validated in-memory value, never a possibly corrupt disk file.
        self._atomic(self.backup, self.value.model_dump_json(indent=2))
        self._atomic(self.path, new.model_dump_json(indent=2))
        self.value = new
        return new.model_dump()

    def export(self):
        return json.loads(self.value.model_dump_json())
