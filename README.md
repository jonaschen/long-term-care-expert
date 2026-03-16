# long-term-care-expert

Hierarchical two-layer AI Agent system designed for elderly home care monitoring in Taiwan. It transforms anonymized IoT sensor data into warm, actionable caregiving language for families.

## Core Philosophy
- **Slow Insights, Not Real-Time Alerts:** Focus on trends to avoid alert fatigue.
- **De-medicalized Language Engineering:** Non-SaMD compliant (No diagnosis, no treatment).
- **Progressive Disclosure:** Simple insights first, deeper guidance on request.

## System Architecture
- **Layer 1 (L1):** `ltc-insight-router` - Pattern recognition and routing.
- **Layer 2 (L2):** Domain Experts (Sleep, Mobility, Dementia, Chronic Disease, Weekly Summary).

## Tech Stack
- **AI Engine:** Claude Agent Skill Sets.
- **Protocol:** Model Context Protocol (MCP).
- **Knowledge Base:** Taiwan HPA Guidelines (RAG).
- **Delivery:** LINE Official Account (Flex Messages).

## Getting Started
Refer to `LONGTERM_CARE_EXPERT_DEV_PLAN.md` for full implementation details and `ROADMAP.md` for the phased development plan.

---

## Phase 1 TODO — Knowledge Base Downloads

The following source documents need to be downloaded manually and placed in `knowledge_base/raw_documents/`. Each item includes the source URL and the expected filename.

### HPA Documents (hpa.gov.tw)

- [ ] **長者防跌妙招手冊** (Fall Prevention — public version)
  - URL: https://www.hpa.gov.tw/Pages/EBook.aspx?nodeid=1193
  - Save as: `長者防跌妙招手冊.pdf` *(replace existing 2 KB stub)*

- [ ] **老人防跌工作手冊** (Fall Prevention — professional version)
  - URL: https://www.hpa.gov.tw/Pages/EBook.aspx?nodeid=4347
  - Save as: `老人防跌工作手冊.pdf`

- [ ] **失智症衛教及資源手冊** (Dementia Health Education and Resource Handbook)
  - URL: https://www.hpa.gov.tw/Pages/EBook.aspx?nodeid=4381
  - Save as: `失智症衛教及資源手冊.pdf` *(supplements existing `_raw.txt`)*

- [ ] **失智症十大警訊** (10 Warning Signs of Dementia — trifold)
  - URL: https://www.hpa.gov.tw/Pages/Detail.aspx?nodeid=871&pid=8017
  - Save as: `失智症十大警訊.pdf` *(supplements existing `_raw.txt`)*

- [ ] **失智症照顧者使用手冊** (Dementia Caregiver Handbook)
  - URL: https://www.hpa.gov.tw/Pages/List.aspx?nodeid=4381
  - Save as: `失智症照顧者使用手冊.pdf` *(replace existing 2 KB stub)*

- [ ] **健康老化手冊 — 睡眠篇** (Healthy Aging — Sleep Chapter)
  - URL: https://health.hpa.gov.tw/common/Download.ashx?f=f70fe5f8-cf1f-4f89-929c-072a219d29ab.pdf&o=05.睡眠與精神健康.pdf
  - Save as: `健康老化手冊_睡眠篇.pdf` *(supplements existing `_raw.txt`)*

- [ ] **動動生活手冊** (Active Living Handbook)
  - URL: https://www.hpa.gov.tw/Pages/EBook.aspx?nodeid=1399
  - Save as: `動動生活手冊_Active_Living.pdf` *(supplements existing `_raw.txt`)*

- [ ] **全民身體活動指引** (Physical Activity Guidelines)
  - URL: https://www.hpa.gov.tw/Pages/EBook.aspx?nodeid=1411
  - Save as: `全民身體活動指引.pdf`

### AD-8 Scale (Washington University / Knight ADRC)

- [ ] **AD-8 Dementia Screening Interview**
  - URL: https://knightadrc.wustl.edu/professionals-clinicians/ad8-instrument/
  - Note: Verify license before use. Free for clinical/research use per Knight ADRC. For this system, the scale is used as an **internal reasoning reference only** — it must never appear in family-facing output and must never be used as a scoring instrument.
  - Save as: `AD8極早期失智症篩檢量表_台灣版.pdf` *(supplements existing `_raw.txt`)*

### After Downloading

Once files are in place, notify Claude Code to proceed with:
1. OCR and Markdown conversion of all PDFs
2. Semantic chunking pipeline
3. Medical content filter pass
4. Vector index build (target: ≥ 500 clean chunks across 5 categories)
