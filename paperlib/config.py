from __future__ import annotations

import json
from dataclasses import MISSING
from pathlib import Path

from paperlib.models import QueryConfig


REQUIRED_KEYS = frozenset(
    name for name, field in QueryConfig.__dataclass_fields__.items()
    if field.default is MISSING and field.default_factory is MISSING
)


def load_config(path: Path) -> QueryConfig:
    """Load and validate the committed collector configuration."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid JSON in {path}") from error

    if not isinstance(data, dict):
        raise ValueError("configuration must be a JSON object")

    missing = sorted(REQUIRED_KEYS.difference(data))
    if missing:
        raise ValueError(f"missing required keys: {', '.join(missing)}")

    if data["schema_version"] != 1:
        raise ValueError("schema_version must be 1")
    if not isinstance(data["page_size"], int) or not 1 <= data["page_size"] <= 100:
        raise ValueError("page_size must be between 1 and 100")
    if not isinstance(data["min_api_interval_seconds"], (int, float)) or data[
        "min_api_interval_seconds"
    ] < 3.0:
        raise ValueError("min_api_interval_seconds must be at least 3.0")
    if not isinstance(data["daily_overlap_hours"], int) or data["daily_overlap_hours"] < 1:
        raise ValueError("daily_overlap_hours must be positive")
    if not isinstance(data["cron_hour"], int) or not 0 <= data["cron_hour"] <= 23:
        raise ValueError("cron_hour must be between 0 and 23")
    if not isinstance(data["cron_minute"], int) or not 0 <= data["cron_minute"] <= 59:
        raise ValueError("cron_minute must be between 0 and 59")

    supplemental = data.get("supplemental_queries", [])
    if not isinstance(supplemental, list):
        raise ValueError("supplemental_queries must be a list")
    parsed: list[tuple[str, str]] = []
    for item in supplemental:
        if not isinstance(item, dict) or not isinstance(item.get("query_id"), str) or not isinstance(item.get("base_query"), str):
            raise ValueError("each supplemental query needs query_id and base_query")
        parsed.append((item["query_id"], item["base_query"]))
    values = {key: data[key] for key in REQUIRED_KEYS}
    values["supplemental_queries"] = tuple(parsed)
    return QueryConfig(**values)
