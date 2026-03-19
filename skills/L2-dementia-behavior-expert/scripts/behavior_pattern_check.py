"""
Behavior Pattern Checker

Utility script for the Dementia Behavior Expert skill.
Processes cognitive-related sensor events (wandering, inactivity, appliance
anomalies) into structured behavioral pattern summaries for the L2 skill.

This script has the HIGHEST SaMD risk of any utility in the system.
Output is internal only — it informs warm family language but must never
be exposed directly. No clinical terminology appears anywhere in this module.

Input:  Raw JSON sensor events from L1 routing payload
Output: Structured BehaviorSummary

Usage:
    from skills.L2_dementia_behavior_expert.scripts.behavior_pattern_check import analyze_behavior_events
    summary = analyze_behavior_events(triggering_events, baseline_comparison)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time
from typing import Optional


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class NighttimeMovementEvent:
    """Movement event outside the usual bedroom-to-bathroom path, overnight."""
    timestamp: datetime
    area: Optional[str] = None    # "living_room", "kitchen", "entrance", etc.


@dataclass
class InactivityEvent:
    timestamp: datetime
    duration_hours: float
    time_of_day: str = ""   # "morning", "afternoon", "evening"


@dataclass
class ApplianceEvent:
    timestamp: datetime
    appliance_context: Optional[str] = None   # "kitchen", "stove", "kettle"
    duration_label: str = ""   # "anomalous_long", "normal"
    duration_minutes: Optional[int] = None


@dataclass
class BehaviorSummary:
    """Structured summary of cognitive-domain behavioral patterns."""

    # Nighttime movement
    nighttime_movement_events: int = 0
    nighttime_movement_days: set = field(default_factory=set)
    nighttime_areas: list[str] = field(default_factory=list)

    # Daytime inactivity
    long_inactivity_events: int = 0
    max_inactivity_hours: float = 0.0
    avg_inactivity_hours: float = 0.0
    inactivity_days: set = field(default_factory=set)

    # Appliance anomalies
    appliance_anomaly_events: int = 0
    appliance_contexts: list[str] = field(default_factory=list)
    appliance_anomaly_days: set = field(default_factory=set)

    # Multi-domain
    distinct_calendar_days: set = field(default_factory=set)
    is_multi_day_trend: bool = False
    active_domains: list[str] = field(default_factory=list)   # which types are present
    is_multi_domain: bool = False    # 2+ domain types in same period

    # Internal calibration signal (never expose to families)
    internal_attention_weight: str = "standard"   # "standard" or "elevated"

    # Warm language
    warm_description: str = ""


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OVERNIGHT_START = time(23, 0)
OVERNIGHT_END = time(5, 0)
DAYTIME_INACTIVITY_THRESHOLD_HOURS = 4.0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_timestamp(raw: str) -> Optional[datetime]:
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def _is_overnight(dt: datetime) -> bool:
    t = dt.time()
    return t >= OVERNIGHT_START or t <= OVERNIGHT_END


def _time_of_day_label(dt: datetime) -> str:
    h = dt.hour
    if 6 <= h < 12:
        return "morning"
    if 12 <= h < 17:
        return "afternoon"
    if 17 <= h < 22:
        return "evening"
    return "night"


def _parse_nighttime_movements(events: list[dict]) -> list[NighttimeMovementEvent]:
    """Extract wandering/movement events that occur during overnight hours."""
    result = []
    for e in events:
        if e.get("event_type") not in ("wandering", "movement"):
            continue
        ts = _parse_timestamp(e.get("timestamp", ""))
        if ts is None or not _is_overnight(ts):
            continue
        result.append(NighttimeMovementEvent(
            timestamp=ts,
            area=e.get("area") or e.get("location"),
        ))
    return result


def _parse_inactivity(events: list[dict]) -> list[InactivityEvent]:
    result = []
    for e in events:
        if e.get("event_type") != "inactivity":
            continue
        ts = _parse_timestamp(e.get("timestamp", ""))
        if ts is None:
            continue
        duration_h = e.get("duration_hours", 0.0)
        if float(duration_h) < DAYTIME_INACTIVITY_THRESHOLD_HOURS:
            continue
        result.append(InactivityEvent(
            timestamp=ts,
            duration_hours=float(duration_h),
            time_of_day=_time_of_day_label(ts),
        ))
    return result


def _parse_appliance_anomalies(events: list[dict]) -> list[ApplianceEvent]:
    result = []
    for e in events:
        if e.get("event_type") != "appliance_interaction":
            continue
        if e.get("duration_label") != "anomalous_long" and not e.get("is_anomalous"):
            continue
        ts = _parse_timestamp(e.get("timestamp", ""))
        if ts is None:
            continue
        result.append(ApplianceEvent(
            timestamp=ts,
            appliance_context=e.get("appliance_context") or e.get("location"),
            duration_label=e.get("duration_label", "anomalous_long"),
            duration_minutes=e.get("duration_minutes"),
        ))
    return result


# ---------------------------------------------------------------------------
# Internal attention weight (never exposed to families)
# ---------------------------------------------------------------------------

def _compute_attention_weight(summary: BehaviorSummary) -> str:
    """
    Internal calibration — informs L2 skill's internal reasoning depth.
    Never referenced in family output.

    Elevated conditions (from ME-BYO calibration framework):
    - Any nighttime movement event
    - Multi-domain convergence (2+ domain types in same period)
    """
    if summary.nighttime_movement_events > 0:
        return "elevated"
    if summary.is_multi_domain:
        return "elevated"
    return "standard"


# ---------------------------------------------------------------------------
# Warm language
# ---------------------------------------------------------------------------

def _build_warm_description(summary: BehaviorSummary) -> str:
    """
    Generate a starting-point warm description.
    The L2 skill should layer HPA RAG content before producing output.

    CRITICAL: No clinical terms. No condition names. Pure observation language.
    """
    parts = []

    # Nighttime movement — highest priority, most sensitive
    if summary.nighttime_movement_events > 0:
        if summary.nighttime_movement_days and len(summary.nighttime_movement_days) >= 2:
            parts.append(
                "over the past few nights, there were some moments of overnight activity "
                "that went a bit beyond the usual brief bathroom trip"
            )
        else:
            parts.append(
                "the sensor noticed some overnight movement that was a little different "
                "from the usual pattern"
            )

    # Daytime inactivity
    if summary.long_inactivity_events > 0:
        if summary.avg_inactivity_hours >= 6:
            parts.append(
                "the past few days have been quite a bit quieter than usual — "
                "long stretches of stillness during the day"
            )
        else:
            parts.append(
                "there were some longer quiet stretches during the day — "
                "less movement around the home than the usual pattern"
            )

    # Appliance anomalies
    if summary.appliance_anomaly_events > 0:
        ctx = summary.appliance_contexts[0] if summary.appliance_contexts else "kitchen"
        parts.append(
            f"the sensor noticed an extended period of activity in the {ctx} area "
            f"that was a little longer than the usual pattern"
        )

    if not parts:
        return "daily patterns this period looked within the familiar range"

    return "; ".join(parts)


# ---------------------------------------------------------------------------
# Main analysis function
# ---------------------------------------------------------------------------

def analyze_behavior_events(
    triggering_events: list[dict],
    baseline_comparison: Optional[dict] = None,
) -> BehaviorSummary:
    """
    Analyze raw sensor events into a structured behavioral pattern summary.

    Args:
        triggering_events: List of sensor event dicts from the L1 routing payload.
        baseline_comparison: Optional dict with baseline deviation context.

    Returns:
        BehaviorSummary with multi-domain assessment and warm description.
    """
    summary = BehaviorSummary()

    nighttime = _parse_nighttime_movements(triggering_events)
    inactivity = _parse_inactivity(triggering_events)
    appliance = _parse_appliance_anomalies(triggering_events)

    # --- Nighttime movement ---
    summary.nighttime_movement_events = len(nighttime)
    if nighttime:
        summary.nighttime_movement_days = {e.timestamp.date() for e in nighttime}
        summary.nighttime_areas = [e.area for e in nighttime if e.area]
        summary.distinct_calendar_days |= summary.nighttime_movement_days
        summary.active_domains.append("nighttime_movement")

    # --- Inactivity ---
    summary.long_inactivity_events = len(inactivity)
    if inactivity:
        durations = [e.duration_hours for e in inactivity]
        summary.max_inactivity_hours = max(durations)
        summary.avg_inactivity_hours = sum(durations) / len(durations)
        summary.inactivity_days = {e.timestamp.date() for e in inactivity}
        summary.distinct_calendar_days |= summary.inactivity_days
        summary.active_domains.append("inactivity")

    # --- Appliance ---
    summary.appliance_anomaly_events = len(appliance)
    if appliance:
        summary.appliance_contexts = [e.appliance_context for e in appliance if e.appliance_context]
        summary.appliance_anomaly_days = {e.timestamp.date() for e in appliance}
        summary.distinct_calendar_days |= summary.appliance_anomaly_days
        summary.active_domains.append("appliance")

    # --- Multi-day and multi-domain ---
    summary.is_multi_day_trend = len(summary.distinct_calendar_days) >= 2
    summary.is_multi_domain = len(summary.active_domains) >= 2

    # --- Internal calibration ---
    summary.internal_attention_weight = _compute_attention_weight(summary)

    # --- Warm language ---
    summary.warm_description = _build_warm_description(summary)

    return summary


# ---------------------------------------------------------------------------
# CLI for testing
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sample_events = [
        {"event_type": "wandering", "timestamp": "2026-03-17T02:15:00", "area": "living_room"},
        {"event_type": "wandering", "timestamp": "2026-03-18T03:00:00", "area": "kitchen"},
        {"event_type": "inactivity", "timestamp": "2026-03-17T14:00:00", "duration_hours": 4.5},
        {
            "event_type": "appliance_interaction",
            "timestamp": "2026-03-18T11:30:00",
            "appliance_context": "kitchen",
            "duration_label": "anomalous_long",
            "duration_minutes": 45,
        },
    ]

    result = analyze_behavior_events(sample_events)
    print(f"Nighttime movement events: {result.nighttime_movement_events}")
    print(f"Nighttime movement days: {result.nighttime_movement_days}")
    print(f"Long inactivity events: {result.long_inactivity_events}")
    print(f"Appliance anomalies: {result.appliance_anomaly_events}")
    print(f"Multi-domain: {result.is_multi_domain}")
    print(f"Active domains: {result.active_domains}")
    print(f"Internal attention weight: {result.internal_attention_weight}")
    print(f"Multi-day trend: {result.is_multi_day_trend}")
    print(f"Warm description: {result.warm_description}")
