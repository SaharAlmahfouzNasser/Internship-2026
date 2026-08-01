"""JSON and JSONL helpers for experiment artifacts."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any, TypeVar

T = TypeVar("T")


def ensure_parent_dir(path: str | Path) -> Path:
    """Create the parent directory for a file path if needed."""

    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    return file_path


def read_json(path: str | Path) -> Any:
    """Read a JSON file."""

    with Path(path).open("r", encoding="utf-8") as file:
        return json.load(file)


def write_json(path: str | Path, data: Any, *, indent: int = 2) -> None:
    """Write a JSON file."""

    file_path = ensure_parent_dir(path)
    with file_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=indent)
        file.write("\n")


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    """Read a JSONL file into a list of dictionaries."""

    file_path = Path(path)
    if not file_path.exists():
        return []

    records: list[dict[str, Any]] = []
    with file_path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {file_path}:{line_number}") from exc
            if not isinstance(record, dict):
                raise ValueError(f"Expected object at {file_path}:{line_number}")
            records.append(record)
    return records


def write_jsonl(path: str | Path, records: Iterable[dict[str, Any]]) -> None:
    """Write dictionaries to a JSONL file."""

    file_path = ensure_parent_dir(path)
    with file_path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False))
            file.write("\n")


def append_jsonl(path: str | Path, record: dict[str, Any]) -> None:
    """Append one dictionary to a JSONL file."""

    file_path = ensure_parent_dir(path)
    with file_path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False))
        file.write("\n")


def load_dataclass_jsonl(path: str | Path, factory: Callable[[dict[str, Any]], T]) -> list[T]:
    """Load JSONL records and convert each record with a dataclass factory."""

    return [factory(record) for record in read_jsonl(path)]


def write_dataclass_jsonl(path: str | Path, records: Iterable[Any]) -> None:
    """Write dataclass-like records that expose a to_dict method."""

    write_jsonl(path, [record.to_dict() for record in records])
