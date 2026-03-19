# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Phase 2 project nearing completion** for building `long-term-care-expert`, a hierarchical two-layer Claude Agent Skill Set for elderly home care monitoring in Taiwan.

Two specification documents must be read before writing any code:
- `LONGTERM_CARE_EXPERT_DEV_PLAN.md` — core system architecture, all five L2 Skills, three MCP tools, SaMD compliance rules, Phases 1–4
- `LONG_TERM_CARE_EXT_PLAN.md` — Japan calibration layer extension: new `east-asian-health-context-expert` Skill, `search_japan_clinical_data` tool, four Japanese RAG categories, enrichments to three existing Skills, Phases 5–6

**Current state:** Phase 1 complete. Phase 2 ~90% complete. All L1/L2 SKILL.md files written. FastMCP server built with 3 MCP tools. All L2 reference docs and utility scripts created. Compliance files complete. 100-case routing test suite and 50-case adversarial test suite built. **Automated blacklist scanner** built and tested (40 unit tests) at `tests/compliance_tests/blacklist_scanner.py`. **150 L2 skill evaluation test cases** built (30 per skill × 5 skills) at `tests/skill_eval/test_cases/`. Knowledge base: 177 chunks indexed in Qdrant (177/177 points). RAG evaluation complete — **4.87/5 overall** (all 5 categories ≥ 4/5). **Remaining Phase 2 blockers:** (1) L1 routing validation against 100-case test suite (requires running L1 agent), (2) 30-case quality eval per L2 Skill (requires running L2 agents against test cases, then scanning outputs with blacklist scanner).

## Knowledge Base — Current State

`knowledge_base/raw_documents/` contains all 9 real PDFs (HPA handbooks + AD-8 scale).

`knowledge_base/processed_chunks/` contains **177 compliant chunks** — 18 original stubs/summaries + 159 section-level chunks from `expand_chunks.py`. All pass the blacklist compliance scan (0 violations, 0 `.REVIEW` files). RAG evaluation scored **4.87/5 overall** — further chunk expansion is not needed at this stage.

**Chunk counts by category:**

| Category | Approx. chunks | Source base_ids |
|---|---|---|
| `fall_prevention` | ~36 | fall_prevention_00x, fall_pro_s01–s18, fall_tips_s01–s14 |
| `dementia_care` | ~53 | dementia_care_00x, dementia_edu_s01–s14, dementia_care_s01–s20, dementia_signs_s01–s12, ad8_s01–s10 (⚠ internal) |
| `sleep_hygiene` | ~16 | sleep_hygiene_00x, sleep_s01–s14 |
| `chronic_disease_lifestyle` | ~33 | chronic_disease_lifestyle_00x, active_living_s01–s15, activity_guidelines_s01–s14 |
| `general_aging` | ~29 | general_aging_001 (stub), general_aging_active_s01–s10, general_aging_guidelines_s01–s10, general_aging_caregiver_s01–s08 |

**AD-8 internal chunks** (dementia_care_004, dementia_care_008, ad8_s01–ad8_s10 — 12 total): tagged `audience: internal_reasoning_only`. Stored in `hpa_knowledge` but **always excluded from general RAG queries** via hard payload filter. Accessible only via `lookup_ad8_chunks()` in `tools/hpa_rag_search.py`.

**Compliance rules for knowledge base chunks:**
- Every chunk must have metadata: `Category`, `Medical Content: false`, `Source`, `Audience`, `Update Date`, `Chunk ID`
- Run blacklist scan before indexing: `grep -rni "sarcopenia|medication|sleeping pill|melatonin|diagnos|disorder|prescription|alzheimer|parkinson|BPSD|rehabilitation" knowledge_base/processed_chunks/`
- `exclude_medical: true` must always be set when calling `search_hpa_guidelines`

## Vector Store & Embedding Stack

**Decided:** Qdrant (local embedded) + BAAI/bge-m3.

### Why Qdrant
- **Two collections** map exactly to the two-pillar architecture: `hpa_knowledge` and `japan_knowledge`. The firewall between pillars is enforced at the collection level — `search_hpa_guidelines` only queries `hpa_knowledge`, `search_japan_clinical_data` only queries `japan_knowledge`.
- **Payload filtering** handles all metadata requirements (`category`, `medical_content`, `audience`) natively, including the AD-8 isolation rule.
- **Hybrid search** (dense vector + sparse BM25 in a single query) — critical for domain precision. For dementia care queries, exact terminology ("wandering," "appliance difficulty," "day-night reversal") must be matched reliably alongside semantic similarity. Pure vector search alone is insufficient.
- **Named vectors** — allows adding a second embedding model later (e.g., a Chinese-specialized model) without rebuilding the index.
- **Embedded mode** (no Docker required for development) — runs as a local file at `knowledge_base/vector_index/`. Can be upgraded to Qdrant Cloud later with no code changes.

### Why BAAI/bge-m3
- Designed for Chinese + English retrieval tasks — the source documents are Chinese (Traditional), the queries will be English.
- Runs fully locally (privacy-first — no data sent to external APIs).
- Natively supports both dense and sparse vectors, feeding Qdrant's hybrid search directly without a separate sparse encoder.

### Collection Architecture

```
Qdrant (local file: knowledge_base/vector_index/)
│
├── Collection: hpa_knowledge
│   ├── Payload fields: category, chunk_id, source, audience, medical_content, update_date
│   ├── Query filter (always enforced): medical_content == false
│   ├── Query filter (general RAG): audience != "internal_reasoning_only"
│   └── Direct lookup (dementia-behavior-expert only): audience == "internal_reasoning_only"
│       └── Contains: dementia_care_004, dementia_care_008 (AD-8 chunks — never in general RAG)
│
└── Collection: japan_knowledge  ← Phase 5
    ├── Payload fields: category, source, population, outcome_type, taiwan_cultural_relevance, medical_content
    └── Query filter (always enforced): medical_content == false, purpose field required
```

### Phase 1 Scripts and Tools

| Script | Purpose |
|---|---|
| `scripts/expand_chunks.py` | Section-level chunk extraction (10–20 sections per PDF). Run: `python3 scripts/expand_chunks.py [--file <filename>]`. Includes JSON repair for gemini output with embedded double-quotes. |
| `tools/embedding_pipeline.py` | Embeds all chunks into Qdrant `hpa_knowledge` collection. Run: `.venv/bin/python3 tools/embedding_pipeline.py [--reset] [--batch-size N] [--dry-run]`. Use `--reset` when re-indexing after chunk additions. |
| `tools/hpa_rag_search.py` | `search_hpa_guidelines` MCP tool — hybrid search (dense + sparse RRF fusion). Hard filters enforced: `medical_content == false`, `audience != internal_reasoning_only`. Also exposes `lookup_ad8_chunks()`. CLI: `.venv/bin/python3 tools/hpa_rag_search.py "query" --category <cat> [--top-k N]` |
| `tests/rag_eval/run_rag_eval.py` | Runs 30-query RAG evaluation across all 5 categories. Saves Markdown report to `tests/rag_eval/results_YYYY-MM-DD.md` for manual scoring. Run: `.venv/bin/python3 tests/rag_eval/run_rag_eval.py` |

### Phase 2 Tools

| Script | Purpose |
|---|---|
| `tools/baseline_manager.py` | `BaselineManager` class — per-user behavioral baseline storage and 14-day silent learning period logic. Manages `memory/user_baselines/` JSON files. |
| `tools/mcp_server.py` | FastMCP server exposing 3 tools: `search_hpa_guidelines`, `generate_line_report`, `check_alert_history`. |
| `tools/line_report_generator.py` | `generate_line_report` tool — blacklist scanning of output text and auto-injection of mandatory legal disclaimer from `compliance/disclaimer_template.md`. |
| `tools/alert_history_checker.py` | `check_alert_history` tool — alert suppression within 48-72h window to prevent alert fatigue. Used by L1 router. |
| `tests/compliance_tests/blacklist_scanner.py` | ✅ Automated compliance scanner. Scans LINE Flex Messages and raw text for prohibited terms, whitelist coverage, and disclaimer injection. CLI: `python blacklist_scanner.py --scan-file FILE \| --scan-dir DIR \| --scan-text TEXT [--json-output] [--strict]`. Module API: `ComplianceScanner().scan_text()` / `.scan_flex_message()` / `.scan_directory()`. |
| `tests/skill_eval/test_cases/*.json` | ✅ 150 L2 skill evaluation test cases (30 per skill × 5 skills). Each file contains routing payloads, expected behaviors, and prohibited terms for compliance validation. |

**Python environment:** A venv exists at `.venv/`. Always use it for `tools/` and `tests/rag_eval/`. System Python is externally managed (cannot `pip install` without venv).

**RAG evaluation results** (2026-03-19): `tests/rag_eval/results_2026-03-19.md`

| Category | Score |
|---|---|
| fall_prevention | 5.00/5 |
| sleep_hygiene | 4.67/5 |
| dementia_care | 4.83/5 |
| chronic_disease_lifestyle | 5.00/5 |
| general_aging | 4.83/5 |
| **Overall** | **4.87/5** ✅ |

**Pending work (for contributors):**
1. Validate L1 routing against 100-case test suite — run L1 agent against `tests/routing_accuracy/test_cases_100.json`, target ≥ 95% accuracy
2. Run L2 agents against 30-case evaluation test suites (`tests/skill_eval/test_cases/*_30.json`), then scan outputs with `tests/compliance_tests/blacklist_scanner.py --scan-dir <output_dir>` (target ≥ 4/5 quality, 0% prohibited term leaks)

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
│   ├── embedding_pipeline.py  # Phase 1: embed chunks → Qdrant hpa_knowledge collection
│   ├── mcp_server.py          # FastMCP server
│   ├── hpa_rag_search.py      # search_hpa_guidelines — hybrid search on hpa_knowledge
│   ├── line_report_generator.py
│   ├── alert_history_checker.py
│   └── japan_clinical_data_search.py  # Extension Phase 5 — queries japan_knowledge collection
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
    │   └── test_cases_100.json
    ├── skill_eval/
    │   └── test_cases/          # 30-case eval suites per L2 Skill
    │       ├── sleep_pattern_expert_30.json
    │       ├── mobility_fall_expert_30.json
    │       ├── dementia_behavior_expert_30.json
    │       ├── chronic_disease_observer_30.json
    │       └── weekly_summary_composer_30.json
    ├── compliance_tests/
    │   ├── blacklist_scanner.py  # Automated compliance scanner (CLI + module)
    │   └── test_blacklist_scanner.py  # 40 unit tests
    ├── rag_eval/
    └── test_baseline_manager.py
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

## Scripts & Tools

| File | Purpose |
|---|---|
| `scripts/download_hpa_docs.py` | Automates HPA PDF downloads (AD-8 requires manual download) |
| `scripts/process_pdfs.py` | Uses gemini-cli (`@filename` syntax) to extract and chunk each PDF into `knowledge_base/processed_chunks/`. Run: `python3 scripts/process_pdfs.py [--file <filename>]` |
| `scripts/requirements.txt` | `requests`, `beautifulsoup4` |
| `tools/embedding_pipeline.py` | Embeds all chunks from `processed_chunks/` using bge-m3 and indexes into Qdrant `hpa_knowledge` collection. Run: `.venv/bin/python3 tools/embedding_pipeline.py [--reset] [--batch-size N] [--dry-run]` |
| `tools/requirements.txt` | `qdrant-client`, `FlagEmbedding`, `torch`, `transformers>=4.44.2,<5.0.0` ⚠ pin required — FlagEmbedding 1.3.5 incompatible with transformers 5.x |
| `scripts/expand_chunks.py` | Second-pass section-level chunk extraction via gemini-cli. Targets 10-20 sections per PDF. Run: `python3 scripts/expand_chunks.py [--file <filename>] [--dry-run]` |
| `tools/hpa_rag_search.py` | ✅ Built. `search_hpa_guidelines` MCP tool. Hybrid search (dense + sparse RRF fusion) on `hpa_knowledge`. Hard filters always enforced: `medical_content == false` and `audience != internal_reasoning_only`. Also exposes `lookup_ad8_chunks()` for dementia-behavior-expert direct lookup. Run CLI: `.venv/bin/python3 tools/hpa_rag_search.py "query" --category <cat> [--top-k N]` |
| `tests/rag_eval/run_rag_eval.py` | ✅ Built. Runs 30-query evaluation (6 per category). Saves Markdown report with content previews for manual scoring. Run: `.venv/bin/python3 tests/rag_eval/run_rag_eval.py` |
| `tools/japan_clinical_data_search.py` | *(Phase 5 — to build)* `search_japan_clinical_data` MCP tool. Queries `japan_knowledge` collection. Requires `purpose` field. Must never feed into `generate_line_report`. |

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
