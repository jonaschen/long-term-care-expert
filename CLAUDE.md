# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **planning-phase project** for building `long-term-care-expert`, a hierarchical two-layer Claude Agent Skill Set for elderly home care monitoring in Taiwan. The full specification is in `LONGTERM_CARE_EXPERT_DEV_PLAN.md` — read it completely before writing any code.

**Current state:** No code exists yet. Only documentation and architectural specifications.

## Planned Directory Structure

```
long-term-care-expert/
├── skills/
│   ├── L1-ltc-insight-router/
│   ├── L2-sleep-pattern-expert/
│   ├── L2-mobility-fall-expert/
│   ├── L2-dementia-behavior-expert/
│   ├── L2-chronic-disease-observer/
│   └── L2-weekly-summary-composer/
├── tools/
│   ├── mcp_server.py          # FastMCP server
│   ├── hpa_rag_search.py
│   ├── line_report_generator.py
│   └── alert_history_checker.py
├── knowledge_base/
│   ├── raw_documents/
│   ├── processed_chunks/
│   └── vector_index/
├── compliance/
│   ├── blacklist_terms.json
│   ├── whitelist_terms.json
│   ├── adversarial_test_cases.json
│   └── disclaimer_template.md
└── tests/
    ├── routing_accuracy/
    ├── skill_eval/
    └── compliance_tests/
```

## Architecture: Two-Layer Agent System

**Layer 1 — `ltc-insight-router`:** Aggregates 24-72 hours of JSON behavioral events from IoT edge devices. Compares against a personal 14-day baseline. Calls `check_alert_history` to suppress duplicate reports (48-72h window). Single-event anomalies are **always suppressed** — only multi-day trends route to L2.

**Layer 2 — Domain Experts (5 Skills):** Each expert handles one behavioral domain and outputs exclusively via `generate_line_report`. They never output raw text to the user.

### Routing Thresholds

| Event | Threshold | Routes To |
|---|---|---|
| `bed_exit` | ≥ 2 during night | sleep-pattern-expert |
| `tossing_and_turning` | ≥ 30 min | sleep-pattern-expert |
| `walking` (anomalous_slow) | ≥ 30% below baseline | mobility-fall-expert |
| `rise_attempt_fail` | ≥ 2 consecutive | mobility-fall-expert |
| `posture_change: sudden_drop` | Any occurrence (URGENT) | mobility-fall-expert immediately |
| `wandering` | During 23:00-05:00 | dementia-behavior-expert |
| `inactivity` | ≥ 4 hours daytime | dementia-behavior-expert |

### MCP Tools

1. **`search_hpa_guidelines`** — RAG from Taiwan HPA knowledge base. Always use `exclude_medical: true`.
2. **`generate_line_report`** — The only valid L2 output channel. Auto-injects legal disclaimer.
3. **`check_alert_history`** — Used by L1 to prevent alert fatigue.

## Non-Negotiable Compliance Rules (SaMD)

This system must **never** be classified as a Software as a Medical Device under Taiwan TFDA rules.

**Prohibited terms (zero tolerance):**
`diagnose`, `diagnosis`, `treatment`, `disorder`, `disease`, `prescription`, `medication`, `sleeping pills`, `melatonin`, `Alzheimer's disease`, `Parkinson's`, `dementia` (as diagnosis), `"has X"`, `"suffers from"`, `rehabilitation`, `symptoms`

**Required observational language:**
- "sensor noticed..." / "we observed that..."
- "compared to the usual pattern..."
- "behavioral pattern change" (not "symptom")
- "you might consider..." / "if this continues, consult a professional"

**Mandatory disclaimer** (auto-injected by `generate_line_report`):
> This system is not a medical device (Non-SaMD). The information provided is for home environment safety improvement and general health promotion reference only. It does not constitute professional medical diagnosis.

Compliance tests must achieve: **0% prohibited term leaks**, **100% disclaimer coverage**.

## Acceptance KPIs

| Metric | Target |
|---|---|
| L1 routing accuracy | ≥ 95% (100-case test suite) |
| RAG passage relevance | ≥ 4/5 |
| SaMD violations | 0% |
| Daily push frequency | ≤ 1/day |
| Family reply rate | ≥ 30% |
