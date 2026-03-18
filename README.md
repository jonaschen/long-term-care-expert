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
| Compliance scan (blacklist, 0 violations) | ✅ Passed |
| Build Qdrant `hpa_knowledge` collection + embed with bge-m3 | ✅ Complete (18 points indexed, dense + sparse) |
| Expand to fine-grained semantic chunks (target: ≥ 500) | ⬜ Pending (currently 18/500+) |
| Re-index after chunk expansion | ⬜ Pending |
| 30-query RAG relevance evaluation | ⬜ Pending |
| Design per-user baseline data structure | ⬜ Pending |

### PDF Processing

Run gemini-cli based extraction:

```bash
python3 scripts/process_pdfs.py           # process all 9 documents
python3 scripts/process_pdfs.py --file 失智症十大警訊.pdf  # single file
python3 scripts/process_pdfs.py --dry-run  # preview without calling gemini
```

Run compliance scan on processed chunks:

```bash
grep -rni "sarcopenia|medication|sleeping pill|diagnos|disorder" knowledge_base/processed_chunks/
```

### Download Script (if re-downloading)

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

---

### Remaining Phase 1 Steps

1. **Expand chunking** — re-run `process_pdfs.py` with section-level prompts to produce 50–100 chunks per large document; target ≥ 500 total across 5 categories
2. Build vector database with the five category partitions (`fall_prevention`, `dementia_care`, `sleep_hygiene`, `chronic_disease_lifestyle`, `general_aging`)
3. Run embedding pipeline over all processed chunks
4. Validate index with 30-query manual evaluation (target: ≥ 4/5 relevance)
5. Design per-user behavioral baseline data structure for `memory/user_baselines/`
6. Implement 14-day silent learning period logic

> **Note on AD-8 chunks:** `dementia_care_004` / `ad8_behavioral_domains_full.md` are marked `audience: internal_reasoning_only`. They must be stored in a non-queryable partition (or filtered out of all RAG results). The `dementia-behavior-expert` skill accesses them via direct lookup only — they must never surface through `search_hpa_guidelines`.
