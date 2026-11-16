"""Application-wide state: user settings and the log of this session's calculations."""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

THEMES = ("light", "dark")
MIN_DIGITS, MAX_DIGITS = 3, 15
MAX_RECENT = 10


def format_number(value: float, digits: int) -> str:
    """Format ``value`` with ``digits`` significant digits, for display only.

    The value held by the engine is never changed. Integer digits are never
    dropped, and plain notation is kept for everyday magnitudes.
    """
    if value == 0.0:
        return "0"
    magnitude = abs(value)
    text = f"{value:.{digits}g}"
    if "e" in text and 1e-4 <= magnitude < 1e12:
        decimals = max(digits - math.floor(math.log10(magnitude)) - 1, 0)
        text = f"{value:.{decimals}f}"
    return text


@dataclass
class AppSettings:
    theme: str = "light"
    display_digits: int = 6
    default_folder: str = ""
    recent_files: list[str] = field(default_factory=list)

    def add_recent(self, path: str | os.PathLike[str]) -> None:
        text = os.fspath(path)
        self.recent_files = [text] + [p for p in self.recent_files if p != text]
        del self.recent_files[MAX_RECENT:]

    def to_dict(self) -> dict[str, Any]:
        return {
            "theme": self.theme,
            "display_digits": self.display_digits,
            "default_folder": self.default_folder,
            "recent_files": list(self.recent_files),
        }

    @classmethod
    def from_dict(cls, data: object) -> AppSettings:
        """Tolerant loader: invalid or missing entries fall back to defaults."""
        settings = cls()
        if not isinstance(data, dict):
            return settings
        if data.get("theme") in THEMES:
            settings.theme = data["theme"]
        digits = data.get("display_digits")
        if (
            isinstance(digits, int)
            and not isinstance(digits, bool)
            and MIN_DIGITS <= digits <= MAX_DIGITS
        ):
            settings.display_digits = digits
        if isinstance(data.get("default_folder"), str):
            settings.default_folder = data["default_folder"]
        recent = data.get("recent_files")
        if isinstance(recent, list):
            settings.recent_files = [p for p in recent if isinstance(p, str)][:MAX_RECENT]
        return settings

    @classmethod
    def load(cls, path: Path) -> AppSettings:
        try:
            return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            return cls()

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")


@dataclass(frozen=True)
class SessionEntry:
    model_title: str
    finished_at: str
    saved_to: str | None = None


@dataclass
class AppState:
    """Only real data lives here: nothing is invented to fill the dashboard."""

    settings: AppSettings = field(default_factory=AppSettings)
    session: list[SessionEntry] = field(default_factory=list)
    running_tasks: int = 0

    def log_calculation(self, model_title: str) -> None:
        self.session.append(SessionEntry(model_title, datetime.now().strftime("%H:%M:%S")))
