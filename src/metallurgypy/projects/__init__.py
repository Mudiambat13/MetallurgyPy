"""Project folders: an index (``project.json``), saved calculations and an activity history.

Layout::

    my_project/
      project.json        versioned index (format "metallurgypy.project")
      history.sqlite      append-only activity log (SQLite, standard library)
      calculations/       one ``*.mpy.json`` per saved calculation

Safety: file names come from a sanitised slug plus a counter, never from raw user text;
an index entry that points outside ``calculations/`` is refused; nothing is deleted
(removing an entry only unlists it); archives contain only the project's own files.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from metallurgypy.core.exceptions import MetallurgyPyError, RecordFormatError
from metallurgypy.core.results import CalculationResult
from metallurgypy.precision.uncertainty import UncertainResult
from metallurgypy.records import (
    FILE_SUFFIX,
    CalculationRecord,
    _write_text,
    load_record,
    save_record,
)

__all__ = [
    "PROJECT_FORMAT",
    "PROJECT_VERSION",
    "HistoryEvent",
    "Project",
    "ProjectEntry",
    "ProjectError",
]

PROJECT_FORMAT = "metallurgypy.project"
PROJECT_VERSION = 1
_INDEX = "project.json"
_HISTORY = "history.sqlite"
_CALC_DIR = "calculations"
_SLUG_BAD = re.compile(r"[^a-z0-9]+")


class ProjectError(MetallurgyPyError):
    """The project folder is missing, malformed, or an operation is not allowed."""


@dataclass(frozen=True)
class ProjectEntry:
    id: int
    name: str
    model_id: str
    file: str  # relative to the project folder, always inside calculations/
    saved: str


@dataclass(frozen=True)
class HistoryEvent:
    timestamp: str
    action: str
    detail: str


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _slug(text: str) -> str:
    slug = _SLUG_BAD.sub("-", text.lower()).strip("-")[:60]
    return slug or "calculation"


class Project:
    def __init__(self, root: Path, meta: dict[str, Any]) -> None:
        self.root = root
        self._meta = meta

    # ---- creation and opening ----

    @classmethod
    def create(cls, folder: str | os.PathLike[str], name: str, description: str = "") -> Project:
        root = Path(folder)
        if not name.strip():
            raise ProjectError("A project needs a name.")
        if (root / _INDEX).exists():
            raise ProjectError(f"{root} already contains a project; refusing to overwrite it.")
        if root.exists() and any(root.iterdir()):
            raise ProjectError(f"{root} is not empty; choose a new or empty folder.")
        (root / _CALC_DIR).mkdir(parents=True, exist_ok=True)
        now = _now()
        meta: dict[str, Any] = {
            "format": PROJECT_FORMAT,
            "format_version": PROJECT_VERSION,
            "name": name.strip(),
            "description": description,
            "created": now,
            "modified": now,
            "next_id": 1,
            "calculations": [],
        }
        project = cls(root, meta)
        project._write_index()
        project._log("create", name.strip())
        return project

    @classmethod
    def open(cls, folder: str | os.PathLike[str]) -> Project:
        root = Path(folder)
        index = root / _INDEX
        if not index.is_file():
            raise ProjectError(f"{root} is not a MetallurgyPy project (no {_INDEX}).")
        try:
            meta = json.loads(index.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ProjectError(f"{_INDEX} is not valid JSON: {exc}") from None
        if not isinstance(meta, dict) or meta.get("format") != PROJECT_FORMAT:
            raise ProjectError(f"{_INDEX} is not a MetallurgyPy project file.")
        version = meta.get("format_version")
        if isinstance(version, bool) or not isinstance(version, int) or version < 1:
            raise ProjectError("'format_version' must be a positive integer.")
        if version > PROJECT_VERSION:
            raise ProjectError(
                f"Project format version {version} is newer than this release understands ({PROJECT_VERSION})."
            )
        if not isinstance(meta.get("calculations"), list) or not isinstance(meta.get("name"), str):
            raise ProjectError("project.json is missing 'name' or 'calculations'.")
        return cls(root, meta)

    # ---- properties ----

    @property
    def name(self) -> str:
        return str(self._meta["name"])

    @property
    def description(self) -> str:
        return str(self._meta.get("description", ""))

    # ---- calculations ----

    def entries(self) -> tuple[ProjectEntry, ...]:
        out = []
        for raw in self._meta["calculations"]:
            try:
                out.append(
                    ProjectEntry(
                        int(raw["id"]),
                        str(raw["name"]),
                        str(raw["model_id"]),
                        str(raw["file"]),
                        str(raw["saved"]),
                    )
                )
            except (KeyError, TypeError, ValueError):
                raise ProjectError("project.json has a malformed calculation entry.") from None
        return tuple(out)

    def add_calculation(
        self,
        result: CalculationResult,
        name: str,
        *,
        notes: str = "",
        uncertain: UncertainResult | None = None,
    ) -> ProjectEntry:
        if not name.strip():
            raise ProjectError("A calculation needs a name.")
        calc_dir = self.root / _CALC_DIR
        calc_dir.mkdir(parents=True, exist_ok=True)
        base, n = _slug(name), 1
        while True:
            filename = f"{base}{'' if n == 1 else f'-{n}'}{FILE_SUFFIX}"
            if not (calc_dir / filename).exists():
                break
            n += 1
        save_record(
            calc_dir / filename, result, name=name.strip(), notes=notes, uncertainty=uncertain
        )
        entry_id = int(self._meta["next_id"])
        self._meta["next_id"] = entry_id + 1
        entry = ProjectEntry(
            entry_id, name.strip(), result.provenance.model_id, f"{_CALC_DIR}/{filename}", _now()
        )
        self._meta["calculations"].append(
            {
                "id": entry.id,
                "name": entry.name,
                "model_id": entry.model_id,
                "file": entry.file,
                "saved": entry.saved,
            }
        )
        self._write_index()
        self._log("add_calculation", f"{entry.name} ({entry.model_id}) -> {entry.file}")
        return entry

    def entry(self, entry_id: int) -> ProjectEntry:
        return self._entry(entry_id)

    def _entry(self, entry_id: int) -> ProjectEntry:
        for e in self.entries():
            if e.id == entry_id:
                return e
        raise ProjectError(f"No calculation with id {entry_id} in this project.")

    def _path_of(self, entry: ProjectEntry) -> Path:
        path = (self.root / entry.file).resolve()
        if not path.is_relative_to((self.root / _CALC_DIR).resolve()):
            raise ProjectError(
                f"Entry {entry.id} points outside the calculations folder; refusing to read it."
            )
        return path

    def load_calculation(self, entry_id: int) -> CalculationRecord:
        entry = self._entry(entry_id)
        path = self._path_of(entry)
        if not path.is_file():
            raise ProjectError(f"The file for {entry.name!r} is missing: {entry.file}")
        try:
            return load_record(path)
        except RecordFormatError as exc:
            raise ProjectError(f"{entry.file}: {exc}") from None

    def calculation_path(self, entry_id: int) -> Path:
        return self._path_of(self._entry(entry_id))

    def remove_entry(self, entry_id: int) -> None:
        """Unlist a calculation. The file stays on disk; delete it yourself if you want it gone."""
        entry = self._entry(entry_id)
        self._meta["calculations"] = [
            c for c in self._meta["calculations"] if int(c["id"]) != entry_id
        ]
        self._write_index()
        self._log("remove_entry", f"{entry.name} ({entry.file}) unlisted; file kept")

    # ---- history ----

    def history(self) -> tuple[HistoryEvent, ...]:
        with sqlite3.connect(self.root / _HISTORY) as db:
            rows = db.execute("SELECT timestamp, action, detail FROM events ORDER BY id").fetchall()
        return tuple(HistoryEvent(*r) for r in rows)

    def log_event(self, action: str, detail: str = "") -> None:
        """Record an activity such as ``'export_report'`` (the history is append-only)."""
        self._log(action, detail)

    def _log(self, action: str, detail: str) -> None:
        db = sqlite3.connect(self.root / _HISTORY)
        try:
            with db:
                db.execute(
                    "CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, "
                    "timestamp TEXT NOT NULL, action TEXT NOT NULL, detail TEXT NOT NULL)"
                )
                db.execute(
                    "INSERT INTO events (timestamp, action, detail) VALUES (?, ?, ?)",
                    (_now(), action, detail),
                )
        finally:
            db.close()

    # ---- persistence ----

    def _write_index(self) -> None:
        self._meta["modified"] = _now()
        text = json.dumps(self._meta, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
        _write_text(self.root / _INDEX, text, overwrite=True)

    def export_archive(self, archive: str | os.PathLike[str], *, overwrite: bool = False) -> Path:
        """Zip ``project.json``, the history and every listed calculation (fixed, relative names)."""
        target = Path(archive)
        if target.exists() and not overwrite:
            raise FileExistsError(f"{target} already exists; refusing to overwrite it.")
        target.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(self.root / _INDEX, _INDEX)
            zf.write(self.root / _HISTORY, _HISTORY)
            for e in self.entries():
                path = self._path_of(e)
                if path.is_file():
                    zf.write(path, f"{_CALC_DIR}/{path.name}")
        self._log("export_archive", target.name)
        return target
