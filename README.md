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

## Phase 1 — Knowledge Base

### Status

| Step | Status |
|---|---|
| Download 9 HPA source PDFs | ✅ Complete |
| Initial extraction via `scripts/process_pdfs.py` | ✅ Complete (18 chunks — one per document) |
| Section-level expansion via `scripts/expand_chunks.py` | ✅ Complete (177 chunks total, 0 violations) |
| Compliance scan (blacklist, 0 violations) | ✅ Passed |
| Build Qdrant `hpa_knowledge` collection + embed with bge-m3 | ⚠ Re-index needed (Qdrant has 149 pts; 177 chunks in `processed_chunks/`) |
| `tools/hpa_rag_search.py` — `search_hpa_guidelines` MCP tool | ✅ Complete — hybrid search (dense + sparse RRF), hard payload filters, AD-8 direct lookup |
| 30-query RAG evaluation script | ✅ Complete (`tests/rag_eval/run_rag_eval.py`) |
| 30-query RAG relevance evaluation — manual scoring | ⬜ Pending (run eval, score results in `tests/rag_eval/results_YYYY-MM-DD.md`) |
| Design per-user baseline data structure | ⬜ Pending |

### Immediate Next Steps for Contributors

**1. Re-index Qdrant** (28 new `general_aging` chunks not yet indexed):
```bash
source .venv/bin/activate
python tools/embedding_pipeline.py --reset
```

**2. Re-run and score the RAG evaluation:**
```bash
python tests/rag_eval/run_rag_eval.py
# Then open tests/rag_eval/results_YYYY-MM-DD.md and fill in Score: ?/5 for each query
# Target: ≥ 4/5 average across all 30 queries
```

**3. If general_aging scores < 4/5** — that category had only one stub until recently. The 3 new extraction passes (28 chunks) should fix it. If still weak after re-index, consider sourcing an additional HPA general aging document.

**4. Design `memory/user_baselines/` schema** — per-user behavioral baseline (14-day silent learning period, then report generation begins). See `LONGTERM_CARE_EXPERT_DEV_PLAN.md` Phase 1 spec.

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
python3 scripts/process_pdfs.py --dry-run

# Section-level expansion (10–20 chunks per document)
python3 scripts/expand_chunks.py
python3 scripts/expand_chunks.py --file "健康老化手冊_睡眠篇.pdf"
python3 scripts/expand_chunks.py --dry-run

# Compliance scan
grep -rni "sarcopenia|medication|sleeping pill|melatonin|diagnos|disorder|prescription|alzheimer|parkinson|BPSD|rehabilitation|clinical" knowledge_base/processed_chunks/
```

### Download Script (if re-downloading PDFs)

```bash
pip install -r scripts/requirements.txt
python scripts/download_hpa_docs.py
```

---

### HPA Documents (hpa.gov.tw)

- [x] **長者防跌妙招手冊** (Fall Prevention — public version)
- [x] **老人防跌工作手冊** (Fall Prevention — professional version)
- [x] **失智症衛教及資源手冊** (Dementia Health Education and Resource Handbook)
- [x] **失智症十大警訊** (10 Warning Signs of Dementia — trifold)
- [x] **失智症照顧者使用手冊** (Dementia Caregiver Handbook)
- [x] **健康老化手冊 — 睡眠篇** (Healthy Aging — Sleep Chapter)
- [x] **動動生活手冊** (Active Living Handbook)
- [x] **全民身體活動指引** (Physical Activity Guidelines)

### AD-8 Scale (Washington University / Knight ADRC) — Manual Download

- [x] **AD-8 Dementia Screening Interview — Taiwan Version**
  - URL: https://knightadrc.wustl.edu/professionals-clinicians/ad8-instrument/
  - **Licence:** Free for clinical/research use per Knight ADRC. Verify before use.
  - **Important — internal use only:** Used as an *internal reasoning reference* for the
    `dementia-behavior-expert` skill only. Must **never** appear in family-facing output
    and must never be used as a scoring instrument.

> **AD-8 isolation rule:** Chunks tagged `audience: internal_reasoning_only` are stored in `hpa_knowledge` but are **excluded from all general RAG queries** via hard payload filter. They are accessible only via `lookup_ad8_chunks()` in `tools/hpa_rag_search.py` — never through `search_hpa_guidelines`.
