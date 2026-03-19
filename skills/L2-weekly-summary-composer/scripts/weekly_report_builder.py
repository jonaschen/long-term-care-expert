"""
Weekly Report Builder

Utility script for the Weekly Summary Composer skill.
Aggregates L2 observation packages from the past 7 days into a structured
input for the weekly LINE report. Handles deduplication, section ordering,
and tone calibration based on observation severity.

Input:  Weekly aggregation payload from L1
Output: WeeklyReportContext — structured input for the L2 composer skill

Usage:
    from skills.L2_weekly_summary_composer.scripts.weekly_report_builder import build_weekly_context
    context = build_weekly_context(weekly_payload)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Enums and constants
# ---------------------------------------------------------------------------

class WeekType(str, Enum):
    QUIET = "quiet"                     # No anomalies — celebrate stability
    MILD_OBSERVATION = "mild"           # 1 mild observation
    MULTIPLE_OBSERVATIONS = "multiple"  # 2+ observations or sustained pattern
    POST_ALERT = "post_alert"           # Following an attention_needed week


SECTION_ORDER = ["sleep", "mobility", "cognitive_routine", "lifestyle"]


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class ObservationSection:
    domain: str               # "sleep", "mobility", "cognitive_routine", "lifestyle"
    has_content: bool = False
    urgency: str = "routine"  # "routine" or "attention_needed"
    summary_text: str = ""    # Warm description from L2 skill
    is_new: bool = True       # False if same pattern was reported last week


@dataclass
class WeeklyReportContext:
    """Structured context for the Weekly Summary Composer skill."""

    # Period
    week_start: Optional[date] = None
    week_end: Optional[date] = None
    user_id: str = ""

    # Week classification
    week_type: WeekType = WeekType.QUIET
    has_prior_week_summary: bool = False
    prior_week_had_alert: bool = False

    # Sections (ordered by SECTION_ORDER)
    sections: list[ObservationSection] = field(default_factory=list)

    # Deduplication
    daily_reports_sent: int = 0
    domains_already_reported_this_week: list[str] = field(default_factory=list)

    # Tone guidance
    lead_with_positive: bool = True
    closing_question_hint: str = ""   # Hint for which question type fits this week

    # Composer notes (internal only)
    composer_notes: str = ""


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _parse_date(raw: str) -> Optional[date]:
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def _extract_sleep_section(payload: dict) -> ObservationSection:
    sleep_data = payload.get("sleep_observations") or {}
    if not sleep_data:
        return ObservationSection(domain="sleep", has_content=False)

    return ObservationSection(
        domain="sleep",
        has_content=True,
        urgency=sleep_data.get("urgency_level", "routine"),
        summary_text=sleep_data.get("behavior_summary", ""),
        is_new=sleep_data.get("is_new_pattern", True),
    )


def _extract_mobility_section(payload: dict) -> ObservationSection:
    mob_data = payload.get("mobility_observations") or {}
    if not mob_data:
        return ObservationSection(domain="mobility", has_content=False)

    return ObservationSection(
        domain="mobility",
        has_content=True,
        urgency=mob_data.get("urgency_level", "routine"),
        summary_text=mob_data.get("behavior_summary", ""),
        is_new=mob_data.get("is_new_pattern", True),
    )


def _extract_cognitive_section(payload: dict) -> ObservationSection:
    cog_data = payload.get("cognitive_observations") or {}
    if not cog_data:
        return ObservationSection(domain="cognitive_routine", has_content=False)

    return ObservationSection(
        domain="cognitive_routine",
        has_content=True,
        urgency=cog_data.get("urgency_level", "routine"),
        summary_text=cog_data.get("behavior_summary", ""),
        is_new=cog_data.get("is_new_pattern", True),
    )


def _extract_lifestyle_section(payload: dict) -> ObservationSection:
    lifestyle_data = payload.get("lifestyle_data") or {}
    if not lifestyle_data:
        return ObservationSection(domain="lifestyle", has_content=False)

    # Lifestyle section is always "routine" urgency
    return ObservationSection(
        domain="lifestyle",
        has_content=True,
        urgency="routine",
        summary_text=lifestyle_data.get("observation_summary", ""),
        is_new=True,
    )


# ---------------------------------------------------------------------------
# Week type classifier
# ---------------------------------------------------------------------------

def _classify_week(
    sections: list[ObservationSection],
    prior_week_had_alert: bool,
) -> WeekType:
    if prior_week_had_alert:
        return WeekType.POST_ALERT

    active_sections = [s for s in sections if s.has_content]

    if not active_sections:
        return WeekType.QUIET

    attention_sections = [s for s in active_sections if s.urgency == "attention_needed"]
    if attention_sections or len(active_sections) >= 2:
        return WeekType.MULTIPLE_OBSERVATIONS

    return WeekType.MILD_OBSERVATION


# ---------------------------------------------------------------------------
# Closing question hint
# ---------------------------------------------------------------------------

def _choose_closing_question_hint(week_type: WeekType, sections: list[ObservationSection]) -> str:
    active_domains = [s.domain for s in sections if s.has_content]

    if week_type == WeekType.QUIET:
        return "activity_focused"   # Celebrate the week; invite sharing a nice moment

    if "cognitive_routine" in active_domains:
        return "relationship_focused"   # Invite family's own observation

    if "mobility" in active_domains:
        return "environment_focused"    # Home setup check-in

    if "sleep" in active_domains:
        return "routine_focused"        # Sleep routine inquiry

    return "routine_focused"


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

def _find_already_reported_domains(payload: dict) -> list[str]:
    """
    Identify which domains already had a standalone daily report this week
    so the weekly report does not duplicate the same content.
    """
    reports = payload.get("daily_reports_sent") or []
    domains = []
    for r in reports:
        source = r.get("source_skill", "")
        if "sleep" in source:
            domains.append("sleep")
        elif "mobility" in source or "fall" in source:
            domains.append("mobility")
        elif "dementia" in source or "cognitive" in source:
            domains.append("cognitive_routine")
    return list(set(domains))


# ---------------------------------------------------------------------------
# Composer notes generator
# ---------------------------------------------------------------------------

def _build_composer_notes(context: WeeklyReportContext) -> str:
    notes = []

    if context.week_type == WeekType.QUIET:
        notes.append("Lead with celebration of a stable week. Keep warm and brief.")

    if context.prior_week_had_alert:
        notes.append(
            "Reference last week's observation gently — frame this week as a follow-up check."
        )

    if context.domains_already_reported_this_week:
        already = ", ".join(context.domains_already_reported_this_week)
        notes.append(
            f"Domains already covered in daily reports this week: {already}. "
            "Summarize briefly — don't repeat the full daily insight."
        )

    attention_domains = [
        s.domain for s in context.sections
        if s.has_content and s.urgency == "attention_needed"
    ]
    if attention_domains:
        notes.append(
            f"Attention-level observations in: {', '.join(attention_domains)}. "
            "Include gentle professional consultation language for these domains."
        )

    return " | ".join(notes) if notes else "Standard weekly composition."


# ---------------------------------------------------------------------------
# Main function
# ---------------------------------------------------------------------------

def build_weekly_context(weekly_payload: dict) -> WeeklyReportContext:
    """
    Build a structured WeeklyReportContext from the L1 weekly aggregation payload.

    Args:
        weekly_payload: Dict matching the weekly aggregation schema.

    Returns:
        WeeklyReportContext for the Weekly Summary Composer skill.
    """
    context = WeeklyReportContext()

    # Period
    context.user_id = weekly_payload.get("user_id", "")
    context.week_start = _parse_date(weekly_payload.get("week_start", ""))
    context.week_end = _parse_date(weekly_payload.get("week_end", ""))

    # Prior week context
    prior = weekly_payload.get("prior_weekly_summary") or {}
    context.has_prior_week_summary = bool(prior)
    context.prior_week_had_alert = prior.get("had_attention_level_report", False)

    # Extract sections
    sections = [
        _extract_sleep_section(weekly_payload),
        _extract_mobility_section(weekly_payload),
        _extract_cognitive_section(weekly_payload),
        _extract_lifestyle_section(weekly_payload),
    ]
    context.sections = sections

    # Deduplication
    context.daily_reports_sent = len(weekly_payload.get("daily_reports_sent") or [])
    context.domains_already_reported_this_week = _find_already_reported_domains(weekly_payload)

    # Classification
    context.week_type = _classify_week(sections, context.prior_week_had_alert)
    context.lead_with_positive = context.week_type != WeekType.POST_ALERT

    # Closing question
    context.closing_question_hint = _choose_closing_question_hint(context.week_type, sections)

    # Composer notes
    context.composer_notes = _build_composer_notes(context)

    return context


# ---------------------------------------------------------------------------
# CLI for testing
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sample_payload = {
        "user_id": "elder_001",
        "week_start": "2026-03-10",
        "week_end": "2026-03-16",
        "sleep_observations": {
            "urgency_level": "routine",
            "behavior_summary": "There were a couple of brief moments of nighttime activity over a few nights.",
            "is_new_pattern": True,
        },
        "mobility_observations": None,
        "cognitive_observations": None,
        "lifestyle_data": {
            "observation_summary": "Activity levels this week were close to the usual pattern.",
        },
        "prior_weekly_summary": {
            "had_attention_level_report": False,
        },
        "daily_reports_sent": [
            {"source_skill": "sleep-pattern-expert"},
        ],
    }

    ctx = build_weekly_context(sample_payload)
    print(f"Week type: {ctx.week_type.value}")
    print(f"Active sections: {[s.domain for s in ctx.sections if s.has_content]}")
    print(f"Already reported: {ctx.domains_already_reported_this_week}")
    print(f"Lead with positive: {ctx.lead_with_positive}")
    print(f"Closing question hint: {ctx.closing_question_hint}")
    print(f"Composer notes: {ctx.composer_notes}")
