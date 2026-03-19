"""
Long-Term Care Expert — Alert History Checker

Manages per-user alert history stored as JSON files under
``memory/alert_history/``.  Used by the L1 router to prevent duplicate
reports and alert fatigue by checking whether an alert of the same class
was already sent within a configurable look-back window.

Public API
----------
check_alert_history_impl(user_id, event_category, hours_lookback)
    Query whether an alert should be suppressed.

record_alert(user_id, event_category, report_type, source_skill)
    Record that a report was sent so future queries can suppress duplicates.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ALERT_HISTORY_DIR = Path(__file__).resolve().parent.parent / "memory" / "alert_history"

VALID_EVENT_CATEGORIES = frozenset(
    {
        "sleep_issue",
        "mobility_issue",
        "cognitive_issue",
        "weekly_summary",
    }
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _history_path(user_id: str) -> Path:
    """Return the path to a user's alert-history JSON file."""
    return ALERT_HISTORY_DIR / f"{user_id}_alerts.json"


def _load_history(user_id: str) -> dict[str, Any]:
    """Load a user's alert history from disk.

    Returns a default structure when the file does not exist yet (new user).
    """
    path = _history_path(user_id)
    if not path.exists():
        return {"user_id": user_id, "alerts": []}
    with path.open("r", encoding="utf-8") as fh:
        data: dict[str, Any] = json.load(fh)
    return data


def _save_history(data: dict[str, Any]) -> None:
    """Persist a user's alert history to disk (atomic-ish write)."""
    ALERT_HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    path = _history_path(data["user_id"])
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    tmp.replace(path)


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------


def check_alert_history_impl(
    user_id: str,
    event_category: str,
    hours_lookback: int = 48,
) -> dict[str, Any]:
    """Check whether an alert of *event_category* was sent within the
    look-back window for the given user.

    Parameters
    ----------
    user_id:
        Anonymous user identifier.
    event_category:
        One of ``sleep_issue``, ``mobility_issue``, ``cognitive_issue``,
        ``weekly_summary``.
    hours_lookback:
        How far back to look (hours).  Default 48; use 72 for weekly
        summaries.

    Returns
    -------
    dict with keys:
        ``user_id``, ``event_category``, ``hours_lookback``,
        ``recent_alert_found`` (bool), ``most_recent_sent_at`` (ISO str
        or ``null``), ``suppress_recommended`` (bool),
        ``total_alerts_in_window`` (int).
    """
    if not user_id or not isinstance(user_id, str):
        raise ValueError("user_id must be a non-empty string")
    if event_category not in VALID_EVENT_CATEGORIES:
        raise ValueError(
            f"Invalid event_category '{event_category}'. "
            f"Must be one of: {', '.join(sorted(VALID_EVENT_CATEGORIES))}"
        )
    if hours_lookback < 1:
        raise ValueError("hours_lookback must be >= 1")

    history = _load_history(user_id)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_lookback)

    matching: list[dict[str, Any]] = []
    for alert in history.get("alerts", []):
        if alert.get("event_category") != event_category:
            continue
        sent_at = datetime.fromisoformat(alert["sent_at"])
        if sent_at >= cutoff:
            matching.append(alert)

    # Sort descending so the most recent comes first
    matching.sort(key=lambda a: a["sent_at"], reverse=True)

    most_recent = matching[0]["sent_at"] if matching else None
    recent_found = len(matching) > 0

    return {
        "user_id": user_id,
        "event_category": event_category,
        "hours_lookback": hours_lookback,
        "recent_alert_found": recent_found,
        "most_recent_sent_at": most_recent,
        "suppress_recommended": recent_found,
        "total_alerts_in_window": len(matching),
    }


def record_alert(
    user_id: str,
    event_category: str,
    report_type: str,
    source_skill: str = "",
) -> dict[str, Any]:
    """Record that a report was sent for *user_id* / *event_category*.

    Parameters
    ----------
    user_id:
        Anonymous user identifier.
    event_category:
        One of ``sleep_issue``, ``mobility_issue``, ``cognitive_issue``,
        ``weekly_summary``.
    report_type:
        ``daily_insight``, ``weekly_summary``, or ``immediate_alert``.
    source_skill:
        Name of the L2 skill that produced the report.

    Returns
    -------
    dict confirming the recorded alert entry.
    """
    if not user_id or not isinstance(user_id, str):
        raise ValueError("user_id must be a non-empty string")
    if event_category not in VALID_EVENT_CATEGORIES:
        raise ValueError(
            f"Invalid event_category '{event_category}'. "
            f"Must be one of: {', '.join(sorted(VALID_EVENT_CATEGORIES))}"
        )

    history = _load_history(user_id)
    entry = {
        "event_category": event_category,
        "sent_at": datetime.now(timezone.utc).isoformat(),
        "report_type": report_type,
        "source_skill": source_skill,
    }
    history["alerts"].append(entry)
    _save_history(history)

    return {"recorded": True, "entry": entry}
