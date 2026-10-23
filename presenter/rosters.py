"""Saved class lists for the random draw."""

from __future__ import annotations

import json
from pathlib import Path

from PyQt6.QtCore import QStandardPaths


def default_roster_path() -> Path:
    base = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    folder = Path(base) if base else Path.home() / ".presenter"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / "rosters.json"


class RosterStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_roster_path()
        self._lists: dict[str, list[str]] = {}
        self._order: list[str] = []
        self.active = ""
        self._read()

    def titles(self) -> list[str]:
        return list(self._order)

    def names_for(self, title: str) -> list[str]:
        return list(self._lists.get(title, []))

    def active_names(self) -> list[str]:
        if not self.active:
            return []
        return self.names_for(self.active)

    def remember(self, title: str, names: list[str]) -> None:
        title = title.strip() or "Lista"
        cleaned = [name.strip() for name in names if name and name.strip()]
        if title not in self._lists:
            self._order.append(title)
        self._lists[title] = cleaned
        self.active = title
        self._write()

    def select(self, title: str) -> list[str]:
        if title not in self._lists:
            return []
        self.active = title
        self._write()
        return self.names_for(title)

    def forget(self, title: str) -> str:
        if title not in self._lists:
            return self.active
        index = self._order.index(title)
        self._order.pop(index)
        del self._lists[title]
        if self.active == title:
            if self._order:
                self.active = self._order[min(index, len(self._order) - 1)]
            else:
                self.active = ""
        self._write()
        return self.active

    def _read(self) -> None:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeError):
            return
        lists = data.get("lists")
        if not isinstance(lists, dict):
            return
        order = data.get("order")
        if not isinstance(order, list):
            order = list(lists)
        for title in order:
            if not isinstance(title, str) or title not in lists:
                continue
            raw_names = lists[title]
            if not isinstance(raw_names, list):
                continue
            cleaned = [name.strip() for name in raw_names if isinstance(name, str) and name.strip()]
            self._order.append(title)
            self._lists[title] = cleaned
        active = data.get("active")
        if isinstance(active, str) and active in self._lists:
            self.active = active

    def _write(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"active": self.active, "order": self._order, "lists": self._lists}
        temporary = self.path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(self.path)
