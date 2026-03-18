#!/usr/bin/env python3
"""
tests/rag_eval/run_rag_eval.py

Runs the 30-query Phase 1 RAG relevance evaluation against the
hpa_knowledge Qdrant collection via search_hpa_guidelines().

Outputs a Markdown report to tests/rag_eval/results_YYYY-MM-DD.md
for manual scoring (target: ≥ 4/5 per query).

Usage:
    .venv/bin/python3 tests/rag_eval/run_rag_eval.py
"""

import datetime
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

from hpa_rag_search import search_hpa_guidelines  # noqa: E402

# ---------------------------------------------------------------------------
# 30 evaluation queries — 6 per category
# ---------------------------------------------------------------------------
QUERIES = [
    # --- fall_prevention (6) ---
    {
        "category": "fall_prevention",
        "query": "elderly person gets up too fast from bed and feels dizzy",
        "rationale": "Orthostatic hypotension / sudden posture change",
    },
    {
        "category": "fall_prevention",
        "query": "elder walking slower than usual and shuffling feet",
        "rationale": "Gait change observation — L1 routing signal",
    },
    {
        "category": "fall_prevention",
        "query": "bathroom safety grab bars and non-slip mat recommendations",
        "rationale": "Home modification for high-risk fall location",
    },
    {
        "category": "fall_prevention",
        "query": "elder failed twice trying to stand up from chair without help",
        "rationale": "rise_attempt_fail routing threshold",
    },
    {
        "category": "fall_prevention",
        "query": "footwear and clothing tips to reduce tripping indoors",
        "rationale": "Wearable hazard mitigation",
    },
    {
        "category": "fall_prevention",
        "query": "lighting improvements to prevent falls at night in hallway",
        "rationale": "Environmental modification for nighttime safety",
    },

    # --- sleep_hygiene (6) ---
    {
        "category": "sleep_hygiene",
        "query": "elder wakes up multiple times at night and cannot fall back asleep",
        "rationale": "Fragmented sleep pattern — core L2 signal",
    },
    {
        "category": "sleep_hygiene",
        "query": "how to reduce nighttime bathroom trips for elderly",
        "rationale": "Nocturia management without medication",
    },
    {
        "category": "sleep_hygiene",
        "query": "bedroom temperature light and noise for better elder sleep",
        "rationale": "Sleep environment optimization",
    },
    {
        "category": "sleep_hygiene",
        "query": "elder sleeping too much during the day and awake at night",
        "rationale": "Day-night reversal — dementia overlap signal",
    },
    {
        "category": "sleep_hygiene",
        "query": "relaxation routine before bedtime to help elder fall asleep",
        "rationale": "Sleep onset support",
    },
    {
        "category": "sleep_hygiene",
        "query": "how sunlight and daytime activity affect elder sleep quality",
        "rationale": "Circadian rhythm support via lifestyle",
    },

    # --- dementia_care (6) ---
    {
        "category": "dementia_care",
        "query": "elder wandering around house at night unable to find bedroom",
        "rationale": "Nighttime wandering — immediate dementia signal",
    },
    {
        "category": "dementia_care",
        "query": "elder asking same question repeatedly within minutes",
        "rationale": "Repetitive questioning — early behavioral change",
    },
    {
        "category": "dementia_care",
        "query": "elder having difficulty using familiar appliances like kettle or TV remote",
        "rationale": "Appliance difficulty — AD-8 behavioral domain",
    },
    {
        "category": "dementia_care",
        "query": "daily routine and structured schedule to support elder with memory changes",
        "rationale": "Routine establishment for cognitive stability",
    },
    {
        "category": "dementia_care",
        "query": "how to respond calmly when elder becomes agitated or confused",
        "rationale": "Caregiver communication technique",
    },
    {
        "category": "dementia_care",
        "query": "safety measures to prevent elder from leaving home unsupervised",
        "rationale": "Wandering prevention — home safety",
    },

    # --- chronic_disease_lifestyle (6) ---
    {
        "category": "chronic_disease_lifestyle",
        "query": "gentle seated exercises for elderly with limited mobility",
        "rationale": "Chair-based activity for low-mobility elder",
    },
    {
        "category": "chronic_disease_lifestyle",
        "query": "how much walking is recommended for elderly per week",
        "rationale": "Activity target for 65+ per HPA guidelines",
    },
    {
        "category": "chronic_disease_lifestyle",
        "query": "household activities that count as exercise for seniors",
        "rationale": "Incidental activity — low barrier entry",
    },
    {
        "category": "chronic_disease_lifestyle",
        "query": "balance exercises to help elderly reduce fall risk",
        "rationale": "Strength and balance program overlap",
    },
    {
        "category": "chronic_disease_lifestyle",
        "query": "how to encourage an elder who refuses to exercise",
        "rationale": "Caregiver motivation strategy",
    },
    {
        "category": "chronic_disease_lifestyle",
        "query": "warning signs that elder should stop exercising and rest",
        "rationale": "Safety during activity — when to pause",
    },

    # --- general_aging (6) ---
    {
        "category": "general_aging",
        "query": "normal physical changes in elderly that families should know about",
        "rationale": "Baseline expectation setting — reduce family anxiety",
    },
    {
        "category": "general_aging",
        "query": "how to help elderly maintain independence at home",
        "rationale": "Autonomy support — core caregiving principle",
    },
    {
        "category": "general_aging",
        "query": "social engagement activities for elderly living alone",
        "rationale": "Loneliness / social disengagement signal",
    },
    {
        "category": "general_aging",
        "query": "nutrition and meal suggestions for healthy aging",
        "rationale": "Dietary lifestyle guidance (non-medical)",
    },
    {
        "category": "general_aging",
        "query": "caregiver burnout and how families can take breaks",
        "rationale": "Caregiver wellbeing — secondary audience",
    },
    {
        "category": "general_aging",
        "query": "when should family accompany elder to see a professional",
        "rationale": "Appropriate escalation language — SaMD boundary",
    },
]

TOP_K = 3


def run_eval() -> Path:
    today = datetime.date.today().isoformat()
    out_path = REPO_ROOT / "tests" / "rag_eval" / f"results_{today}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        f"# RAG Evaluation — {today}",
        "",
        "**Target:** ≥ 4/5 average relevance per query  |  top_k = 3  |  30 queries across 5 categories",
        "",
        "**Scoring guide:**",
        "- 5 — Perfect. Top result directly answers the query with actionable guidance.",
        "- 4 — Good. Top result is closely related; minor gap in specificity.",
        "- 3 — Acceptable. Relevant category but not the most specific chunk.",
        "- 2 — Weak. Tangentially related; missing the core need.",
        "- 1 — Miss. Irrelevant result returned.",
        "",
        "---",
        "",
    ]

    current_category = None
    query_num = 0

    print("\nLoading bge-m3 model...")

    for q in QUERIES:
        if q["category"] != current_category:
            current_category = q["category"]
            lines.append(f"## {current_category.replace('_', ' ').title()}")
            lines.append("")

        query_num += 1
        print(f"[{query_num:02d}/30] {q['category']} — {q['query'][:60]}")

        try:
            results = search_hpa_guidelines(
                query=q["query"],
                category=q["category"],
                top_k=TOP_K,
            )
            error = None
        except Exception as exc:
            results = []
            error = str(exc)

        lines.append(f"### Q{query_num:02d}. {q['query']}")
        lines.append("")
        lines.append(f"*Rationale: {q['rationale']}*")
        lines.append("")

        if error:
            lines.append(f"> ❌ ERROR: {error}")
        elif not results:
            lines.append("> ⚠ No results returned.")
        else:
            for i, r in enumerate(results, 1):
                lines.append(f"**[{i}] `{r['chunk_id']}`** — score {r['score']}")
                lines.append(f"Source: {r['source']}")
                # Show first 400 chars of content body (skip metadata header)
                body = r["content"]
                # Find first ## heading line for preview start
                preview_start = body.find("## ")
                if preview_start != -1:
                    preview = body[preview_start:preview_start + 450]
                else:
                    preview = body[:450]
                preview = preview.replace("\n", " ").strip()
                lines.append(f"> {preview}...")
                lines.append("")

        lines.append("**Score: ?/5**")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Summary table placeholder
    lines += [
        "## Summary",
        "",
        "| Category | Q1 | Q2 | Q3 | Q4 | Q5 | Q6 | Avg |",
        "|---|---|---|---|---|---|---|---|",
        "| fall_prevention | ? | ? | ? | ? | ? | ? | ? |",
        "| sleep_hygiene | ? | ? | ? | ? | ? | ? | ? |",
        "| dementia_care | ? | ? | ? | ? | ? | ? | ? |",
        "| chronic_disease_lifestyle | ? | ? | ? | ? | ? | ? | ? |",
        "| general_aging | ? | ? | ? | ? | ? | ? | ? |",
        "| **Overall** | | | | | | | **?/5** |",
        "",
        "> Fill in scores above, then compute averages.",
        "> Phase 1 acceptance criterion: overall average ≥ 4/5.",
        "",
    ]

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nReport saved → {out_path.relative_to(REPO_ROOT)}")
    return out_path


if __name__ == "__main__":
    run_eval()
