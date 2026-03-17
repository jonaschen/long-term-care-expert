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
- **Protocol:** Model Context Protocol (MCP).
- **Knowledge Base:** Taiwan HPA Guidelines (RAG, Pillar 1) + Japan MHLW/JPHC (RAG, Pillar 2 — internal only).
- **Delivery:** LINE Official Account (Flex Messages).

## Getting Started
Refer to `LONGTERM_CARE_EXPERT_DEV_PLAN.md` for full implementation details and `ROADMAP.md` for the phased development plan.

---

## Phase 1 — Knowledge Base

### Status

| Step | Status |
|---|---|
| Download 9 HPA source PDFs | ✅ Complete |
| Extract + chunk all PDFs via `scripts/process_pdfs.py` | ✅ Complete (18 chunks) |
| Compliance scan (blacklist, 0 violations) | ✅ Passed |
| Build vector index (target: ≥ 500 chunks) | ⬜ Pending |
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

1. Build vector database with the five category partitions (`fall_prevention`, `dementia_care`, `sleep_hygiene`, `chronic_disease_lifestyle`, `general_aging`)
2. Run embedding pipeline over all processed chunks — target ≥ 500 chunks (split large chunks if needed)
3. Validate index with 30-query manual evaluation (target: ≥ 4/5 relevance)
4. Design per-user behavioral baseline data structure for `memory/user_baselines/`
5. Implement 14-day silent learning period logic
