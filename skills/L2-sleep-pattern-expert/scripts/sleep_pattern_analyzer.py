"""
Sleep Pattern Analyzer

Utility script for the Sleep Pattern Expert skill.
Processes raw bed_exit and tossing_and_turning sensor events into
structured multi-day trend summaries for consumption by the L2 skill.

Input:  Raw JSON sensor events from L1 routing payload
Output: Structured sleep pattern summary dict

Usage:
    from skills.L2_sleep_pattern_expert.scripts.sleep_pattern_analyzer import analyze_sleep_events
    summary = analyze_sleep_events(triggering_events, baseline_comparison)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, time
from typing import Optional


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class BedExitEvent:
    timestamp: datetime
    duration_minutes: Optional[int] = None


@dataclass
class TossingEvent:
    timestamp: datetime
    duration_minutes: int


@dataclass
class SleepPatternSummary:
    """Structured summary of multi-day sleep pattern for L2 skill consumption."""

    # Counts
    total_bed_exits: int = 0
    nighttime_bed_exits: int = 0       # 23:00–06:00
    tossing_events: int = 0

    # Duration
    total_tossing_minutes: int = 0
    avg_tossing_minutes_per_night: float = 0.0

    # Timing
    earliest_exit_hour: Optional[int] = None   # hour of day (0-23)
    latest_exit_hour: Optional[int] = None

    # Multi-day
    nights_with_activity: int = 0
    distinct_calendar_days: set = field(default_factory=set)

    # Deviation from baseline
    baseline_deviation_description: str = ""
    is_multi_day_trend: bool = False

    # Warm language summary (for skill to use as starting point)
    warm_description: str = ""


# ---------------------------------------------------------------------------
# Nighttime window
# ---------------------------------------------------------------------------

NIGHTTIME_START = time(23, 0)   # 23:00
NIGHTTIME_END = time(6, 0)      # 06:00


def _is_nighttime(dt: datetime) -> bool:
    """Return True if datetime falls in the 23:00–06:00 window."""
    t = dt.time()
    if NIGHTTIME_START <= NIGHTTIME_END:
        return NIGHTTIME_START <= t <= NIGHTTIME_END
    # Wraps midnight
    return t >= NIGHTTIME_START or t <= NIGHTTIME_END


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _parse_timestamp(raw: str) -> Optional[datetime]:
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def _parse_bed_exits(events: list[dict]) -> list[BedExitEvent]:
    exits = []
    for e in events:
        if e.get("event_type") != "bed_exit":
            continue
        ts = _parse_timestamp(e.get("timestamp", ""))
        if ts is None:
            continue
        duration = e.get("duration_minutes")
        exits.append(BedExitEvent(timestamp=ts, duration_minutes=duration))
    return exits


def _parse_tossing(events: list[dict]) -> list[TossingEvent]:
    tossing = []
    for e in events:
        if e.get("event_type") != "tossing_and_turning":
            continue
        ts = _parse_timestamp(e.get("timestamp", ""))
        if ts is None:
            continue
        duration = e.get("duration_minutes", 0)
        tossing.append(TossingEvent(timestamp=ts, duration_minutes=duration))
    return tossing


# ---------------------------------------------------------------------------
# Baseline deviation translation
# ---------------------------------------------------------------------------

def _describe_baseline_deviation(baseline_comparison: Optional[dict]) -> str:
    if not baseline_comparison:
        return ""

    sigma = baseline_comparison.get("standard_deviations_above_mean")
    if sigma is None:
        return ""

    if sigma >= 3:
        return "this is quite a bit more than what we usually see"
    if sigma >= 2:
        return "a bit more than what's been typical lately"
    if sigma >= 1:
        return "somewhat above the usual pattern"
    return ""


# ---------------------------------------------------------------------------
# Warm language generator
# ---------------------------------------------------------------------------

def _build_warm_description(summary: SleepPatternSummary) -> str:
    """
    Generate a starting-point warm description of the sleep pattern.
    The L2 skill should refine this with HPA RAG content before output.
    """
    parts = []

    # Bed exits
    if summary.nighttime_bed_exits >= 6:
        parts.append("nighttime activity has been noticeably higher over the past few nights")
    elif summary.nighttime_bed_exits >= 4:
        parts.append("nighttime activity was a bit more frequent than usual")
    elif summary.nighttime_bed_exits >= 2:
        parts.append("there were a couple of brief moments of nighttime activity")

    # Tossing
    if summary.tossing_events > 0:
        if summary.avg_tossing_minutes_per_night >= 45:
            parts.append("the elder seemed to have some difficulty settling in")
        elif summary.avg_tossing_minutes_per_night >= 30:
            parts.append("over the past couple of nights, rest seemed a little lighter than usual")

    # Baseline deviation
    if summary.baseline_deviation_description:
        parts.append(summary.baseline_deviation_description)

    if not parts:
        return "sleep patterns this week looked within the usual range"

    return "; ".join(parts)


# ---------------------------------------------------------------------------
# Main analysis function
# ---------------------------------------------------------------------------

def analyze_sleep_events(
    triggering_events: list[dict],
    baseline_comparison: Optional[dict] = None,
) -> SleepPatternSummary:
    """
    Analyze raw sensor events into a structured sleep pattern summary.

    Args:
        triggering_events: List of sensor event dicts from the L1 routing payload.
        baseline_comparison: Optional dict with baseline deviation info.

    Returns:
        SleepPatternSummary with counts, timing, and warm description.
    """
    summary = SleepPatternSummary()

    bed_exits = _parse_bed_exits(triggering_events)
    tossing_events = _parse_tossing(triggering_events)

    # --- Bed exits ---
    summary.total_bed_exits = len(bed_exits)
    nighttime_exits = [e for e in bed_exits if _is_nighttime(e.timestamp)]
    summary.nighttime_bed_exits = len(nighttime_exits)

    if nighttime_exits:
        hours = [e.timestamp.hour for e in nighttime_exits]
        summary.earliest_exit_hour = min(hours)
        summary.latest_exit_hour = max(hours)
        summary.distinct_calendar_days = {e.timestamp.date() for e in nighttime_exits}
        summary.nights_with_activity = len(summary.distinct_calendar_days)

    # --- Tossing ---
    summary.tossing_events = len(tossing_events)
    if tossing_events:
        summary.total_tossing_minutes = sum(e.duration_minutes for e in tossing_events)
        summary.avg_tossing_minutes_per_night = (
            summary.total_tossing_minutes / summary.tossing_events
        )
        tossing_days = {e.timestamp.date() for e in tossing_events}
        summary.distinct_calendar_days |= tossing_days

    # --- Multi-day trend ---
    summary.is_multi_day_trend = len(summary.distinct_calendar_days) >= 2

    # --- Baseline ---
    summary.baseline_deviation_description = _describe_baseline_deviation(baseline_comparison)

    # --- Warm description ---
    summary.warm_description = _build_warm_description(summary)

    return summary


# ---------------------------------------------------------------------------
# CLI for testing
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    sample_events = [
        {"event_type": "bed_exit", "timestamp": "2026-03-17T01:23:00"},
        {"event_type": "bed_exit", "timestamp": "2026-03-17T04:10:00"},
        {"event_type": "bed_exit", "timestamp": "2026-03-18T02:45:00"},
        {"event_type": "tossing_and_turning", "timestamp": "2026-03-18T00:30:00", "duration_minutes": 35},
    ]

    sample_baseline = {"standard_deviations_above_mean": 2.1}

    result = analyze_sleep_events(sample_events, sample_baseline)
    print(f"Nighttime bed exits: {result.nighttime_bed_exits}")
    print(f"Nights with activity: {result.nights_with_activity}")
    print(f"Tossing events: {result.tossing_events}")
    print(f"Avg tossing (min): {result.avg_tossing_minutes_per_night:.1f}")
    print(f"Multi-day trend: {result.is_multi_day_trend}")
    print(f"Baseline deviation: {result.baseline_deviation_description}")
    print(f"Warm description: {result.warm_description}")
