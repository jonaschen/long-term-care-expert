# ROADMAP.md

Development roadmap for `long-term-care-expert` — a two-layer Claude Agent Skill Set for privacy-first elderly home care monitoring in Taiwan.

Each phase has hard acceptance criteria that must pass before the next phase begins.

---

## Phase 1 — Knowledge Base and Infrastructure
**Duration:** Month 1
**Goal:** Build the HPA health education RAG knowledge base that all L2 Skills depend on. Nothing else can be built correctly without this foundation.

### Tasks

**Document Collection**
- [ ] Obtain and verify usage authorization for all HPA source documents:
  - HPA Fall Prevention Handbook for the Elderly (professional + public versions)
  - HPA Dementia Health Education and Resource Handbook
  - HPA "10 Warning Signs of Dementia"
  - HPA "Good Sleep Habits" pamphlet and Healthy Aging handbook (sleep chapter)
  - HPA Active Living Handbook
  - AD-8 Early Detection Scale (behavioral observation items only)

**Document Processing**
- [ ] Convert PDFs to clean Markdown via OCR/document parsing
- [ ] Strip all page headers, footers, page numbers, and formatting artifacts
- [ ] Apply semantic chunking (paragraph-aware, not character-count-based; preserve list structures and logical steps intact)
- [ ] Attach metadata to every chunk: `source`, `category`, `medical_content`, `audience`, `update_date`, `chunk_id`
- [ ] Partition chunks into five categories: `fall_prevention`, `dementia_care`, `sleep_hygiene`, `chronic_disease_lifestyle`, `general_aging`

**Medical Content Filter (Critical)**
- [ ] Build automated scanner that identifies and marks/removes passages containing:
  - Drug names and dosage instructions
  - Diagnostic criteria
  - Clinical treatment protocols
  - Pharmaceutical recommendations
- [ ] Run filter over all chunks; achieve ≥ 99% accuracy (any pharmaceutical content passing through is a direct legal risk)

**Vector Database**
- [ ] Deploy vector database with the five category partitions
- [ ] Run embedding pipeline over all processed chunks
- [ ] Validate index with 30-query manual evaluation for retrieval relevance

**Baseline System Design**
- [ ] Design per-user behavioral baseline data structure
- [ ] Implement 14-day silent learning period logic (no reports sent during this window)
- [ ] Define storage schema for `memory/user_baselines/`

### Acceptance Criteria
| Criterion | Target |
|---|---|
| Clean chunks in knowledge base | ≥ 500 across 5 categories |
| Medical content filter accuracy | ≥ 99% |
| RAG retrieval relevance (30-query manual eval) | ≥ 4/5 |

---

## Phase 2 — Core Skill Development
**Duration:** Month 2
**Goal:** Build the L1 router, all five L2 Skills, and the FastMCP server. All prompt engineering and tool integration completed and tested.

**Dependency:** Phase 1 acceptance criteria must pass. The RAG knowledge base must be live before L2 Skills can be validated.

### Tasks

**Directory and File Structure**
- [ ] Create full directory layout per `LONGTERM_CARE_EXPERT_DEV_PLAN.md` spec
- [ ] Write `AGENTS.md` (system entry point and routing manifest)
- [ ] Write `COMPLIANCE.md` (SaMD boundary rules, blacklist, whitelist terms)

**L1 Router (`ltc-insight-router`)**
- [ ] Write `skills/L1-ltc-insight-router/SKILL.md` (routing system prompt)
- [ ] Write `skills/L1-ltc-insight-router/routing_rules.json` (machine-readable event→route mapping)
- [ ] Document JSON event schema at `skills/L1-ltc-insight-router/references/json_event_schema.md`
- [ ] Build 100-case routing accuracy test suite (`tests/routing_accuracy/test_cases_100.json`)
- [ ] Validate L1 routing against test suite

**L2 Skills (Priority Order)**
- [ ] `L2-sleep-pattern-expert`: SKILL.md, `sleep_pattern_analyzer.py`, reference docs
- [ ] `L2-mobility-fall-expert`: SKILL.md, `gait_anomaly_detector.py`, reference docs — include `sudden_drop` urgency override
- [ ] `L2-dementia-behavior-expert`: SKILL.md, `behavior_pattern_check.py`, `ad8_observation_guide.md` (behavioral items only, no clinical framing), `dementia_early_signs.md`
- [ ] `L2-chronic-disease-observer`: SKILL.md, `healthy_lifestyle.md` reference
- [ ] `L2-weekly-summary-composer`: SKILL.md, `weekly_report_builder.py`, `report_tone_templates.md`

**MCP Tools (`tools/`)**
- [ ] Implement `mcp_server.py` (FastMCP main server)
- [ ] Implement `hpa_rag_search.py` — `search_hpa_guidelines` tool (enforce `exclude_medical: true` at implementation level)
- [ ] Implement `line_report_generator.py` — `generate_line_report` tool (auto-inject mandatory legal disclaimer into every message footer; make disclaimer non-removable)
- [ ] Implement `alert_history_checker.py` — `check_alert_history` tool

**Compliance Automation**
- [ ] Write `compliance/blacklist_terms.json`
- [ ] Write `compliance/whitelist_terms.json`
- [ ] Write `compliance/disclaimer_template.md`
- [ ] Build automated blacklist scanner that runs over all generated test outputs
- [ ] Prepare 50-case adversarial test suite for Phase 3 (`compliance/adversarial_test_cases.json`)

**Evaluation**
- [ ] Run 30 manually evaluated report generation cases per L2 Skill
- [ ] Audit all test outputs for prohibited term leaks

### Acceptance Criteria
| Criterion | Target |
|---|---|
| L1 routing accuracy (100-case test) | ≥ 95% |
| L2 insight quality (30-case eval per Skill) | ≥ 4/5 |
| MCP tool call success rate | ≥ 99% |
| Prohibited term leak rate (30-case test) | 0% |

---

## Phase 3 — Edge Device Integration and Compliance Hardening
**Duration:** Month 3
**Goal:** Connect to real edge device data streams, complete SaMD red-team testing, and validate alert suppression in production-like conditions.

**Dependency:** Phase 2 acceptance criteria must pass.

### Tasks

**Edge Device Integration**
- [ ] Establish secure API integration with edge devices (RK3588-class or equivalent)
- [ ] Begin processing real anonymized JSON event streams
- [ ] Run 24-hour continuous connection stability test

**Alert Suppression Validation**
- [ ] Deploy L1 alert suppression logic with `check_alert_history` integration
- [ ] Run 7-day continuous monitoring to verify daily report frequency
- [ ] Confirm `posture_change: sudden_drop` bypasses suppression and routes immediately in all test conditions

**SaMD Red-Team Testing**
- [ ] Execute full adversarial test: 50 cases designed to elicit medical diagnoses, drug recommendations, condition naming, or clinical judgments — all 50 must produce zero prohibited output
- [ ] Document all failures (if any) and fix before proceeding
- [ ] Conduct final full audit of all generated messages for disclaimer injection coverage

**Develop Remaining Skills**
- [ ] Finalize `L2-chronic-disease-observer` (if not complete)
- [ ] Finalize `L2-weekly-summary-composer` (if not complete)
- [ ] Validate both against 30-case quality eval

### Acceptance Criteria
| Criterion | Target |
|---|---|
| Red-team SaMD boundary violations | 0 / 50 cases |
| Daily report frequency per user | ≤ 1 / day |
| Disclaimer injection coverage | 100% of messages |
| Edge device connection stability | 24-hour test, zero drops |

---

## Phase 4 — LINE Integration and Field Validation
**Duration:** Month 4
**Goal:** Production-quality LINE Flex Message delivery and real-family usability validation.

**Dependency:** Phase 3 acceptance criteria must pass. Do not expose real families to the system before red-team and disclaimer coverage requirements are met.

### Tasks

**LINE Flex Message Templates**
- [ ] Design `daily_insight` Flex Message template (warm, readable card format)
- [ ] Design `weekly_summary` Flex Message template (structured weekly report layout)
- [ ] Design `immediate_alert` Flex Message template — must be **visually distinct** from routine messages (use distinct color/border treatment so families immediately recognize urgency)

**Progressive Disclosure Dialogue Flow**
- [ ] Implement LINE Bot reply handler: family replies to a report trigger deeper RAG retrieval and follow-up response
- [ ] Validate that proactive reports contain only the single most important suggestion; deeper guidance only surfaces on family request

**Field Testing**
- [ ] Recruit 10 families with genuine elderly care needs for closed-field test
- [ ] Run 4-week continuous field test
- [ ] Collect NPS survey data across: warmth, usefulness, accuracy, alert frequency comfort
- [ ] Record family reply rate via LINE backend analytics
- [ ] Tune L2 Skill tone and suggestion specificity based on family feedback

**Knowledge Base Maintenance (Establish Process)**
- [ ] Schedule quarterly HPA document review and knowledge base update cycle
- [ ] Document update process in `knowledge_base/` README

### Acceptance Criteria
| Criterion | Target |
|---|---|
| NPS score | ≥ 50 |
| Warmth rating | ≥ 4.2 / 5 |
| Accuracy rating (families confirm descriptions match reality) | ≥ 4.0 / 5 |
| Family reply rate | ≥ 30% |

---

## Full KPI Summary

| Category | Metric | Target | Measurement |
|---|---|---|---|
| Routing | L1 routing accuracy | ≥ 95% | 100-case blind test (Phase 2) |
| Knowledge | RAG passage relevance | ≥ 4/5 | 30-query human evaluation (Phase 1) |
| Compliance | SaMD boundary violations | 0% | 50-case red-team (Phase 3) |
| Compliance | Prohibited term leak rate | 0% | Full message audit (Phase 2–3) |
| Compliance | Disclaimer injection coverage | 100% | Automated audit (Phase 3) |
| User Experience | NPS score | ≥ 50 | 10-family field test (Phase 4) |
| User Experience | Warmth rating | ≥ 4.2/5 | NPS sub-item (Phase 4) |
| User Experience | Accuracy rating | ≥ 4.0/5 | NPS sub-item (Phase 4) |
| Alert Quality | Daily push frequency | ≤ 1/day | 7-day monitoring (Phase 3) |
| Engagement | Family reply rate | ≥ 30% | LINE analytics (Phase 4) |
| Maintenance | Knowledge base update cadence | Quarterly minimum | Version control records |

---

## Phase Dependencies

```
Phase 1 (Knowledge Base)
    │
    ▼ RAG live + medical filter validated
Phase 2 (Skill Development)
    │
    ▼ L1 ≥ 95% routing accuracy + zero prohibited term leaks
Phase 3 (Edge Integration + Compliance Hardening)
    │
    ▼ Red-team 50/50 pass + 100% disclaimer coverage
Phase 4 (LINE + Field Validation)
```

No phase begins until the previous phase's acceptance criteria are fully met. The compliance gate between Phase 3 and Phase 4 is the hardest constraint — real families must not be exposed to the system before the SaMD boundary is confirmed clean.
