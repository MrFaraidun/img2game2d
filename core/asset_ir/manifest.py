"""
Project Manifest management (*.img2game2d.json) for img2game2d projects.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ProjectManifest:
    schema_version: str = "3.0.0"
    name: str = ""
    source: str = ""
    asset_ir: str = "asset_ir.json"
    rig: Optional[str] = None
    animations: Dict[str, str] = field(default_factory=dict)
    materials: Dict[str, str] = field(default_factory=dict)
    atlases: Dict[str, str] = field(default_factory=dict)
    exports: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def load(cls, file_path: Path | str) -> ProjectManifest:
        p = Path(file_path)
        if not p.exists():
            raise FileNotFoundError(f"Project manifest not found: {p}")
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(
            schema_version=data.get("schema_version", "3.0.0"),
            name=data.get("name", ""),
            source=data.get("source", ""),
            asset_ir=data.get("asset_ir", "asset_ir.json"),
            rig=data.get("rig"),
            animations=data.get("animations", {}),
            materials=data.get("materials", {}),
            atlases=data.get("atlases", {}),
            exports=data.get("exports", {}),
        )

    def save(self, file_path: Path | str) -> None:
        p = Path(file_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2, ensure_ascii=False)
