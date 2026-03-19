# long-term-care-expert

Hierarchical two-layer AI Agent system designed for elderly home care monitoring in Taiwan. It transforms anonymized IoT sensor data into warm, actionable caregiving language for families.

## Core Philosophy
- **Slow Insights, Not Real-Time Alerts:** Focus on trends to avoid alert fatigue.
- **De-medicalized Language Engineering:** Non-SaMD compliant (No diagnosis, no treatment).
- **Progressive Disclosure:** Simple insights first, deeper guidance on request.

## System Architecture
- **Layer 1 (L1):** `ltc-insight-router` - Pattern recognition and routing.
- **Layer 2 (L2):** Domain Experts (Sleep, Mobility, Dementia, Chronic Disease, Weekly Summary).
- **Extension (Phase 5–6):** `east-asian-health-context-expert` — internal Japan calibration layer (never family-facing).

## Tech Stack
- **AI Engine:** Claude Agent Skill Sets.
- **Protocol:** Model Context Protocol (MCP) via FastMCP.
- **Vector Store:** Qdrant (embedded local mode) — two collections: `hpa_knowledge` (Pillar 1) and `japan_knowledge` (Pillar 2, Phase 5).
- **Embedding Model:** BAAI/bge-m3 (local, multilingual Chinese + English, dense + sparse vectors for hybrid search).
- **Knowledge Base:** Taiwan HPA Guidelines (RAG, Pillar 1, family-facing) + Japan MHLW/JPHC (RAG, Pillar 2, internal calibration only).
- **Delivery:** LINE Official Account (Flex Messages).

## Getting Started
Refer to `LONGTERM_CARE_EXPERT_DEV_PLAN.md` for full implementation details and `ROADMAP.md` for the phased development plan.

---

## Current Status

### Phase 1 — Knowledge Base ✅ COMPLETE

| Step | Status |
|---|---|
| Download 9 HPA source PDFs | ✅ Complete |
| Initial extraction via `scripts/process_pdfs.py` | ✅ Complete (18 chunks) |
| Section-level expansion via `scripts/expand_chunks.py` | ✅ Complete (177 chunks, 0 violations) |
| Compliance scan (blacklist) | ✅ 0 violations / 177 chunks |
| Qdrant `hpa_knowledge` indexed with bge-m3 | ✅ 177/177 points (165 general + 12 AD-8 internal) |
| `tools/hpa_rag_search.py` — `search_hpa_guidelines` | ✅ Hybrid search (dense + sparse RRF), AD-8 isolation enforced |
| 30-query RAG evaluation | ✅ **4.87/5 overall** — all 5 categories ≥ 4/5 |
| Per-user baseline system (`tools/baseline_manager.py`) | ✅ 14-day silent learning period, `memory/user_baselines/` |

### Phase 2 — Core Skill Development (~85% complete)

| Step | Status |
|---|---|
| L1 router SKILL.md + routing_rules.json | ✅ Complete |
| All 5 L2 SKILL.md files | ✅ Complete |
| FastMCP server with 3 tools | ✅ `search_hpa_guidelines`, `generate_line_report`, `check_alert_history` |
| L2 reference docs (8 files) | ✅ All created — sleep, mobility, dementia, chronic disease, weekly |
| L2 utility scripts (4 files) | ✅ `sleep_pattern_analyzer.py`, `gait_anomaly_detector.py`, `behavior_pattern_check.py`, `weekly_report_builder.py` |
| Compliance files | ✅ `blacklist_terms.json`, `whitelist_terms.json`, `disclaimer_template.md` |
| 100-case L1 routing test suite | ✅ `tests/routing_accuracy/test_cases_100.json` |
| 50-case adversarial compliance test suite | ✅ `compliance/adversarial_test_cases.json` |
| **L1 routing validation** (run agent vs. test suite) | ⬜ **Pending** — target ≥ 95% accuracy |
| **Automated blacklist scanner** for generated outputs | ⬜ **Pending** — scan `generate_line_report` output text |
| **30-case quality eval per L2 Skill** | ⬜ **Pending** — 5 Skills × 30 cases, manual scoring, target ≥ 4/5 |

---

## Next Steps for Contributors

**Priority 1 — L1 Routing Validation:**
Run the L1 `ltc-insight-router` agent against the 100-case test suite and score routing decisions against expected outputs.
```
tests/routing_accuracy/test_cases_100.json  ← input
tests/routing_accuracy/                     ← save results here
Target: ≥ 95% correct route assignment
```

**Priority 2 — Automated Blacklist Scanner:**
Build a script that runs `generate_line_report` against a set of test inputs and scans every output for prohibited terms from `compliance/blacklist_terms.json`.
```
compliance/blacklist_terms.json   ← prohibited terms
compliance/adversarial_test_cases.json  ← adversarial inputs to test against
Target: 0 prohibited term leaks
```

**Priority 3 — L2 Quality Evaluation:**
Generate 30 sample reports per L2 Skill and manually score for warmth, accuracy, and compliance.
```
Target: ≥ 4/5 per Skill
Skills: sleep-pattern-expert, mobility-fall-expert, dementia-behavior-expert,
        chronic-disease-observer, weekly-summary-composer
```

### Python Environment

A venv exists at `.venv/`. Always use it for `tools/`:
```bash
source .venv/bin/activate          # activate
.venv/bin/python3 tools/...        # or invoke directly
```
System Python is externally managed — `pip install` without the venv will fail.

### PDF Processing Scripts

```bash
# Initial summary extraction (one chunk per document)
python3 scripts/process_pdfs.py
python3 scripts/process_pdfs.py --file 失智症十大警訊.pdf

# Section-level expansion (10–20 chunks per document)
python3 scripts/expand_chunks.py
python3 scripts/expand_chunks.py --file "健康老化手冊_睡眠篇.pdf"

# Compliance scan
grep -rni "sarcopenia|medication|sleeping pill|melatonin|diagnos|disorder|prescription|alzheimer|parkinson|BPSD|rehabilitation|clinical" knowledge_base/processed_chunks/

# Re-index Qdrant (only needed after adding new chunks)
.venv/bin/python3 tools/embedding_pipeline.py --reset

# RAG evaluation
.venv/bin/python3 tests/rag_eval/run_rag_eval.py
```

---

## HPA Documents (hpa.gov.tw)

- [x] **長者防跌妙招手冊** (Fall Prevention — public version)
- [x] **老人防跌工作手冊** (Fall Prevention — professional version)
- [x] **失智症衛教及資源手冊** (Dementia Health Education and Resource Handbook)
- [x] **失智症十大警訊** (10 Warning Signs of Dementia — trifold)
- [x] **失智症照顧者使用手冊** (Dementia Caregiver Handbook)
- [x] **健康老化手冊 — 睡眠篇** (Healthy Aging — Sleep Chapter)
- [x] **動動生活手冊** (Active Living Handbook)
- [x] **全民身體活動指引** (Physical Activity Guidelines)

## AD-8 Scale (Washington University / Knight ADRC) — Manual Download

- [x] **AD-8 Dementia Screening Interview — Taiwan Version**
  - URL: https://knightadrc.wustl.edu/professionals-clinicians/ad8-instrument/
  - **Licence:** Free for clinical/research use per Knight ADRC. Verify before use.
  - **Important — internal use only:** Used as an *internal reasoning reference* for the
    `dementia-behavior-expert` skill only. Must **never** appear in family-facing output
    and must never be used as a scoring instrument.

> **AD-8 isolation rule:** Chunks tagged `audience: internal_reasoning_only` are stored in `hpa_knowledge` but are **excluded from all general RAG queries** via hard payload filter. They are accessible only via `lookup_ad8_chunks()` in `tools/hpa_rag_search.py` — never through `search_hpa_guidelines`.
