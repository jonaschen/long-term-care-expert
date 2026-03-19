"""
Long-Term Care Expert — MCP Tool Server

FastMCP server exposing three tools for the L1/L2 agent skill system:

1. **search_hpa_guidelines** — RAG search on the HPA knowledge base
   (hybrid dense+sparse search via Qdrant).
2. **generate_line_report** — Package L2 insights into LINE Flex Message
   JSON with mandatory legal disclaimer injection.
3. **check_alert_history** — Query per-user alert history so the L1 router
   can suppress duplicates and prevent alert fatigue.

Run standalone::

    python -m tools.mcp_server          # as module
    python tools/mcp_server.py          # direct
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# Ensure the project root is importable so ``tools.*`` works when invoked
# directly (``python tools/mcp_server.py``).
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from tools.line_report_generator import generate_line_report_impl  # noqa: E402
from tools.alert_history_checker import (  # noqa: E402
    check_alert_history_impl,
    record_alert,
)

# ---------------------------------------------------------------------------
# FastMCP server instance
# ---------------------------------------------------------------------------

mcp = FastMCP("long-term-care-expert")

# ---------------------------------------------------------------------------
# Tool 1 — search_hpa_guidelines
# ---------------------------------------------------------------------------
# The full implementation lives in ``tools/hpa_rag_search.py`` and requires
# the Qdrant vector store + bge-m3 model to be initialised.  We wrap it here
# so the MCP server can still start even if the heavy ML dependencies are
# not available (graceful degradation).
# ---------------------------------------------------------------------------


@mcp.tool()
def search_hpa_guidelines(
    query: str,
    category: str,
    top_k: int = 3,
    exclude_medical: bool = True,
) -> str:
    """Retrieve relevant passages from Taiwan HPA official health-education
    handbooks.  Must be called whenever an L2 expert needs to provide
    caregiving, environmental, or lifestyle suggestions.

    **Never** use this tool to look up medical diagnoses, treatment
    protocols, drug information, or pharmaceuticals.

    Args:
        query: Natural-language query for semantic retrieval.
        category: One of: fall_prevention, dementia_care, sleep_hygiene,
                  chronic_disease_lifestyle, general_aging.
        top_k: Number of passages to return (default 3, max 5).
        exclude_medical: Must always be ``True``.  Filters out any
                         chunk tagged as medical content.
    """
    if not exclude_medical:
        return json.dumps(
            {"error": "exclude_medical must always be True (SaMD compliance)."},
            ensure_ascii=False,
        )

    try:
        from tools.hpa_rag_search import search_hpa_guidelines as hpa_search

        results = hpa_search(
            query=query,
            category=category,
            top_k=min(top_k, 5),
            exclude_medical=True,
        )
        return json.dumps(results, ensure_ascii=False, indent=2)
    except ImportError:
        return json.dumps(
            {
                "error": (
                    "RAG system not available.  "
                    "Run `python tools/embedding_pipeline.py --reset` "
                    "to initialise the vector store."
                ),
                "query": query,
                "category": category,
            },
            ensure_ascii=False,
            indent=2,
        )
    except Exception as exc:
        return json.dumps(
            {"error": f"search_hpa_guidelines failed: {exc}"},
            ensure_ascii=False,
            indent=2,
        )


# ---------------------------------------------------------------------------
# Tool 2 — generate_line_report
# ---------------------------------------------------------------------------


@mcp.tool()
def generate_line_report(
    insight_title: str,
    behavior_summary: str,
    hpa_suggestion: str,
    urgency_level: str,
    report_type: str,
    source_skill: str = "",
) -> str:
    """Package a completed insight into structured JSON for LINE Flex
    Message delivery.  Auto-injects the mandatory legal disclaimer.

    This is the **only** valid L2 output channel — no L2 skill may
    produce text output by any other means.

    Args:
        insight_title: Warm, human-readable title (may include emoji).
        behavior_summary: Empathetic description of sensor observations
                          using approved observational language.
        hpa_suggestion: 1–2 concrete suggestions sourced from RAG results.
        urgency_level: ``"routine"`` or ``"attention_needed"``.
        report_type: ``"daily_insight"``, ``"weekly_summary"``, or
                     ``"immediate_alert"``.
        source_skill: Name of the L2 skill that generated this report.
    """
    try:
        result = generate_line_report_impl(
            insight_title=insight_title,
            behavior_summary=behavior_summary,
            hpa_suggestion=hpa_suggestion,
            urgency_level=urgency_level,
            report_type=report_type,
            source_skill=source_skill,
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except ValueError as exc:
        return json.dumps(
            {"error": str(exc)},
            ensure_ascii=False,
            indent=2,
        )


# ---------------------------------------------------------------------------
# Tool 3 — check_alert_history
# ---------------------------------------------------------------------------


@mcp.tool()
def check_alert_history(
    user_id: str,
    event_category: str,
    hours_lookback: int = 48,
) -> str:
    """Query past alert history for a user and event class.

    Used by the L1 router to decide whether a new report should be
    suppressed to prevent duplicate alerts and alert fatigue.

    Args:
        user_id: Anonymous user identifier.
        event_category: One of: ``sleep_issue``, ``mobility_issue``,
                        ``cognitive_issue``, ``weekly_summary``.
        hours_lookback: Hours to look back (default 48; use 72 for weekly
                        summaries).
    """
    try:
        result = check_alert_history_impl(
            user_id=user_id,
            event_category=event_category,
            hours_lookback=hours_lookback,
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except ValueError as exc:
        return json.dumps(
            {"error": str(exc)},
            ensure_ascii=False,
            indent=2,
        )


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
