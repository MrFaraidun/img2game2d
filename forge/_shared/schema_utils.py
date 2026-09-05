"""
img2game2d shared schema utilities.
JSON Schema validation for all spec files.

Local-first: resolves all $ref schemas from disk — never hits the network.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_DIR = Path(__file__).parent.parent.parent / "schemas"


def load_schema(name: str) -> dict:
    """Load a schema by name (without .schema.json suffix)."""
    path = SCHEMA_DIR / f"{name}.schema.json"
    if not path.exists():
        raise FileNotFoundError(f"Schema not found: {path}")
    with open(path) as f:
        return json.load(f)


def _build_local_store() -> dict:
    """
    Pre-load all schemas into a dict keyed by their $id value.
    This lets jsonschema resolve cross-schema $refs from disk
    without making any network requests.
    """
    store: dict = {}
    for schema_file in SCHEMA_DIR.glob("*.schema.json"):
        with open(schema_file) as f:
            s = json.load(f)
        schema_id = s.get("$id")
        if schema_id:
            store[schema_id] = s
        # Also store by file URI as fallback
        store[schema_file.as_uri()] = s
    return store


def validate(data: Any, schema_name: str) -> list[str]:
    """
    Validate data against named schema.
    Returns list of error strings (empty = valid).
    Uses jsonschema if available, with local $ref store.
    Falls back to basic required-fields check if jsonschema is not installed.
    """
    schema = load_schema(schema_name)

    try:
        import jsonschema

        store = _build_local_store()
        # Use the schema's own $id as the base URI so relative $refs work
        schema_id = schema.get("$id", "")
        resolver = jsonschema.RefResolver(
            base_uri=schema_id or (SCHEMA_DIR / f"{schema_name}.schema.json").as_uri(),
            referrer=schema,
            store=store,
        )

        errors: list[str] = []
        validator = jsonschema.Draft7Validator(schema, resolver=resolver)
        for err in validator.iter_errors(data):
            path = ".".join(str(p) for p in err.absolute_path)
            errors.append(f"{path}: {err.message}" if path else err.message)
        return errors

    except ImportError:
        pass

    # ── stdlib fallback: check required fields only ───────────────────────────
    errors = []
    required = schema.get("required", [])
    if isinstance(data, dict):
        for field in required:
            if field not in data:
                errors.append(f"Missing required field: '{field}'")
    return errors


def validate_or_exit(data: Any, schema_name: str, label: str = "") -> None:
    """Validate and exit(1) if invalid."""
    import sys
    errors = validate(data, schema_name)
    if errors:
        print(f"Schema validation failed for {label or schema_name}:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        sys.exit(1)


def load_json(path: str) -> Any:
    with open(path) as f:
        return json.load(f)


def save_json(data: Any, path: str, indent: int = 2) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=indent)
    print(f"Saved: {path}")
