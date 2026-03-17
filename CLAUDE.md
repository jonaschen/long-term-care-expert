# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Phase 1 in-progress project** for building `long-term-care-expert`, a hierarchical two-layer Claude Agent Skill Set for elderly home care monitoring in Taiwan.

Two specification documents must be read before writing any code:
- `LONGTERM_CARE_EXPERT_DEV_PLAN.md` — core system architecture, all five L2 Skills, three MCP tools, SaMD compliance rules, Phases 1–4
- `LONG_TERM_CARE_EXT_PLAN.md` — Japan calibration layer extension: new `east-asian-health-context-expert` Skill, `search_japan_clinical_data` tool, four Japanese RAG categories, enrichments to three existing Skills, Phases 5–6

**Current state:** Phase 1 in progress. Source PDFs downloaded to `knowledge_base/raw_documents/`. `scripts/process_pdfs.py` uses gemini-cli to extract and chunk content from each PDF. No skill or tool code written yet.

## Knowledge Base — Current State

`knowledge_base/raw_documents/` contains `.txt` stub files for most source documents and 2 KB HTML stub files (mislabeled `.pdf`) that the download script will replace with real PDFs.

`knowledge_base/processed_chunks/` contains 9 hand-written summary chunks covering all 5 RAG categories:

| File | Category | Chunk ID | Notes |
|---|---|---|---|
| `fall_prevention_hpa.md` | fall_prevention | fall_prevention_001 | |
| `dementia_care_hpa.md` | dementia_care | dementia_care_001 | Caregiver principles |
| `dementia_ten_signs_hpa.md` | dementia_care | dementia_care_002 | 10 behavioral change signs |
| `dementia_caregiver_resources_hpa.md` | dementia_care | dementia_care_003 | Community resources |
| `ad8_observation_guide.md` | dementia_care | dementia_care_004 | ⚠ INTERNAL USE ONLY — never surface in family output |
| `sleep_hygiene_hpa.md` | sleep_hygiene | sleep_hygiene_001 | |
| `chronic_disease_lifestyle_hpa.md` | chronic_disease_lifestyle | chronic_disease_lifestyle_001 | |
| `active_living_hpa.md` | chronic_disease_lifestyle | chronic_disease_lifestyle_002 | |
| `general_aging_hpa.md` | general_aging | general_aging_001 | |

These stubs pass the blacklisted-term compliance scan. Once real PDFs are downloaded, the full OCR → semantic chunking → medical filter pipeline needs to run to reach the ≥ 500 chunk target.

**Compliance rules for knowledge base chunks:**
- Every chunk must have metadata: `Category`, `Medical Content: false`, `Source`, `Audience`, `Update Date`, `Chunk ID`
- Run blacklist scan before indexing: `grep -rni "sarcopenia|medication|sleeping pill|melatonin|diagnos|disorder|prescription|alzheimer|parkinson|BPSD|rehabilitation" knowledge_base/processed_chunks/`
- `exclude_medical: true` must always be set when calling `search_hpa_guidelines`

## Two-Pillar Knowledge Architecture

The system uses two strictly separated knowledge pillars:

| Pillar | Source | RAG Tool | Used For |
|---|---|---|---|
| HPA (Pillar 1) | Taiwan Health Promotion Administration | `search_hpa_guidelines` | All family-facing language and suggestions |
| Japan (Pillar 2) | MHLW / JPHC / comparative disability research | `search_japan_clinical_data` | Internal calibration only — **never in family output** |

**The firewall between pillars is absolute.** Japan data informs when the system pays attention and what thresholds matter. It must never appear in any text delivered to families.

### Japan Calibration Layer — Key Facts
- Taiwan's elderly have higher mobility disability (49.82%) than Japan (36.07%) → gait signals need higher sensitivity
- Taiwan's elderly have higher IADL disability (30.36% vs Japan's 19.30%)
- Taiwan's loneliness rises faster with age than Japan's → social disengagement signals carry elevated weight
- JPHC (30-year, 140,000 participants): tea/coffee, fish, and activity regularity are documented protective factors for dementia in East Asian populations
- ME-BYO cognitive domain signals (wandering, appliance difficulty, prolonged inactivity) have lower reversibility than metabolic/locomotor signals — trigger calibration immediately, not after multi-domain convergence

## Planned Directory Structure

```
long-term-care-expert/
├── scripts/
│   ├── download_hpa_docs.py   # Phase 1: download HPA source PDFs
│   └── requirements.txt       # Python deps for scripts/
├── skills/
│   ├── L1-ltc-insight-router/
│   ├── L2-sleep-pattern-expert/
│   ├── L2-mobility-fall-expert/
│   ├── L2-dementia-behavior-expert/
│   ├── L2-chronic-disease-observer/
│   ├── L2-weekly-summary-composer/
│   └── L2-east-asian-health-context/  # Extension Phase 6 — internal calibration only
├── tools/
│   ├── mcp_server.py          # FastMCP server
│   ├── hpa_rag_search.py
│   ├── line_report_generator.py
│   ├── alert_history_checker.py
│   └── japan_clinical_data_search.py  # Extension Phase 5
├── knowledge_base/
│   ├── raw_documents/         # Source PDFs (9 HPA/AD-8 documents)
│   ├── processed_chunks/      # HPA chunks (5 categories) + Japan chunks (4 categories, Phase 5)
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

**Layer 2 — Domain Experts (6 Skills total):** Five core Skills handle behavioral domains and output exclusively via `generate_line_report`. One extension Skill (`east-asian-health-context-expert`) is internal-only — called by three core Skills for calibration, never produces family-facing output.

### Extension Skill Activation Rules
- `mobility-fall-expert` → calls `east-asian-health-context-expert` when gait slowdown persists ≥ 5 days
- `dementia-behavior-expert` → calls it immediately on ANY single cognitive signal (wandering, appliance difficulty, 3+ day inactivity); also on multi-domain ME-BYO convergence
- `weekly-summary-composer` → calls it once per weekly cycle for aggregate trend assessment

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
4. **`search_japan_clinical_data`** *(Extension Phase 5)* — RAG from Japanese MHLW/JPHC data. Used **only** by `east-asian-health-context-expert` for internal calibration. Must never feed into `generate_line_report`. Always use `exclude_medical: true` and include `purpose` field.

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

## Scripts

| Script | Purpose |
|---|---|
| `scripts/download_hpa_docs.py` | Automates HPA PDF downloads (AD-8 requires manual download) |
| `scripts/process_pdfs.py` | Uses gemini-cli (`@filename` syntax) to extract and chunk each PDF into `knowledge_base/processed_chunks/`. Run: `python3 scripts/process_pdfs.py [--file <filename>]` |
| `scripts/requirements.txt` | `requests`, `beautifulsoup4` |

## Acceptance KPIs

| Metric | Target |
|---|---|
| L1 routing accuracy | ≥ 95% (100-case test suite) |
| HPA RAG passage relevance | ≥ 4/5 |
| Japanese RAG calibration relevance | ≥ 4/5 per category |
| SaMD violations | 0% |
| Japan data in family output | 0 instances |
| Daily push frequency | ≤ 1/day |
| Family reply rate | ≥ 30% |
