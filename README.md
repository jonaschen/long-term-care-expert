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

## Phase 1 — Knowledge Base Downloads

A download script is now available at `scripts/download_hpa_docs.py`.
It fetches all HPA PDFs automatically (see [How to run](#how-to-run-the-download-script)).
The AD-8 instrument requires a one-time manual download (see note below).

### How to run the download script

```bash
pip install -r scripts/requirements.txt
python scripts/download_hpa_docs.py
```

The script will:
1. Detect and replace existing 2 KB HTML stub files with real PDFs.
2. For documents with a known direct URL — download immediately.
3. For HPA EBook / Detail / List pages — fetch the HTML, locate the embedded PDF
   link, then download the PDF.
4. Print a status summary and next-step instructions on completion.

---

### HPA Documents (hpa.gov.tw)

- [ ] **長者防跌妙招手冊** (Fall Prevention — public version)
  - Source page: https://www.hpa.gov.tw/Pages/EBook.aspx?nodeid=1193
  - Save as: `knowledge_base/raw_documents/長者防跌妙招手冊.pdf` *(replaces HTML stub)*

- [ ] **老人防跌工作手冊** (Fall Prevention — professional version)
  - Source page: https://www.hpa.gov.tw/Pages/EBook.aspx?nodeid=4347
  - Save as: `knowledge_base/raw_documents/老人防跌工作手冊.pdf`

- [ ] **失智症衛教及資源手冊** (Dementia Health Education and Resource Handbook)
  - Source page: https://www.hpa.gov.tw/Pages/EBook.aspx?nodeid=4381
  - Save as: `knowledge_base/raw_documents/失智症衛教及資源手冊.pdf`

- [ ] **失智症十大警訊** (10 Warning Signs of Dementia — trifold)
  - Source page: https://www.hpa.gov.tw/Pages/Detail.aspx?nodeid=871&pid=8017
  - Save as: `knowledge_base/raw_documents/失智症十大警訊.pdf`

- [ ] **失智症照顧者使用手冊** (Dementia Caregiver Handbook)
  - Source page: https://www.hpa.gov.tw/Pages/List.aspx?nodeid=4381
  - Save as: `knowledge_base/raw_documents/失智症照顧者使用手冊.pdf` *(replaces HTML stub)*

- [ ] **健康老化手冊 — 睡眠篇** (Healthy Aging — Sleep Chapter)
  - Direct URL: https://health.hpa.gov.tw/common/Download.ashx?f=f70fe5f8-cf1f-4f89-929c-072a219d29ab.pdf&o=05.睡眠與精神健康.pdf
  - Save as: `knowledge_base/raw_documents/健康老化手冊_睡眠篇.pdf`

- [ ] **動動生活手冊** (Active Living Handbook)
  - Source page: https://www.hpa.gov.tw/Pages/EBook.aspx?nodeid=1399
  - Save as: `knowledge_base/raw_documents/動動生活手冊_Active_Living.pdf`

- [ ] **全民身體活動指引** (Physical Activity Guidelines)
  - Source page: https://www.hpa.gov.tw/Pages/EBook.aspx?nodeid=1411
  - Save as: `knowledge_base/raw_documents/全民身體活動指引.pdf`

### AD-8 Scale (Washington University / Knight ADRC) — Manual Download

- [ ] **AD-8 Dementia Screening Interview — Taiwan Version**
  - URL: https://knightadrc.wustl.edu/professionals-clinicians/ad8-instrument/
  - **Licence:** Free for clinical/research use per Knight ADRC. Verify before use.
  - **Important — internal use only:** The AD-8 scale is used as an *internal reasoning
    reference* for the `dementia-behavior-expert` skill. It must **never** appear in
    family-facing output and must never be used as a scoring instrument.
  - Save as: `knowledge_base/raw_documents/AD8極早期失智症篩檢量表_台灣版.pdf`

### After Downloading

Once all PDFs are in place:
1. Run OCR and Markdown conversion on all new PDFs
2. Apply semantic chunking pipeline
3. Run medical content filter pass
4. Build vector index (target: ≥ 500 clean chunks across 5 categories)
