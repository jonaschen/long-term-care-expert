"""
Long-Term Care Expert — LINE Report Generator

Packages L2 expert output into LINE Flex Message JSON and auto-injects the
mandatory non-SaMD legal disclaimer.  This module is the **only** valid
output channel for L2 skills.

Before packaging, every text field is scanned against the regulatory
blacklist (``compliance/blacklist_terms.json``).  If a prohibited term or
pattern is found the report is **rejected** — no partial output is emitted.

Public API
----------
generate_line_report_impl(
    insight_title, behavior_summary, hpa_suggestion,
    urgency_level, report_type, source_skill)
    → dict   (LINE Flex Message structure with metadata)
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_BLACKLIST_PATH = _PROJECT_ROOT / "compliance" / "blacklist_terms.json"
_DISCLAIMER_PATH = _PROJECT_ROOT / "compliance" / "disclaimer_template.md"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_URGENCY_LEVELS = frozenset({"routine", "attention_needed"})
VALID_REPORT_TYPES = frozenset({"daily_insight", "weekly_summary", "immediate_alert"})

# Hardcoded fallback if the file cannot be read at runtime.
_FALLBACK_DISCLAIMER = (
    "【系統聲明】本系統並非醫療器材（Non-SaMD）。所提供之資訊僅供居家環境"
    "安全改善及一般健康促進參考，不構成亦無法取代專業醫療診斷、治療計畫或"
    "臨床建議。如長輩出現任何身體不適或緊急狀況，請立即就醫或撥打119。"
)

# Visual styling per urgency level
_URGENCY_STYLES: dict[str, dict[str, str]] = {
    "routine": {
        "bg_color": "#F5F7FA",
        "title_color": "#1A1A1A",
        "accent_color": "#27AE60",
    },
    "attention_needed": {
        "bg_color": "#FFF3F3",
        "title_color": "#C0392B",
        "accent_color": "#E74C3C",
    },
}

# ---------------------------------------------------------------------------
# Blacklist loader
# ---------------------------------------------------------------------------


def _load_blacklist() -> tuple[list[str], list[re.Pattern[str]]]:
    """Load prohibited terms and compiled regex patterns from the
    compliance blacklist file.

    Returns
    -------
    (terms, patterns)
        *terms* is a list of lowercase prohibited strings.
        *patterns* is a list of compiled regex objects.
    """
    if not _BLACKLIST_PATH.exists():
        return [], []

    with _BLACKLIST_PATH.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    terms: list[str] = [t.lower() for t in data.get("prohibited_terms", [])]
    patterns: list[re.Pattern[str]] = []
    for pat_str in data.get("prohibited_patterns", []):
        try:
            patterns.append(re.compile(pat_str, re.IGNORECASE))
        except re.error:
            pass  # skip malformed patterns
    return terms, patterns


def _scan_text(text: str, terms: list[str], patterns: list[re.Pattern[str]]) -> list[str]:
    """Return a list of violations found in *text*."""
    violations: list[str] = []
    lower = text.lower()
    for term in terms:
        if term in lower:
            violations.append(f"prohibited term: '{term}'")
    for pat in patterns:
        if pat.search(text):
            violations.append(f"prohibited pattern: '{pat.pattern}'")
    return violations


# ---------------------------------------------------------------------------
# Disclaimer loader
# ---------------------------------------------------------------------------


def _load_disclaimer() -> str:
    """Load the Chinese disclaimer from the template file.

    Falls back to the hardcoded version if the file is missing.
    """
    if not _DISCLAIMER_PATH.exists():
        return _FALLBACK_DISCLAIMER

    raw = _DISCLAIMER_PATH.read_text(encoding="utf-8")

    # Extract the Chinese section between "## 系統聲明" and the next heading
    chinese_start = raw.find("【系統聲明】")
    if chinese_start == -1:
        return _FALLBACK_DISCLAIMER

    chinese_section = raw[chinese_start:]
    # End at the next markdown heading or end of file
    next_heading = chinese_section.find("\n## ", 1)
    if next_heading != -1:
        chinese_section = chinese_section[:next_heading]

    return chinese_section.strip()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_line_report_impl(
    *,
    insight_title: str,
    behavior_summary: str,
    hpa_suggestion: str,
    urgency_level: str,
    report_type: str,
    source_skill: str = "",
) -> dict[str, Any]:
    """Build a LINE Flex Message payload with compliance checks.

    Parameters
    ----------
    insight_title:
        Warm, readable title (may include emoji).
    behavior_summary:
        Empathetic plain-language description of sensor observations.
    hpa_suggestion:
        One or two concrete suggestions drawn from HPA RAG results.
    urgency_level:
        ``"routine"`` or ``"attention_needed"``.
    report_type:
        ``"daily_insight"``, ``"weekly_summary"``, or ``"immediate_alert"``.
    source_skill:
        Name of the L2 skill that produced this insight.

    Returns
    -------
    dict
        A complete LINE Flex Message structure with ``metadata`` block.

    Raises
    ------
    ValueError
        If required fields are missing, enums are invalid, or the
        blacklist scan fails.
    """

    # --- Validate required fields -------------------------------------------
    if not insight_title or not insight_title.strip():
        raise ValueError("insight_title is required and cannot be empty")
    if not behavior_summary or not behavior_summary.strip():
        raise ValueError("behavior_summary is required and cannot be empty")
    if not hpa_suggestion or not hpa_suggestion.strip():
        raise ValueError("hpa_suggestion is required and cannot be empty")

    if urgency_level not in VALID_URGENCY_LEVELS:
        raise ValueError(
            f"Invalid urgency_level '{urgency_level}'. "
            f"Must be one of: {', '.join(sorted(VALID_URGENCY_LEVELS))}"
        )
    if report_type not in VALID_REPORT_TYPES:
        raise ValueError(
            f"Invalid report_type '{report_type}'. "
            f"Must be one of: {', '.join(sorted(VALID_REPORT_TYPES))}"
        )

    # --- Blacklist scan ------------------------------------------------------
    terms, patterns = _load_blacklist()
    all_violations: list[str] = []
    for field_name, field_text in [
        ("behavior_summary", behavior_summary),
        ("hpa_suggestion", hpa_suggestion),
        ("insight_title", insight_title),
    ]:
        violations = _scan_text(field_text, terms, patterns)
        all_violations.extend(f"{field_name}: {v}" for v in violations)

    if all_violations:
        raise ValueError(
            "Blacklist compliance scan FAILED — report rejected.\n"
            + "\n".join(f"  • {v}" for v in all_violations)
        )

    # --- Load disclaimer (cannot be removed) ---------------------------------
    disclaimer = _load_disclaimer()

    # --- Build LINE Flex Message ---------------------------------------------
    style = _URGENCY_STYLES[urgency_level]

    header_contents: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": insight_title,
            "weight": "bold",
            "size": "lg",
            "color": style["title_color"],
            "wrap": True,
        }
    ]

    # Urgent badge for immediate alerts
    if report_type == "immediate_alert":
        header_contents.insert(
            0,
            {
                "type": "text",
                "text": "⚠️ 需要關注",
                "size": "xs",
                "color": "#FFFFFF",
                "weight": "bold",
                "align": "center",
                "backgroundColor": style["accent_color"],
                "cornerRadius": "md",
                "margin": "none",
            },
        )

    flex_message: dict[str, Any] = {
        "type": "flex",
        "altText": insight_title,
        "contents": {
            "type": "bubble",
            "header": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": style["bg_color"],
                "paddingAll": "lg",
                "contents": header_contents,
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "paddingAll": "lg",
                "spacing": "md",
                "contents": [
                    {
                        "type": "text",
                        "text": behavior_summary,
                        "wrap": True,
                        "size": "sm",
                        "color": "#333333",
                    },
                    {"type": "separator", "margin": "md"},
                    {
                        "type": "text",
                        "text": f"💡 {hpa_suggestion}",
                        "wrap": True,
                        "size": "sm",
                        "color": "#555555",
                        "margin": "md",
                    },
                ],
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "paddingAll": "sm",
                "contents": [
                    {
                        "type": "text",
                        "text": disclaimer,
                        "wrap": True,
                        "size": "xxs",
                        "color": "#888888",
                    }
                ],
            },
        },
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_skill": source_skill,
            "urgency_level": urgency_level,
            "report_type": report_type,
            "compliance": {
                "blacklist_scan": "pass",
                "disclaimer_injected": True,
            },
        },
    }

    return flex_message
