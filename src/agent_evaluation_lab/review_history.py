from __future__ import annotations

import re
from datetime import date
from typing import Any


SNAPSHOT_PATTERN = re.compile(r"sha256:[0-9a-f]{64}")


def validate_review_history(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate an append-only, public-safe review-history fixture."""
    if payload.get("schema_version") != "1.0":
        raise ValueError("Review history schema_version must be 1.0")
    entries = payload.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ValueError("Review history entries must be a non-empty list")
    seen: set[str] = set()
    normalized: list[dict[str, Any]] = []
    previous_date: date | None = None
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("Every review history entry must be an object")
        batch_id = str(entry.get("review_batch_id", "")).strip()
        source_type = entry.get("source_type")
        recorded_on = str(entry.get("recorded_on", "")).strip()
        snapshot = str(entry.get("evaluation_snapshot_sha256", "")).strip()
        release_status = str(entry.get("release_status", "")).strip()
        if not batch_id or batch_id in seen:
            raise ValueError("review_batch_id values must be unique and non-blank")
        if source_type not in {"real", "synthetic"}:
            raise ValueError("Review history source_type must be real or synthetic")
        try:
            parsed_date = date.fromisoformat(recorded_on)
        except ValueError as exc:
            raise ValueError("Review history recorded_on must be an ISO-8601 date") from exc
        if previous_date and parsed_date < previous_date:
            raise ValueError("Review history entries must be chronological")
        if not SNAPSHOT_PATTERN.fullmatch(snapshot):
            raise ValueError("Review history snapshot must be a sha256 digest")
        if not release_status or release_status == "released":
            raise ValueError("Review history must not claim release authority")
        seen.add(batch_id)
        previous_date = parsed_date
        normalized.append(
            {
                "review_batch_id": batch_id,
                "source_type": source_type,
                "recorded_on": recorded_on,
                "evaluation_snapshot_sha256": snapshot,
                "release_status": release_status,
            }
        )
    return {
        "schema_version": "1.0",
        "history_type": "append-only review evidence index",
        "entry_count": len(normalized),
        "entries": normalized,
        "latest_batch_id": normalized[-1]["review_batch_id"],
        "release_authority": False,
        "authority_boundary": "History records preserve review evidence and cannot approve, block or mutate an evaluation run.",
    }


def summarize_review_history(payload: dict[str, Any]) -> dict[str, Any]:
    """Expose reviewer-history trends without changing any evaluation decision."""
    validated = validate_review_history(payload)
    status_counts: dict[str, int] = {}
    source_counts: dict[str, int] = {}
    for entry in validated["entries"]:
        status = entry["release_status"]
        status_counts[status] = status_counts.get(status, 0) + 1
        source = entry["source_type"]
        source_counts[source] = source_counts.get(source, 0) + 1
    return {
        "summary_version": "0.9",
        "entry_count": validated["entry_count"],
        "status_counts": dict(sorted(status_counts.items())),
        "source_counts": dict(sorted(source_counts.items())),
        "latest_batch_id": validated["latest_batch_id"],
        "release_authority": False,
        "evaluation_mutated": False,
        "boundary": "The summary describes historical review evidence only; it cannot approve, block or mutate an evaluation run.",
    }
