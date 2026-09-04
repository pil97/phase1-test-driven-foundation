from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class EvidenceStore:
    """Filesystem evidence writer with raw-first semantics.

    Role raw text is always written first. Parsed JSON is written only after the
    caller has successfully parsed and schema-validated that role output.
    """

    def __init__(self, run_dir: Path) -> None:
        self.run_dir = run_dir
        self.run_dir.mkdir(parents=True, exist_ok=True)

    def iteration_dir(self, iteration: int) -> Path:
        path = self.run_dir / f"iteration-{iteration:02d}"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def write_raw(self, iteration: int, role: str, raw_text: str) -> Path:
        path = self.iteration_dir(iteration) / f"{role}.raw.txt"
        path.write_text(raw_text, encoding="utf-8")
        return path

    def write_parsed(self, iteration: int, role: str, parsed: dict[str, Any]) -> Path:
        path = self.iteration_dir(iteration) / f"{role}.json"
        self._write_json(path, parsed)
        return path

    def write_validation(self, iteration: int, name: str, result: dict[str, Any]) -> Path:
        path = self.iteration_dir(iteration) / f"{name}.json"
        self._write_json(path, result)
        return path

    def write_top_level(self, filename: str, value: dict[str, Any]) -> Path:
        path = self.run_dir / filename
        self._write_json(path, value)
        return path

    @staticmethod
    def _write_json(path: Path, value: dict[str, Any]) -> None:
        path.write_text(
            json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
