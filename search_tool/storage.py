from __future__ import annotations

import json
from pathlib import Path

from .indexer import InvertedIndex


DEFAULT_INDEX_PATH = Path("index/search_index.json")


def save_index(index: InvertedIndex, path: Path = DEFAULT_INDEX_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(index.to_dict(), handle, indent=2)
    return path


def load_index(path: Path = DEFAULT_INDEX_PATH) -> InvertedIndex:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return InvertedIndex.from_dict(payload)
