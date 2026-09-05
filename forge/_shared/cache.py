"""
img2game2d incremental build cache.
Prevents regeneration of already-built pipeline stages.

Cache entries keyed by (step_id, input_hash).
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


DEFAULT_CACHE_DIR = ".img2game2d/cache"


class Cache:
    def __init__(self, cache_dir: str = DEFAULT_CACHE_DIR) -> None:
        self._dir = Path(cache_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._index_path = self._dir / "index.json"
        self._index: dict = self._load_index()

    def _load_index(self) -> dict:
        if self._index_path.exists():
            with open(self._index_path) as f:
                return json.load(f)
        return {}

    def _save_index(self) -> None:
        with open(self._index_path, "w") as f:
            json.dump(self._index, f, indent=2)

    @staticmethod
    def file_hash(path: str) -> str:
        """SHA-256 of a file's contents."""
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    @staticmethod
    def data_hash(data: Any) -> str:
        """SHA-256 of JSON-serializable data."""
        h = hashlib.sha256()
        h.update(json.dumps(data, sort_keys=True).encode())
        return h.hexdigest()

    def is_cached(self, step_id: str, input_hash: str) -> bool:
        """Returns True if this step + input hash is already cached."""
        key = f"{step_id}:{input_hash}"
        entry = self._index.get(key)
        if not entry:
            return False
        # Check output files still exist
        outputs = entry.get("outputs", [])
        return all(Path(p).exists() for p in outputs)

    def record(self, step_id: str, input_hash: str, outputs: list[str]) -> None:
        """Record a completed step in the cache."""
        key = f"{step_id}:{input_hash}"
        self._index[key] = {
            "step_id": step_id,
            "input_hash": input_hash,
            "outputs": outputs,
            "cached_at": datetime.now(timezone.utc).isoformat(),
        }
        self._save_index()

    def invalidate(self, step_id: str) -> None:
        """Remove all cache entries for a step."""
        keys_to_remove = [k for k in self._index if k.startswith(f"{step_id}:")]
        for k in keys_to_remove:
            del self._index[k]
        self._save_index()
        print(f"Cache invalidated for: {step_id}")
