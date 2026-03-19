"""
Gait Anomaly Detector

Utility script for the Mobility and Fall Risk Expert skill.
Processes walking pace, rise attempt, and posture change events into
structured mobility trend summaries for consumption by the L2 skill.

Input:  Raw JSON sensor events from L1 routing payload
Output: Structured MobilitySummary dict

Usage:
    from skills.L2_mobility_fall_expert.scripts.gait_anomaly_detector import analyze_mobility_events
    summary = analyze_mobility_events(triggering_events, baseline_comparison)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class WalkingEvent:
    timestamp: datetime
    pace_label: str            # "anomalous_slow", "normal", etc.
    percent_below_baseline: Optional[float] = None


@dataclass
class RiseAttemptEvent:
    timestamp: datetime
    result: str                # "fail", "success"
    location: Optional[str] = None   # "chair", "bed", etc.


@dataclass
class PostureDropEvent:
    timestamp: datetime
    severity: Optional[str] = None   # "sudden", "gradual"


@dataclass
class MobilitySummary:
    """Structured summary of mobility patterns for L2 skill consumption."""

    # Gait
    slow_walk_events: int = 0
    avg_pace_reduction_pct: float = 0.0   # average % below baseline
    max_pace_reduction_pct: float = 0.0
    gait_days_observed: set = field(default_factory=set)

    # Rising
    total_rise_attempts: int = 0
    failed_rise_attempts: int = 0
    rise_fail_rate: float = 0.0          # 0.0–1.0
    consecutive_fail_days: int = 0

    # Posture drops (urgent)
    posture_drops: int = 0
    has_urgent_posture_drop: bool = False

    # Multi-day
    distinct_calendar_days: set = field(default_factory=set)
    is_multi_day_trend: bool = False

    # Urgency
    urgency_level: str = "routine"       # "routine" or "attention_needed"

    # Baseline
    baseline_deviation_description: str = ""

    # Warm language
    warm_description: str = ""
    urgency_note: str = ""


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SLOW_GAIT_THRESHOLD_PCT = 30.0   # % below baseline to flag as anomalous


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


def _parse_walking_events(events: list[dict]) -> list[WalkingEvent]:
    result = []
    for e in events:
        if e.get("event_type") != "walking":
            continue
        ts = _parse_timestamp(e.get("timestamp", ""))
        if ts is None:
            continue
        pace_label = e.get("pace_label", "")
        pct_below = e.get("percent_below_baseline")
        result.append(WalkingEvent(
            timestamp=ts,
            pace_label=pace_label,
            percent_below_baseline=float(pct_below) if pct_below is not None else None,
        ))
    return result


def _parse_rise_attempts(events: list[dict]) -> list[RiseAttemptEvent]:
    result = []
    for e in events:
        if e.get("event_type") != "rise_attempt":
            continue
        ts = _parse_timestamp(e.get("timestamp", ""))
        if ts is None:
            continue
        result.append(RiseAttemptEvent(
            timestamp=ts,
            result=e.get("result", ""),
            location=e.get("location"),
        ))
    return result


def _parse_posture_drops(events: list[dict]) -> list[PostureDropEvent]:
    result = []
    for e in events:
        if e.get("event_type") != "posture_change":
            continue
        if e.get("posture_type") != "sudden_drop":
            continue
        ts = _parse_timestamp(e.get("timestamp", ""))
        if ts is None:
            continue
        result.append(PostureDropEvent(
            timestamp=ts,
            severity=e.get("severity"),
        ))
    return result


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
        return "somewhat different from the usual pattern"
    return ""


# ---------------------------------------------------------------------------
# Warm language generator
# ---------------------------------------------------------------------------

def _build_warm_description(summary: MobilitySummary) -> str:
    parts = []

    if summary.posture_drops > 0:
        parts.append(
            "the sensor noticed a sudden change in posture — the family should check "
            "on the elder to make sure everything is okay"
        )

    if summary.slow_walk_events > 0:
        if summary.max_pace_reduction_pct >= 40:
            parts.append("movement through the home has been noticeably slower than the usual pace")
        elif summary.max_pace_reduction_pct >= 30:
            parts.append("the sensor noticed that movement was a little slower than usual")

    if summary.failed_rise_attempts >= 2:
        parts.append(
            "getting up from a seated position seemed to take more effort than usual "
            "on a few occasions"
        )
    elif summary.failed_rise_attempts == 1:
        parts.append("there was one moment where rising from a seated position seemed a bit effortful")

    if summary.baseline_deviation_description:
        parts.append(summary.baseline_deviation_description)

    if not parts:
        return "movement patterns this period looked within the familiar range"

    return "; ".join(parts)


def _build_urgency_note(summary: MobilitySummary) -> str:
    if summary.has_urgent_posture_drop:
        return (
            "A sudden posture change was detected — please check on the elder to confirm "
            "they are safe. The sensor cannot confirm whether a fall occurred."
        )
    return ""


# ---------------------------------------------------------------------------
# Consecutive fail day counter
# ---------------------------------------------------------------------------

def _count_consecutive_fail_days(rise_events: list[RiseAttemptEvent]) -> int:
    """Count the number of distinct calendar days with at least one failed rise attempt."""
    fail_days = {e.timestamp.date() for e in rise_events if e.result == "fail"}
    return len(fail_days)


# ---------------------------------------------------------------------------
# Main analysis function
# ---------------------------------------------------------------------------

def analyze_mobility_events(
    triggering_events: list[dict],
    baseline_comparison: Optional[dict] = None,
) -> MobilitySummary:
    """
    Analyze raw sensor events into a structured mobility pattern summary.

    Args:
        triggering_events: List of sensor event dicts from the L1 routing payload.
        baseline_comparison: Optional dict with baseline deviation info.

    Returns:
        MobilitySummary with counts, urgency level, and warm description.
    """
    summary = MobilitySummary()

    walking = _parse_walking_events(triggering_events)
    rising = _parse_rise_attempts(triggering_events)
    posture_drops = _parse_posture_drops(triggering_events)

    # --- Gait ---
    slow_walks = [
        w for w in walking
        if w.pace_label == "anomalous_slow"
        or (w.percent_below_baseline is not None and w.percent_below_baseline >= SLOW_GAIT_THRESHOLD_PCT)
    ]
    summary.slow_walk_events = len(slow_walks)

    if slow_walks:
        reductions = [w.percent_below_baseline for w in slow_walks if w.percent_below_baseline is not None]
        if reductions:
            summary.avg_pace_reduction_pct = sum(reductions) / len(reductions)
            summary.max_pace_reduction_pct = max(reductions)
        summary.gait_days_observed = {w.timestamp.date() for w in slow_walks}
        summary.distinct_calendar_days |= summary.gait_days_observed

    # --- Rising ---
    summary.total_rise_attempts = len(rising)
    failed = [r for r in rising if r.result == "fail"]
    summary.failed_rise_attempts = len(failed)
    summary.rise_fail_rate = (
        summary.failed_rise_attempts / summary.total_rise_attempts
        if summary.total_rise_attempts > 0 else 0.0
    )
    summary.consecutive_fail_days = _count_consecutive_fail_days(rising)
    summary.distinct_calendar_days |= {r.timestamp.date() for r in rising}

    # --- Posture drops ---
    summary.posture_drops = len(posture_drops)
    summary.has_urgent_posture_drop = summary.posture_drops > 0
    summary.distinct_calendar_days |= {p.timestamp.date() for p in posture_drops}

    # --- Multi-day trend ---
    summary.is_multi_day_trend = len(summary.distinct_calendar_days) >= 2

    # --- Urgency ---
    if summary.has_urgent_posture_drop:
        summary.urgency_level = "attention_needed"
    elif summary.consecutive_fail_days >= 2 or summary.slow_walk_events >= 3:
        summary.urgency_level = "attention_needed"
    else:
        summary.urgency_level = "routine"

    # --- Baseline ---
    summary.baseline_deviation_description = _describe_baseline_deviation(baseline_comparison)

    # --- Language ---
    summary.warm_description = _build_warm_description(summary)
    summary.urgency_note = _build_urgency_note(summary)

    return summary


# ---------------------------------------------------------------------------
# CLI for testing
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sample_events = [
        {"event_type": "walking", "timestamp": "2026-03-17T09:00:00",
         "pace_label": "anomalous_slow", "percent_below_baseline": 35.0},
        {"event_type": "walking", "timestamp": "2026-03-18T10:30:00",
         "pace_label": "anomalous_slow", "percent_below_baseline": 32.0},
        {"event_type": "rise_attempt", "timestamp": "2026-03-17T08:00:00", "result": "fail"},
        {"event_type": "rise_attempt", "timestamp": "2026-03-18T08:15:00", "result": "fail"},
    ]

    sample_baseline = {"standard_deviations_above_mean": 2.5}

    result = analyze_mobility_events(sample_events, sample_baseline)
    print(f"Slow walk events: {result.slow_walk_events}")
    print(f"Max pace reduction: {result.max_pace_reduction_pct:.1f}%")
    print(f"Failed rise attempts: {result.failed_rise_attempts}")
    print(f"Consecutive fail days: {result.consecutive_fail_days}")
    print(f"Posture drops: {result.posture_drops}")
    print(f"Urgency level: {result.urgency_level}")
    print(f"Multi-day trend: {result.is_multi_day_trend}")
    print(f"Warm description: {result.warm_description}")
    if result.urgency_note:
        print(f"Urgency note: {result.urgency_note}")
