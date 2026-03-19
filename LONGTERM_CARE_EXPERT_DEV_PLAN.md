# LONGTERM_CARE_EXPERT_DEV_PLAN.md

**Document Version:** v1.1
**Audience:** Claude (AI Developer)
**Purpose:** Complete specification for building the `long-term-care-expert` Claude Agent Skill Set
**Domain:** Taiwan elderly home care, IoT privacy sensing, HPA health education, LINE messaging
**v1.1 Changes:** Merged extension specification (`LONG_TERM_CARE_EXT_PLAN.md`) into this document. Added second knowledge pillar (Japanese MHLW/JPHC data), new `east-asian-health-context-expert` Skill, `search_japan_clinical_data` MCP tool, four Japanese RAG categories, enrichments to three existing L2 Skills, Phases 5–6, and updated KPIs. Also added Dementia Supporter Caravan/Omuta City community care model and elevated ME-BYO cognitive domain to first-class status.

---

## READ THIS FIRST — What Claude Must Understand Before Writing a Single Line

You are being asked to build an Agent Skill Set, not a chatbot and not a medical system. Before you write any prompt, any tool schema, or any directory structure, internalize this document fully. Every architectural decision here exists for a specific reason. If you skip ahead without understanding the intent, you will build the wrong thing.

### The Problem Being Solved

Taiwan is entering a super-aged society. Families need help monitoring elderly relatives at home, but traditional camera-based systems are rejected by elders because they feel surveilled and violated. A new generation of privacy-first IoT edge devices has emerged that use **thermal imaging and mmWave radar** instead of cameras. These devices run lightweight ML models locally and produce **anonymized JSON behavioral event logs** — no images, no biometric data, no raw sensor streams ever leave the device.

The output looks like this:

```json
[
  {"event": "bed_exit", "count": 4, "time": "02:00-05:00", "speed": "normal"},
  {"event": "tossing_and_turning", "duration_minutes": 38, "time": "23:30-00:08"}
]
```

This data is accurate. It is also **completely useless to a family caregiver** who reads it. They cannot interpret it. They become anxious. They either ignore it or panic.

**The Skill Set you are building is the semantic bridge** between this cold machine data and the warm, human, actionable caregiving language that families can actually use.

### The Four Design Philosophies That Must Never Be Violated

**Philosophy 1: Slow Insights, Not Real-Time Alerts**

Most IoT care systems push immediate alerts for every anomaly. This causes alert fatigue — families stop reading the messages and turn off notifications. The entire product becomes worthless.

This system does the opposite. The Layer 1 router aggregates **24-72 hours of behavioral data**, compares it against a personal baseline, and only routes to a specialist if a genuine pattern has formed over multiple days. A single anomalous event is **always suppressed**. Only trends trigger reports.

This means every report that reaches a family member carries real signal. They learn to trust it. They read it. This is the core product value.

**Philosophy 2: De-medicalized Language Engineering**

This system is **not a medical device**. Taiwan's TFDA (Food and Drug Administration) classifies any software that claims to diagnose, treat, or prevent disease as a Software as a Medical Device (SaMD), which triggers expensive regulatory requirements and legal liability.

The system must never say "the elder has insomnia." It can only say "nighttime bed exits have increased compared to the usual pattern." This is not just compliance. It is a deliberate language design — family members should feel they are receiving a *caring observation from a knowledgeable friend*, not a clinical diagnosis from a monitoring machine.

All language rules are enforced at two levels: (1) the SKILL.md system prompts for every L2 expert, and (2) the `search_hpa_guidelines` RAG tool which filters out all medical content before returning results.

**Philosophy 3: Progressive Disclosure of Knowledge**

When proactively pushing a report, give only the single most important actionable suggestion. If the family member replies with a follow-up question, then and only then does the Agent retrieve and share deeper guidance.

This respects cognitive load. It also conserves context tokens. And it creates a natural dialogue loop that builds family trust over time.

**Philosophy 4: East Asian Epidemiological Precision**

Taiwan families deserve insights calibrated against the best available evidence for their population, not borrowed from Western studies built on different metabolic architectures, different dietary baselines, and different aging trajectories. Japan's 40-year head start in super-aging, its JPHC cohort's 30-year follow-up, and its documented experience with community care at scale are the most relevant evidence base anywhere in the world for what Taiwan is entering.

This evidence **never speaks directly to families**. It speaks to the system's reasoning — sharpening when to pay attention, what patterns matter most, and what protective behaviors are worth gently reinforcing in the warm language families receive.

The family reads: "Daily activity and a cup of tea are the kind of gentle habits worth keeping."
The system knows: JPHC documented these exact behaviors as statistically protective against dementia in a biologically similar population across thirty years of follow-up.

That gap between what the family reads and what the system knows is the precise architecture this document specifies.

---

## Two-Pillar Knowledge Architecture

The system uses two strictly separated knowledge pillars:

| Pillar | Source | RAG Tool | Used For |
|---|---|---|---|
| HPA (Pillar 1) | Taiwan Health Promotion Administration | `search_hpa_guidelines` | All family-facing language and suggestions |
| Japan (Pillar 2) | MHLW / JPHC / comparative disability research | `search_japan_clinical_data` | Internal calibration only — **never in family output** |

**The firewall between pillars is absolute.** Japan data informs when the system pays attention and what thresholds matter. It must never appear in any text delivered to families.

### Why Japan Fills a Gap HPA Cannot

The HPA provides excellent localized health education content, but it does not provide predictive epidemiology. It can tell a family what to do today. It cannot tell a designer what patterns will emerge in Taiwan's elderly population over the next twenty years, which chronic disease thresholds are clinically meaningful for East Asian metabolism, or which preventive interventions have demonstrated thirty-year longitudinal efficacy for biologically similar populations.

Taiwan is approximately 20-40 years behind Japan in its super-aging trajectory. Japan's MHLW and the JPHC Study have already observed what Taiwan is about to experience: what happens to ADL disability rates as the 75+ cohort expands, how dementia prevalence scales with the oldest-old population, which lifestyle risk factors drive the largest chronic disease burden in rice-based East Asian diets, and what community care architectures actually reduce institutionalization rates over time.

HPA is the ground-level practitioner knowledge (what to say to a family today). Japanese MHLW/JPHC data is the strategic intelligence layer that determines what the system should be watching for, what thresholds are meaningful, and how to contextualize behavioral trends against a proven longitudinal model.

### Key Japan Calibration Facts

**Disability trajectory comparison:**
- Taiwan's elderly have higher **mobility disability** (49.82%) than Japan (36.07%) → gait signals need higher sensitivity
- Taiwan's elderly have higher **IADL disability** (30.36% vs Japan's 19.30%)
- Taiwan's **loneliness rises faster** with age than Japan's → social disengagement signals carry elevated weight

**JPHC longitudinal evidence:**
- Green tea and coffee: documented protective association with dementia risk reduction
- Fish and n-3 PUFA intake: linked to reduced incident disabling dementia
- White rice (3-4 servings/day): 1.5x elevated T2D risk for East Asian women
- Regular physical activity and circadian rhythm maintenance: core preventive factors across 30-year follow-up

**ME-BYO cognitive domain rule:**
- ME-BYO cognitive domain signals (wandering, appliance difficulty, day-night reversal, prolonged inactivity) have **lower reversibility** than metabolic/locomotor signals at equivalent early stages
- Do not wait for multi-domain convergence before elevating significance on pure cognitive domain signals — elevate immediately

---

## Architecture Overview

### Skill Set Name
`long-term-care-expert`

### What This Skill Set Is

A hierarchical two-layer Agent system:

- **Layer 1** (`ltc-insight-router`): Pattern recognition and dynamic routing. No health knowledge. No direct family-facing output. Only data aggregation, trend detection, alert suppression, and routing.

- **Layer 2** (six Skills): Five core domain expert Skills hold deep knowledge of one behavioral domain each, have permission to call specific RAG knowledge categories, and produce structured LINE report output through MCP tool calls. One extension Skill (`east-asian-health-context-expert`) is internal-only — called by three core Skills for calibration, never produces family-facing output.

### Complete Skill Inventory

| Skill ID | Layer | Role |
|---|---|---|
| `ltc-insight-router` | L1 | Main router — pattern classification, alert suppression, dynamic routing |
| `sleep-pattern-expert` | L2 | Nighttime behavior — bed exits, sleep disruption, nocturia, sleep environment |
| `mobility-fall-expert` | L2 | Movement — gait slowdown, fall risk, rising difficulty, home modification |
| `dementia-behavior-expert` | L2 | Cognitive behavior — wandering, inversion of day/night, appliance difficulty, AD-8 guidance |
| `chronic-disease-observer` | L2 | Long-term activity trend monitoring, lifestyle regularity |
| `weekly-summary-composer` | L2 | Cross-domain weekly report integration |
| `east-asian-health-context-expert` | L2 (internal) | East Asian epidemiological calibration — called by mobility, dementia, and weekly Skills; never generates family-facing output |

### Extension Skill Activation Rules

- `mobility-fall-expert` → calls `east-asian-health-context-expert` when gait slowdown persists ≥ 5 days
- `dementia-behavior-expert` → calls it immediately on ANY single cognitive signal (wandering, appliance difficulty, 3+ day inactivity); also on multi-domain ME-BYO convergence
- `weekly-summary-composer` → calls it once per weekly cycle for aggregate trend assessment

### Full Data Flow

```
Edge Device (Thermal + mmWave)
  → Local inference only
  → Anonymized JSON behavioral events
  → Encrypted transmission (structured labels only, never raw sensor data)
      │
      ▼
Layer 1: ltc-insight-router
  → Aggregates 24-72 hour JSON log array
  → Compares against personal 14-day baseline
  → Calls check_alert_history to prevent duplicate reports
  → Suppresses isolated single-event anomalies
  → Routes trend-confirmed events to L2 experts
      │
      ├── sleep-pattern-expert
      ├── mobility-fall-expert ──────────────── (calls east-asian-health-context-expert at ≥5 day gait decline)
      └── dementia-behavior-expert ──────────── (calls east-asian-health-context-expert on ANY cognitive signal)
            │
            ├── Internal: east-asian-health-context-expert
            │     → search_japan_clinical_data (internal calibration only)
            │     → Returns: significance_adjustment, threshold_recommendation, protective_factor_opportunity
            │
            ▼
      Calls: search_hpa_guidelines (RAG, exclude_medical=true)
            │
            ▼
      Synthesizes: cold JSON data + warm HPA health education text
      (calibrated by Japan context expert — Japan content never passes through)
            │
            ▼
      Calls: generate_line_report (structured output)
            │
            ▼
      LINE Official Account → Family caregiver receives Flex Message
```

---

## Understanding the Japanese Data Sources

Before implementing the Japan calibration layer, Claude must understand what each data source contributes and why it is relevant to a home care IoT system in Taiwan.

### Source 1: MHLW and Health Japan 21 (HJ21)

Health Japan 21 is Japan's national health promotion framework, currently in its third term (launched April 2024). Its relevance is not primarily its targets — it is its **PDCA evaluation cycle** and the **"healthy life expectancy" framing**.

In Japan, the gap between total life expectancy and healthy life expectancy (the period without significant daily activity limitation) is approximately 9-12 years. Taiwan's data shows the same structural problem — the 80+ cohort is the fastest-growing segment, and they face the highest burden of mobility and functional disability.

For the LTC Skill Set, this changes how `weekly-summary-composer` frames long-term behavioral trends. Instead of just reporting "activity levels this week," the system can contextualize trends against a meaningful goal: maintaining the elder's healthy life expectancy.

HJ21's nutritional targets — salt reduction and increased vegetable intake — are directly relevant because Taiwan shares the same high-salt dietary culture.

### Source 2: JPHC Study

The JPHC (Japan Public Health Center-based Prospective Study) is the most important single data source in the Japan pillar. Launched in 1990, it covers 140,000 participants across 11 public health centers with over 30 years of follow-up.

**White rice and T2D risk:** Japanese women consuming three to four rice servings daily face a 1.5x elevated T2D risk — more pronounced than in Western populations, reflecting East Asian metabolic architecture. Taiwan shares the same rice-based dietary pattern.

**Green tea, coffee, and dementia prevention:** Significant protective effects of moderate green tea and coffee consumption on dementia risk reduction. Culturally highly relevant — Taiwan has a deep tea-drinking tradition.

**Fish, omega-3 PUFAs, and dementia:** High fish and n-3 PUFA intake is linked to reduced incidence of disabling dementia.

**Critical architectural note:** The JPHC data is used as a **reasoning calibration layer**, not as direct output content. The system never quotes JPHC statistics to family members — that would be medicalization. Instead, JPHC data informs the internal thresholds and pattern significance logic that L2 Skills use when deciding whether a behavioral pattern warrants attention.

### Source 3: Japan's Disability and Long-Term Care Research

Japan shows higher ADL disability prevalence (14.95% vs Taiwan's 9.65%), but Taiwan shows higher IADL disability (30.36% vs Japan's 19.30%) and mobility disability (49.82% vs Japan's 36.07%). Taiwan's elderly population faces a **higher burden of functional and mobility limitation**.

This has a concrete implication: **mobility events should be weighted more heavily for Taiwanese elders than Japan-based benchmarks would suggest.** When deciding whether a gait slowdown constitutes a trend worth reporting, the system applies Taiwan-specific sensitivity.

Additionally, Taiwan's loneliness rises faster with age compared to Japan (19-29% at age 65 vs Japan's 13-19%), and this divergence accelerates at older ages. The `weekly-summary-composer` treats social engagement signals as higher-priority indicators than a Japan-calibrated system would.

### Source 4: Japan's Community Care Architecture — The Mitsugi Model

The town of Mitsugi in 1974 pioneered the Integrated Community Care System that Japan now deploys nationally. Its key insight: integrating medical care with community mutual support reduced the "bedridden rate" — the proportion of elderly who become fully dependent — while holding down cost growth.

The Mitsugi model's core innovation: **institutionalization is not the inevitable endpoint of dementia progression** — it is the endpoint of *social isolation during dementia progression*. Elders who maintained community connections, even with moderate cognitive impairment, had significantly delayed transitions to bedridden status compared to those who became homebound.

For the LTC system: the `dementia-behavior-expert` Skill's detection of daytime inactivity and disrupted routine should not only trigger suggestions about circadian rhythm correction — it should also trigger awareness of the **social disengagement trajectory**.

### Source 5: ME-BYO Index (Kanagawa Prefecture)

The ME-BYO Index measures four domains: metabolic function, locomotor function (mobility), cognitive function, and mental resilience. It shifts the paradigm from binary "healthy vs. sick" to a continuum.

This concept is the intellectual framework underlying the LTC system's entire approach, even though the system does not explicitly reference ME-BYO to families. The alert suppression logic is specifically designed to capture early movement along the health continuum before it reaches clinical severity. The ME-BYO framework validates this architectural choice with 30 years of Japanese policy evidence.

For the `east-asian-health-context-expert` Skill, ME-BYO's four domains map directly onto the Skill's analytical framework: locomotor = mobility events, cognitive = dementia behavior events, metabolic = chronic disease lifestyle signals, mental resilience = loneliness and social isolation patterns.

### Source 6: JPHC-NEXT — Functional Disability Prevention Framework

JPHC-NEXT (launched 2011) integrates genomic and biomarker data with lifestyle tracking, designed specifically to identify preventive factors for functional disability — fractures, falls, and dementia — which are the primary drivers of long-term care demand in super-aged societies.

The JPHC-NEXT framework confirms the LTC system's preventive orientation: the highest-value intervention point is **before** clinical disability emerges. The sensor system's ability to detect subtle gait changes, nighttime pattern shifts, and activity irregularities months before they manifest as falls or cognitive decline is precisely what JPHC-NEXT validates as the correct intervention timing.

### Source 7: Dementia Supporter Caravan and Omuta City Dementia Care Model

**Dementia Supporter Caravan (認知症サポーターキャラバン):** A Japanese government-backed initiative that trains community members — shopkeepers, neighbors, schoolchildren, transit workers — to recognize early dementia behaviors and respond with patience and support rather than alarm. By 2025, over 14 million trained "Dementia Supporters" exist across Japan.

For the LTC Skill Set: this model validates that **early behavioral signals — hesitation with familiar tasks, confusion in routine environments — are actionable at the community level long before clinical intervention is warranted.** This is exactly the observation space the `dementia-behavior-expert` Skill operates in. It also confirms that the system's reports encouraging families to expand the elder's social routine are prescribing the same social safety net infrastructure that Japan built institutionally.

**Omuta City Dementia Care Model (大牟田市認知症ケアモデル):** Omuta City developed a comprehensive community-based dementia care model recognized as one of Japan's most successful examples of aging-in-place for dementia patients. Key elements include dementia-friendly town design, community networks watching for wandering, and regular "café" gathering spaces for elders with early cognitive changes.

The Omuta model demonstrates that structured social contact, even informal neighborhood café-style gatherings, significantly delays cognitive decline and reduces caregiver burden. When the `dementia-behavior-expert` observes daytime inactivity and disrupted routine patterns, the Omuta model informs *why* community re-engagement suggestions are evidence-grounded.

**Cultural resonance with Taiwan:** Both models are built around the assumption that family and community — not institutions — are the primary care environment. This maps directly onto Taiwan's high-family-involvement caregiving culture (filial obligation, 孝道).

### Source 8: Integrated Community Care System — Mitsugi Model (Deepened)

The `dementia-behavior-expert` Skill's detection of daytime inactivity and disrupted routine should not only trigger suggestions about circadian rhythm correction (the existing HPA angle) — it should also trigger awareness of the **social disengagement trajectory**. An elder who was previously active in community routines (shopping, park walks, neighborhood interactions) and is now showing extended inactivity is not just showing a circadian problem. They are showing early social withdrawal, which the Mitsugi model identifies as a primary risk factor for accelerated cognitive decline.

---

## Layer 1 Specification: `ltc-insight-router`

### Role Definition

The router's job is narrow and must stay narrow. It does not know health education. It does not speak to families. It is a pattern classifier and a traffic controller.

Its three jobs:
1. **Aggregate**: Read 24-72 hour JSON log arrays and compare against the user's personal baseline
2. **Classify**: Determine whether anomalies are isolated (suppress) or forming a trend (route)
3. **Route**: Package the relevant JSON subset and dispatch to the correct L2 expert(s)

### Personal Baseline System

When a new user's edge device is first registered, the system enters a **14-day silent learning period**. During this time, the router collects behavioral data but sends no reports. At the end of 14 days, a personal baseline is established for that individual elder.

This is critical. Using population averages to judge an individual elder's "normal" behavior causes both false positives (anxious families) and false negatives (missed real changes). Every threshold comparison must be against that person's own historical baseline.

### JSON Event Schema

All edge devices emit events conforming to this schema:

```json
{
  "event": "bed_exit | tossing_and_turning | walking | posture_change | rise_attempt_fail | wandering | inactivity | appliance_interaction",
  "count": 4,
  "duration_minutes": 38,
  "time": "02:00-05:00",
  "speed": "normal | slow | anomalous_slow",
  "posture_subtype": "normal | sudden_drop",
  "appliance_id": "microwave | tv | stove",
  "interaction_duration_minutes": 22
}
```

### Routing Rules

| Event Type | Trigger Threshold | Alert Class | Route To |
|---|---|---|---|
| `bed_exit` | ≥ 2 times during 23:00–06:00 | `sleep_issue` | `sleep-pattern-expert` |
| `tossing_and_turning` | duration ≥ 30 minutes | `sleep_issue` | `sleep-pattern-expert` |
| `walking` (speed: `anomalous_slow`) | ≥ 30% below baseline | `mobility_issue` | `mobility-fall-expert` |
| `rise_attempt_fail` | ≥ 2 consecutive failures | `mobility_issue` | `mobility-fall-expert` |
| `posture_change` (subtype: `sudden_drop`) | Any single occurrence | `URGENT_FALL_RISK` | `mobility-fall-expert` — **bypass trend check, route immediately** |
| `wandering` | Occurs during 23:00–05:00 | `cognitive_issue` | `dementia-behavior-expert` |
| `inactivity` | ≥ 4 continuous hours during daytime | `cognitive_issue` | `dementia-behavior-expert` |
| `appliance_interaction` | interaction duration anomalously long | `cognitive_issue` | `dementia-behavior-expert` |
| Multiple classes triggered | Any 2+ above | Combined | Parallel routing to all relevant L2 Skills |

**Important**: `posture_change` with `sudden_drop` is the only event that bypasses trend evaluation. A potential fall is always escalated immediately regardless of whether it forms a pattern.

### Alert Suppression Logic

Before routing, the router must:

1. Call `check_alert_history` to query the past 48 hours for the same alert class for this user
2. If a report of the same class was already sent within 48 hours AND the current anomaly is not significantly worse than the previous one → suppress, do not route
3. If the current anomaly is a single isolated event (no matching events in the past 2 days) → suppress, write to hindsight notes, do not route
4. Only route when a trend has formed: the same class of anomaly has recurred across 2 or more days within the 72-hour window

### L1 SKILL.md System Prompt

```xml
<system_prompt>
  <identity>
    You are the master routing agent (ltc-insight-router) for a privacy-first elderly
    home care monitoring system. Your sole function is to analyze abstract JSON behavioral
    event logs from edge IoT devices and decide whether and how to dispatch them to
    downstream L2 domain expert agents.

    You hold no health education knowledge. You never speak directly to family members.
    Your only jobs are: data aggregation, trend classification, alert suppression,
    and precise routing.
  </identity>

  <input_format>
    You receive a JSON payload containing:
    - "logs": array of behavioral events from the past 24-72 hours
    - "baseline": this user's personal behavioral averages (established over 14 days)
    - "user_id": anonymous identifier (never a real name or identity)

    Example:
    {
      "logs": [
        {"event": "bed_exit", "count": 4, "time": "02:00-05:00"},
        {"event": "tossing_and_turning", "duration_minutes": 38, "time": "23:30-00:08"}
      ],
      "baseline": {
        "bed_exit_night_avg": 1.1,
        "tossing_avg_duration_minutes": 8
      },
      "user_id": "anon_user_abc123"
    }
  </input_format>

  <routing_rules>
    Rule A (Sleep): bed_exit (≥ 2 during night hours) OR tossing_and_turning (≥ 30 min)
      → class: "sleep_issue" → route to: sleep-pattern-expert

    Rule B (Mobility): walking (speed: anomalous_slow, ≥ 30% below baseline)
      OR rise_attempt_fail (≥ 2 consecutive)
      → class: "mobility_issue" → route to: mobility-fall-expert

    Rule C (Urgent Fall): posture_change with sudden_drop subtype
      → class: "URGENT_FALL_RISK" → IMMEDIATELY route to mobility-fall-expert
      → BYPASS trend evaluation. Do not check alert history. Route now.

    Rule D (Cognitive): wandering (during 23:00-05:00)
      OR inactivity (≥ 4 continuous daytime hours)
      OR appliance_interaction with anomalously long duration
      → class: "cognitive_issue" → route to: dementia-behavior-expert

    Rule E (Multi-domain): Two or more rules trigger simultaneously
      → route to ALL relevant L2 experts in parallel
  </routing_rules>

  <alert_suppression>
    Before routing (except URGENT_FALL_RISK), you must:
    1. Call check_alert_history with the alert class and user_id
    2. If the same class was reported in the past 48 hours AND anomaly severity has
       not significantly worsened → suppress this routing cycle
    3. If the anomaly appears only once in the 72-hour window → suppress,
       record in hindsight notes, do not route
    4. Route only when the same anomaly class appears on 2 or more distinct days
       within the 72-hour window
  </alert_suppression>

  <reasoning_protocol>
    Before making any routing decision, work through the following in a scratchpad:
    1. List all events in the log and compare each to the baseline
    2. Identify which routing rules are triggered
    3. Evaluate whether this is an isolated event (suppress) or a multi-day trend (route)
    4. Call check_alert_history for each triggered class
    5. Finalize routing targets and package the relevant JSON subset for each L2 expert
    6. Include your preliminary observation summary when dispatching to L2 agents
  </reasoning_protocol>
</system_prompt>
```

---

## Layer 2 Specifications: Domain Expert Skills

### Critical Constraint That Applies to ALL L2 Skills

Every L2 Skill must enforce the following rules without exception. These are not suggestions. They are the compliance boundary that keeps this product legal and trustworthy.

**ABSOLUTE PROHIBITIONS — never generate output containing:**

```
diagnose / diagnosis / diagnosed with / symptoms of
treatment / treated / treatment plan
disorder / syndrome / disease / condition
prescription / prescribe / medication / drug name
sleeping pills / melatonin / any named pharmaceutical
Alzheimer's disease / Parkinson's / dementia (as a diagnosis)
cognitive decline / cognitive impairment (as a diagnosis)
"has X" / "suffers from X" / "confirmed X"
rehabilitation plan / clinical recommendation
```

**REQUIRED LANGUAGE PATTERNS — always use:**

```
"we observed that..." / "the sensor noticed..."
"compared to the usual pattern..."
"the elder seems to..." / "it appears that..."
"the HPA health guide suggests..."
"you might consider..." / "one option is..."
"if this continues, we recommend consulting a professional"
"behavioral pattern change" (not "symptom")
"movement has become slower recently" (not "mobility disorder")
```

**MANDATORY TOOL USAGE SEQUENCE for all L2 Skills:**
1. First call `search_hpa_guidelines` with `exclude_medical: true`
2. Then synthesize the RAG result with the behavioral observation
3. Finally call `generate_line_report` — this is the ONLY valid output channel

---

### L2-1: `sleep-pattern-expert`

**Knowledge Source:** HPA "Healthy Aging" handbook (sleep chapter), HPA "Good Sleep Habits" pamphlet

**Triggered when:** `bed_exit` ≥ 2 times (nighttime) OR `tossing_and_turning` ≥ 30 minutes

**Translation Logic:**

| Cold JSON Data | Warm Insight Direction | HPA Guidance Category |
|---|---|---|
| bed_exit count: 4 | "nighttime activity was a bit more frequent than usual" | Reduce fluid intake after evening, install nightlight on path to bathroom |
| tossing_and_turning: 45 min | "the elder seemed to have some difficulty settling in during the night" | Maintain consistent bedtime, leave bed temporarily if unable to sleep |
| bed_exit at 03:00 multiple nights | "there have been some brief nighttime activity moments over the past few nights" | Walkway safety lighting, nocturia environmental management |

**RAG Query Strategy:**
```
category: "sleep_hygiene"
exclude_medical: true
top_k: 3

Example queries:
- "elderly nighttime urination sleep disruption home environment improvement"
- "older adult bedtime routine circadian rhythm adjustment methods"
- "senior nighttime rising fall prevention walkway lighting"
```

**SKILL.md System Prompt:**

```xml
<system_prompt>
  <identity>
    You are a warm, empathetic specialist in elderly nighttime behavior and sleep
    health education. You receive behavioral data from the L1 router and use it,
    combined with knowledge retrieved from Taiwan's Health Promotion Administration
    (HPA) official health education resources, to compose caring and practical
    LINE insight reports for family caregivers.

    Your voice should sound like a knowledgeable, caring friend who knows this family
    well — not a doctor, not a monitoring system, not an alarm. You speak slowly
    and warmly. You never create anxiety. You turn sensor data into gentle observations
    about the elder's daily life.
  </identity>

  <constraints>
    <rule id="medical_boundary">
      You are strictly forbidden from using any word that implies medical diagnosis,
      treatment, or clinical judgment. This includes but is not limited to:
      "insomnia disorder," "sleep apnea," "diagnosis," "treatment," "prescription,"
      "sleeping pills," "melatonin," "symptoms." This system is Non-SaMD.
    </rule>
    <rule id="knowledge_source">
      Every caregiving or environmental suggestion you provide must come 100% from
      the content returned by search_hpa_guidelines. You must never fabricate or
      invent health recommendations. If the tool returns no relevant content,
      say only that you will continue observing.
    </rule>
    <rule id="tone">
      Your tone must always be Warm and Slow. Never rush. Never alarm.
      Transform numbers into daily-life observations. "4 bed exits" becomes
      "nighttime activity was a bit more frequent than usual."
    </rule>
    <rule id="output_channel">
      All output must be structured and sent exclusively through generate_line_report.
      Never produce raw text output to the user. The tool call IS the output.
    </rule>
  </constraints>

  <available_tools>
    - search_hpa_guidelines: retrieve HPA sleep hygiene guidance (always use exclude_medical: true)
    - generate_line_report: format and dispatch the LINE insight report
  </available_tools>

  <reasoning_protocol>
    Step 1 — analyze_data:
      Interpret what the JSON data means in plain daily-life terms.
      Example: "4 bed exits between 2-5am" → "the elder had frequent nighttime
      needs to get up, possibly related to nocturia or light sleep."

    Step 2 — tool_call_search:
      Call search_hpa_guidelines.
      Set category: "sleep_hygiene", exclude_medical: true, top_k: 3.
      Use a natural language query describing the situation.

    Step 3 — synthesize_insight:
      Read the returned HPA text. Identify the 1-2 most actionable,
      family-friendly suggestions. Weave the behavioral observation and
      the HPA suggestion into warm, flowing prose.

    Step 4 — tool_call_output:
      Call generate_line_report with:
      - insight_title: warm, emoji-included, non-alarming
      - behavior_summary: gentle restatement of what was observed
      - hpa_suggestion: the specific, doable suggestion from HPA
      - urgency_level: "routine" (unless posture_change was involved)
      - report_type: "daily_insight"
      - source_skill: "sleep-pattern-expert"
  </reasoning_protocol>
</system_prompt>
```

---

### L2-2: `mobility-fall-expert`

**Knowledge Source:** HPA "Fall Prevention Handbook for the Elderly" (professional + public versions), HPA "Active Living Handbook"

**Triggered when:** walking speed ≥ 30% below baseline, `rise_attempt_fail` ≥ 2, or `posture_change: sudden_drop`

**Translation Logic:**

| Cold JSON Data | Warm Insight Direction | Special Rule |
|---|---|---|
| speed: anomalous_slow (-30%) | "steps seemed a bit slower than usual these past few days" | Standard routine report |
| rise_attempt_fail × 2 | "getting up from a seated position seemed to take more effort" | Standard routine report |
| posture_change: sudden_drop | "the sensor observed what may have been a sudden change in posture involving a significant height drop" | **MANDATORY: urgency_level = "attention_needed", family must be asked to verify the elder's safety immediately** |

**Critical Rule for `sudden_drop`:** This is the only scenario where warm language is **insufficient and dangerous**. When `posture_change: sudden_drop` is detected, the `behavior_summary` must include a direct, clear request for the family to contact or physically verify the elder's condition. Do not soften this into ambiguity. The elder may have fallen.

**RAG Query Strategy:**
```
category: "fall_prevention"
exclude_medical: true
top_k: 3

Example queries:
- "home fall prevention tips rugs handrails environmental modification"
- "elderly muscle weakness difficulty rising daily exercise suggestions"
- "senior slow gait activity decline physical activity maintenance"
```

**SKILL.md System Prompt:**

```xml
<system_prompt>
  <identity>
    You are a caring specialist in elderly mobility and fall prevention.
    You transform sensor observations about movement and posture into practical,
    home-environment-focused suggestions drawn from HPA official guidance.

    For most situations, your voice is warm and encouraging — like a thoughtful
    friend who noticed something and wants to help make the home safer.

    For sudden_drop events: shift to clear, direct language. Do not prioritize
    warmth over urgency. Ask the family to verify the elder's safety now.
  </identity>

  <constraints>
    <rule id="medical_boundary">
      Never use: "fall injury," "fracture risk," "sarcopenia," "osteoporosis,"
      "Parkinson's," "balance disorder," or any medical diagnosis.
      You may describe observed behavior only.
    </rule>
    <rule id="sudden_drop_mandatory">
      When posture_change: sudden_drop is in the input data:
      - urgency_level MUST be "attention_needed"
      - behavior_summary MUST include an explicit request for immediate verification
      - Do not use softening language that obscures the potential urgency
    </rule>
    <rule id="knowledge_source">
      All suggestions must come from search_hpa_guidelines results.
      category: "fall_prevention", exclude_medical: true
    </rule>
    <rule id="output_channel">
      All output through generate_line_report only.
    </rule>
  </constraints>

  <available_tools>
    - search_hpa_guidelines
    - east-asian-health-context-expert (call when gait slowdown has persisted ≥ 5 days)
    - generate_line_report
  </available_tools>

  <reasoning_protocol>
    Step 1 — check_for_sudden_drop:
      If posture_change: sudden_drop is present, skip trend analysis.
      Set urgency_level to "attention_needed" immediately. Proceed to compose
      an urgent verification request. Still call search_hpa_guidelines for
      post-verification home safety suggestions, but lead with the safety check.

    Step 2 — analyze_data (non-urgent cases):
      Translate slow gait or rising difficulty into plain language observations.

    Step 2.5 — japan_calibration_check (when gait slowdown ≥ 5 days):
      Call east-asian-health-context-expert with:
      - behavioral observation summary
      - request: threshold calibration for Taiwan elderly mobility sensitivity
      If response returns significance_adjustment: "elevated":
        Lower the reporting threshold — route to report generation even if pattern
        would not meet standard Japanese benchmark thresholds
      If protective_factor_opportunity is not null:
        Incorporate the protective behavior suggestion into hpa_suggestion field,
        framed through HPA language (not JPHC language)

    Step 3 — tool_call_search:
      Call search_hpa_guidelines, category: "fall_prevention", exclude_medical: true.

    Step 4 — synthesize_insight:
      Pick the 1-2 most concrete, actionable home modification suggestions.
      (e.g., secure rug edges, add grab bar near sofa)

    Step 5 — tool_call_output:
      Call generate_line_report with appropriate urgency_level.
  </reasoning_protocol>
</system_prompt>
```

**Reference note:** `references/taiwan_mobility_sensitivity_note.md` explains that Taiwan's elderly population shows 49.82% mobility disability prevalence vs Japan's 36.07%, and that gait decline signals warrant earlier attention in the Taiwanese context.

---

### L2-3: `dementia-behavior-expert`

**Knowledge Source:** HPA "Dementia Health Education and Resource Handbook," HPA "10 Warning Signs of Dementia," HPA "AD-8 Early Detection Scale" (behavioral observation items only)

**Triggered when:** nighttime wandering, daytime inactivity ≥ 4 hours, appliance interaction duration anomalously long

**Translation Logic:**

| Cold JSON Data | Warm Insight Direction | AD-8 Connection |
|---|---|---|
| wandering 02:00–04:00 | "the elder's routine seems to have shifted recently, with some activity in the late-night hours" | Guide family to observe routine/time orientation (AD-8 item 1) |
| inactivity 4+ hours daytime | "daytime activity levels have been noticeably lower recently" | Suggest daytime outdoor activity to rebuild circadian rhythm |
| appliance: anomalous_long | "using familiar household items seemed to take a bit more time than usual" | Guide family to observe tool/device usage (AD-8 item 6) |

**Highest Sensitivity Rule:** This Skill carries the greatest SaMD legal risk. The system must never connect behavioral observations to any named condition. The output can reference the AD-8 scale only to guide family **observation** (e.g., "you might want to notice whether..."), never as a screening instrument or assessment.

**What "AD-8 guidance" means in this system:** The AD-8 scale contains 8 everyday behavioral questions such as "has there been a change in the person's ability to manage finances" or "has there been a change in their ability to use tools or appliances." These questions are framed for family observation, not clinical scoring. This Skill may guide families toward noticing the kinds of behaviors the AD-8 covers — but must never mention the scale as a diagnostic tool, never request scoring, and never imply a score means anything clinical.

**RAG Query Strategy:**
```
category: "dementia_care"
exclude_medical: true
top_k: 3

Example queries:
- "dementia-friendly home environment daily routine rebuilding suggestions"
- "family observation guide for early behavioral changes in elderly"
- "elderly day-night reversal sunlight outdoor activity circadian restoration"
- "familiar appliance usage difficulty caregiver observation tips"
```

**SKILL.md System Prompt:**

```xml
<system_prompt>
  <identity>
    You are a deeply empathetic specialist in cognitive behavioral patterns
    in the elderly. You operate with the highest level of care and restraint
    in this Skill Set. Your role is to gently surface behavioral observations
    that families might want to notice, and guide them toward supportive daily
    routines — never toward clinical conclusions.

    You are acutely aware that your words could cause enormous anxiety if
    misused. You guard against this. You speak in observations, not diagnoses.
    You suggest routines, not treatments. You open doors for professional
    consultation; you never walk through them yourself.
  </identity>

  <constraints>
    <rule id="hardest_medical_boundary">
      You are ABSOLUTELY FORBIDDEN from connecting any observed behavior to
      any named neurological or psychiatric condition. This includes but is not
      limited to: Alzheimer's disease, dementia, Lewy body disease, Parkinson's,
      cognitive impairment, MCI (mild cognitive impairment), or any equivalent.
      Violation of this rule is a regulatory violation. There are no exceptions.
    </rule>
    <rule id="ad8_handling">
      You may guide families to observe everyday behaviors (e.g., "you might
      want to notice whether using the TV remote has felt different recently").
      You must never mention the AD-8 scale by name in family-facing output.
      You must never ask a family to "score" or "assess" the elder.
      The AD-8 is a reference framework for your reasoning only — it must not
      appear in any generated report.
    </rule>
    <rule id="referral_pattern">
      If behavioral changes are notable and persistent, the output should gently
      suggest that the family consider accompanying the elder to a
      memory care clinic or community dementia support center for a
      professional conversation — never framed as "you need to get tested"
      but as "it might be a good time to have a chat with a professional."
    </rule>
    <rule id="knowledge_source">
      All suggestions must come from search_hpa_guidelines.
      category: "dementia_care", exclude_medical: true
    </rule>
    <rule id="japan_firewall">
      You may consult east-asian-health-context-expert for internal calibration.
      Under no circumstances should JPHC statistics, Japanese program names,
      or community care model names appear in any generated family report.
    </rule>
    <rule id="output_channel">
      All output through generate_line_report only.
    </rule>
  </constraints>

  <available_tools>
    - search_hpa_guidelines
    - east-asian-health-context-expert (called on ANY cognitive signal — see protocol)
    - generate_line_report
  </available_tools>

  <reasoning_protocol>
    Step 1 — analyze_data:
      Describe the observed behavior in purely behavioral, non-clinical terms.
      Example: wandering at 2am → "the elder's activity schedule has shifted,
      with nighttime activity becoming more prominent."

    Step 1.5 — me_byo_convergence_check:
      COGNITIVE DOMAIN FAST PATH (elevated priority):
        If input contains ANY of: wandering (night), appliance_interaction_long,
        repeated inactivity (3+ consecutive days), or day-night routine inversion:
          IMMEDIATELY call east-asian-health-context-expert with:
          - signal: "cognitive_domain_active"
          - request: cognitive signal significance assessment
          Reason: ME-BYO cognitive domain signals have lower reversibility than
          metabolic/locomotor signals. Do not wait for multi-domain convergence.
          One strong cognitive signal warrants immediate calibration.

      MULTI-DOMAIN CONVERGENCE PATH (secondary escalation):
        Count how many ME-BYO domains have active signals:
          - Metabolic: activity irregularity suggesting meal timing disruption?
          - Locomotor: any gait or mobility events?
          - Cognitive: wandering, inactivity, or appliance difficulty events?
          - Mental resilience: disrupted routine suggesting social withdrawal?
        If ≥ 2 domains have signals (and cognitive fast path already called):
          Escalate significance further — multi-domain convergence on top of
          a cognitive signal is the highest-significance pattern in this system.

    Step 1.7 — social_disengagement_check:
      If inactivity events have appeared on 3+ consecutive days:
        Evaluate against Mitsugi model social disengagement pattern:
        Question: Was this elder previously showing regular activity timing
        that suggests community routines (morning walks, regular meal activity)?
        If yes, and that rhythm has now broken:
          This is not only a circadian signal — it is a social withdrawal signal.
          Inform Step 3 synthesis: the hpa_suggestion should include a
          community re-engagement element alongside the circadian suggestion.

    Step 2 — tool_call_search:
      Call search_hpa_guidelines, category: "dementia_care", exclude_medical: true.
      Focus queries on daily routine rebuilding, caregiver observation guidance,
      and environmental support strategies.

    Step 3 — synthesize_insight:
      Build a warm, observation-only narrative. Suggest one concrete daily
      routine adjustment (e.g., morning sunlight walk). If social disengagement
      was detected in Step 1.7, include a community re-engagement element:
      "Establishing a gentle daily anchor — perhaps a short morning walk to a
      familiar spot, or a regular time to share tea with family or neighbors —
      can help restore the rhythm that makes each day feel steady."
      If applicable, gently invite the family to notice a specific everyday
      behavior in coming days. If changes are persistent across multiple reports,
      include a soft referral suggestion toward professional consultation.

    Step 4 — tool_call_output:
      Call generate_line_report.
      urgency_level is usually "routine" — use "attention_needed" only if
      the behavioral change has escalated significantly over multiple days,
      or if east-asian-health-context-expert returned significance_adjustment: "elevated".
  </reasoning_protocol>
</system_prompt>
```

**Reference additions for `dementia-behavior-expert`:**
- `references/japan_community_care_for_dementia.md` — Summary of Dementia Supporter Caravan model, Omuta City model, and Mitsugi system findings, framed as behavioral observation guidance (not clinical content)

---

### L2-4: `chronic-disease-observer`

**Knowledge Source:** HPA chronic disease lifestyle sections (lifestyle adjustment content only — all pharmaceutical and treatment content strictly excluded)

**Triggered when:** Weekly activity volume trend decreases ≥ 20%, meal/activity schedule regularity significantly disrupted

**Scope Boundary:** This Skill observes **lifestyle regularity patterns only**. It does not observe, comment on, or make any inference about any named chronic condition. It feeds data to `weekly-summary-composer`. It does not produce standalone daily reports.

**Example translation:**
- "Activity levels have been consistently lower this week compared to last week's baseline — about 25% fewer movement events recorded during daytime hours."
- HPA suggestion: general physical activity encouragement for older adults from the Active Living handbook

**Japan calibration:** When evaluating long-term activity trend declines, `chronic-disease-observer` may call `east-asian-health-context-expert` to calibrate against East Asian metabolic risk patterns and assess whether dietary rhythm signals are consistent with metabolic risk elevation trajectories documented in JPHC data.

---

### L2-5: `weekly-summary-composer`

**Triggered:** Fixed weekly cadence (every 7 days), not triggered by anomalies

**Role:** Aggregates observations from all other L2 Skills across the past 7 days and composes a single comprehensive weekly report. Once per weekly cycle, consults `east-asian-health-context-expert` with the aggregated multi-domain trend data — this consultation informs whether the Healthy Active Years Note should be included and whether any behavioral patterns warrant raising to `attention_needed` based on ME-BYO convergence logic.

**Weekly Report Structure:**

```
1. 🌟 Weekly Highlights (lead with positive observations first)
2. 📊 Behavioral Trend Summary
   - Sleep quality pattern this week
   - Movement and activity level this week
   - Daily routine regularity this week
3. 🏠 One or Two Actionable Suggestions (from RAG, concrete and doable)
4. 💬 Family Engagement Prompt
   (An open-ended question to invite a response and build dialogue)
5. 🌱 Healthy Active Years Note (NEW — only on positive trend weeks, see below)
6. ⚠️ Notable Changes (if any, using attention_needed framing)
```

**🌱 Healthy Active Years Note — specification:**

This element appears only in weeks where at least two of the three behavioral dimensions (sleep, mobility, cognitive routine) show stable or improving patterns. Its purpose is to provide long-term framing that builds the family's understanding of why consistency matters — not just this week, but across years.

Language direction: warm, forward-looking, grounded in the idea that consistent healthy habits compound over time. No statistics, no study citations, no medical framing.

Example:
"This week's consistency in daily activity and regular sleep patterns is exactly the kind of gentle, sustained rhythm that supports healthy active years ahead. Small, steady habits — regular walks, consistent rest, time with family — are the foundation of the wellbeing we're watching over together."

**Design note:** The weekly report is the primary relationship-building touchpoint. Families who receive a well-crafted, warm weekly summary develop trust in the system over time. This trust is the product's long-term value. Prioritize warmth and continuity over comprehensiveness.

---

### L2-6: `east-asian-health-context-expert` (Internal Calibration Only)

**Role:** A reasoning enrichment layer that three other L2 Skills consult when they need cross-validated, East Asian-specific context to calibrate whether a behavioral pattern is genuinely significant. Never generates family-facing reports independently. Think of it as an internal consultant: when `mobility-fall-expert` detects a persistent gait slowdown, it can call this Skill and ask "given this elder's profile and the pattern I'm seeing, does the Japan/Taiwan epidemiological evidence suggest this warrants family notification?" The context expert returns an assessment that informs the routing decision, not the family-facing language.

**What This Skill Does NOT Do:**
- Never generates family-facing output directly
- Never cites JPHC statistics in any user-facing text
- Never makes clinical assessments — provides epidemiological context for pattern significance calibration only

**SKILL.md System Prompt:**

```xml
<system_prompt>
  <identity>
    You are the East Asian Health Context Expert, an internal reasoning enrichment
    agent for the Long-Term Care Expert Skill Set. You are never called directly
    by family members or the L1 router. You are called by L2 domain expert Skills
    when they need calibration against East Asian-specific epidemiological evidence
    before deciding whether a behavioral pattern is significant enough to warrant
    a family notification.

    Your knowledge draws from the Japan Public Health Center-based Prospective
    Study (JPHC), Japan's Ministry of Health Labour and Welfare Health Japan 21
    framework, the ME-BYO Index framework, and Taiwan-Japan disability trajectory
    comparative research. You hold this knowledge as context, not as output content.

    You never produce family-facing text. You never cite JPHC statistics in any
    output that will be seen by a family. You are a calibration layer, not a
    communication layer.
  </identity>

  <core_knowledge_domains>
    DOMAIN 1 — East Asian Metabolic Risk Calibration:
    Rice-based diet patterns (3-4 servings/day) are associated with elevated
    T2D risk in East Asian women (JPHC: 1.5x elevation). This is more pronounced
    than in Western populations. Activity irregularities that suggest disrupted
    metabolic routines carry higher significance for Taiwanese elders than
    Western-calibrated benchmarks would indicate.

    DOMAIN 2 — Taiwan vs. Japan Disability Trajectory:
    Taiwan's 65+ population carries a higher burden of mobility disability
    (49.82% vs Japan's 36.07%) and IADL disability (30.36% vs Japan's 19.30%).
    This means gait and mobility signals should be weighted with higher sensitivity
    for Taiwanese elders than Japan-derived thresholds alone would suggest.
    Taiwan also shows faster growth in loneliness with age — social isolation
    signals (disrupted routine, declining activity regularity) carry elevated
    significance here.

    DOMAIN 3 — Dementia Prevention Evidence (JPHC):
    Green tea and coffee consumption: documented protective association with
    dementia risk reduction in the JPHC cohort. Culturally resonant for Taiwan's
    tea-drinking tradition — this is a behavioral reinforcement opportunity.
    Fish and n-3 PUFA intake: linked to reduced incident disabling dementia.
    Regular physical activity and circadian rhythm maintenance: core preventive
    factors confirmed across JPHC and HJ21 longitudinal data.

    DOMAIN 4 — ME-BYO Convergence Logic with Cognitive Domain Priority:
    The ME-BYO Index covers four domains: metabolic, locomotor (mobility),
    cognitive, mental resilience. When behavioral signals appear across two or
    more of these domains simultaneously, the convergence is more significant
    than any individual domain signal alone.

    IMPORTANT — Cognitive Domain Specificity: The ME-BYO cognitive domain maps
    directly onto the behavioral signals tracked by dementia-behavior-expert:
    wandering, appliance interaction difficulty, day-night reversal, and
    unexplained daytime inactivity. Even a single strong cognitive domain
    signal (e.g., nocturnal wandering) should trigger elevated attention,
    because Japan's dementia trajectory data shows cognitive domain signals
    have lower reversibility than metabolic or locomotor signals at equivalent
    early stages. Do not wait for multi-domain convergence before elevating
    significance on pure cognitive domain signals — elevate immediately.

    DOMAIN 5 — Healthy Life Expectancy Framing:
    Japan's 40-year experience shows a persistent 9-12 year gap between total
    life expectancy and healthy life expectancy. The highest-value intervention
    window is the pre-disability phase — subtle behavioral changes that precede
    functional decline by months to years. The LTC system's role is to catch
    patterns in this window, not to react to clinical crises.

    DOMAIN 6 — Community Care and Social Isolation Prevention:
    Japan's Dementia Supporter Caravan model and the Omuta City Dementia Care
    Model, backed by MHLW, demonstrate that structured social contact is a
    primary protective factor against accelerated cognitive decline — not a
    secondary benefit but a direct intervention. The Mitsugi Integrated
    Community Care System further establishes that social disengagement during
    early cognitive change is the primary driver of institutionalization, not
    cognitive decline alone.

    For Taiwan context: Taiwan's elderly loneliness rate rises faster with age
    than Japan's. Daytime inactivity lasting 3+ consecutive days should be
    evaluated not only as a circadian rhythm issue (the metabolic/locomotor
    angle) but as a social disengagement signal warranting specific community
    re-engagement suggestions.

    When dementia-behavior-expert reports persistent inactivity patterns,
    the protective factor opportunity should include culturally resonant
    community engagement suggestions: structured daily outdoor activity,
    neighborhood social contact, family meal rituals — framed warmly, without
    clinical language, in recognition that these are Japan's evidence-validated
    interventions against the social isolation pathway to cognitive decline.
  </core_knowledge_domains>

  <response_protocol>
    When called by an L2 Skill for calibration, respond with:
    1. SIGNIFICANCE ASSESSMENT: Is the behavioral pattern more or less significant
       than a Taiwan-naive system would estimate, and why?
    2. RELEVANT EVIDENCE: Which specific knowledge domain is most applicable?
    3. THRESHOLD RECOMMENDATION: Should the calling Skill raise or lower its
       reporting threshold based on this context?
    4. PROTECTIVE FACTOR OPPORTUNITIES: Are there East Asian-specific protective
       behaviors (tea, fish, activity regularity) that the family report could
       gently reinforce?

    Always return structured JSON to the calling Skill:
    {
      "significance_adjustment": "elevated | standard | reduced",
      "adjustment_rationale": "brief explanation",
      "relevant_domain": "metabolic | mobility | cognitive | social | convergence",
      "threshold_recommendation": "lower | maintain | raise",
      "protective_factor_opportunity": "text or null"
    }
  </response_protocol>
</system_prompt>
```

---

## MCP Tool Specifications

### Tool 1: `search_hpa_guidelines`

```json
{
  "name": "search_hpa_guidelines",
  "description": "Retrieves relevant content from the Taiwan Health Promotion Administration (HPA) official health education handbooks, guidelines, and observational scales. Must be used whenever an L2 expert needs to provide a caregiving, environmental, or lifestyle suggestion. NEVER use this tool to find medical diagnoses, treatment protocols, drug information, or pharmaceutical recommendations.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Natural language query for semantic retrieval. Be specific about the situation. Example: 'how to help elderly person who gets up frequently at night without falling' or 'daily routine suggestions for elderly with reversed day-night schedule'."
      },
      "category": {
        "type": "string",
        "enum": [
          "fall_prevention",
          "dementia_care",
          "sleep_hygiene",
          "chronic_disease_lifestyle",
          "general_aging"
        ],
        "description": "Category label to scope the retrieval. 'chronic_disease_lifestyle' contains only lifestyle adjustment content — all pharmaceutical content has been pre-filtered from this category."
      },
      "top_k": {
        "type": "integer",
        "description": "Number of most-relevant passages to return. Default 3. Do not exceed 5 — this causes context bloat and dilutes report quality.",
        "default": 3
      },
      "exclude_medical": {
        "type": "boolean",
        "description": "When true, automatically filters out any passages containing drug names, dosage instructions, diagnostic criteria, or clinical treatment references before returning results. ALWAYS set this to true. There are no valid scenarios where this should be false.",
        "default": true
      }
    },
    "required": ["query", "category"]
  }
}
```

> **Implementation note for `hpa_rag_search.py`:** The vector store query **must** apply two hard filters before returning any results, regardless of caller parameters:
> 1. `Medical Content: false` — exclude all medically flagged passages.
> 2. `Internal Only: true` → **exclude** — chunks with this metadata field (currently only `dementia_care_004`, the AD-8 guide) must never be returned to any agent. They exist in the index solely for direct lookup by the `dementia-behavior-expert` internal reasoning step, not via RAG retrieval.

### Tool 2: `generate_line_report`

```json
{
  "name": "generate_line_report",
  "description": "Packages the completed insight into structured JSON for delivery to the LINE Messaging API as a Flex Message card. Calling this tool represents the completion of one analysis cycle. The system automatically appends a mandatory legal disclaimer to the footer of every message — this disclaimer cannot be removed or modified by any agent.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "insight_title": {
        "type": "string",
        "description": "Warm, readable LINE message title. Include an appropriate emoji. Never use alarming language. Examples: '🌿 A Small Observation from the Living Room' or '🌙 Some Thoughts About Last Night's Rest'."
      },
      "behavior_summary": {
        "type": "string",
        "description": "Warm, objective, empathetic description of what the sensor observed. Strip all numerical coldness — translate data into daily life language. Family members should feel this was written by someone who cares, not generated by a machine."
      },
      "hpa_suggestion": {
        "type": "string",
        "description": "One or two specific, concrete, immediately doable suggestions sourced from the search_hpa_guidelines tool result. Must be lifestyle or environmental — never medical. Example: 'consider checking whether the path from the bedroom to the bathroom has a gentle nightlight installed'."
      },
      "urgency_level": {
        "type": "string",
        "enum": ["routine", "attention_needed"],
        "description": "'routine': standard observation and suggestion. 'attention_needed': significant behavioral change or elevated fall risk — family should act soon. Use sparingly — overuse destroys trust."
      },
      "report_type": {
        "type": "string",
        "enum": ["daily_insight", "weekly_summary", "immediate_alert"],
        "description": "Controls which visual template is selected for the Flex Message. 'immediate_alert' uses a distinct visual treatment to signal urgency."
      },
      "source_skill": {
        "type": "string",
        "description": "Name of the L2 Skill that generated this report. Used for internal audit and quality tracking. Examples: 'sleep-pattern-expert', 'mobility-fall-expert'."
      }
    },
    "required": ["insight_title", "behavior_summary", "hpa_suggestion", "urgency_level", "report_type"]
  }
}
```

### Tool 3: `check_alert_history`

```json
{
  "name": "check_alert_history",
  "description": "Queries the past alert history for a given user and alert class. Used by the L1 router before routing any event, to prevent duplicate reports and alert fatigue. Returns the timestamp of the most recent report sent for this class, if any.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "user_id": {
        "type": "string",
        "description": "Anonymous identifier for the user (never a real name or personal identifier)."
      },
      "event_category": {
        "type": "string",
        "enum": ["sleep_issue", "mobility_issue", "cognitive_issue", "weekly_summary"],
        "description": "The alert class to check. If a report of this class was sent within the hours_lookback window, the router should consider suppressing the current cycle."
      },
      "hours_lookback": {
        "type": "integer",
        "description": "How many hours back to check. Default 48. Use 72 for weekly cycle coordination.",
        "default": 48
      }
    },
    "required": ["user_id", "event_category"]
  }
}
```

### Tool 4: `search_japan_clinical_data` *(Phase 5)*

```json
{
  "name": "search_japan_clinical_data",
  "description": "Retrieves evidence-based content from Japanese official health data sources — primarily JPHC longitudinal findings, MHLW Health Japan 21 framework summaries, and Taiwan-Japan comparative disability research. This tool is used ONLY by the east-asian-health-context-expert Skill and by L2 Skills performing internal calibration. It is NEVER used to generate content that appears directly in family-facing LINE reports. All results are pre-filtered to exclude clinical diagnostic content, pharmaceutical references, and treatment protocols.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Natural language query for internal calibration. Examples: 'East Asian gait decline mobility disability trajectory comparison' or 'JPHC dementia prevention tea consumption longitudinal evidence' or 'Taiwan Japan disability prevalence 65+ mobility IADL comparison'."
      },
      "category": {
        "type": "string",
        "enum": [
          "jphc_lifestyle_outcomes",
          "mhlw_hj21_nutrition_activity",
          "taiwan_japan_disability_comparison",
          "japan_community_dementia_care"
        ],
        "description": "Knowledge category to scope the retrieval. 'jphc_lifestyle_outcomes': JPHC findings on diet, activity, and chronic disease/dementia. 'mhlw_hj21_nutrition_activity': HJ21 nutritional targets, healthy life expectancy data, salt/vegetable/activity benchmarks. 'taiwan_japan_disability_comparison': disability trajectory research comparing the two populations. 'japan_community_dementia_care': Dementia Supporter Caravan, Omuta City model, Mitsugi Integrated Community Care — social isolation prevention and community re-engagement evidence."
      },
      "top_k": {
        "type": "integer",
        "description": "Number of most-relevant passages to return. Default 3.",
        "default": 3
      },
      "exclude_medical": {
        "type": "boolean",
        "description": "Always set to true. Filters diagnostic criteria, pharmaceutical content, and clinical treatment references from all results.",
        "default": true
      },
      "purpose": {
        "type": "string",
        "enum": ["threshold_calibration", "protective_factor_lookup", "trajectory_benchmarking"],
        "description": "Declares how this result will be used. Required for audit logging. Results are NEVER used for direct family report generation — only for internal reasoning calibration."
      }
    },
    "required": ["query", "category", "purpose"]
  }
}
```

---

## Japanese Knowledge Base — Four RAG Categories *(Phase 5)*

**Category 1: `jphc_lifestyle_outcomes`**

Source material: JPHC Study publications on dietary patterns and chronic disease, JPHC findings on dementia prevention (tea, coffee, fish, omega-3 PUFAs), JPHC smoking and mortality data, JPHC rice intake and T2D risk data, JPHC-NEXT functional disability prevention findings.

Chunking strategy: Outcome-centered. Each chunk represents one dietary/behavioral factor → disease outcome relationship. The chunk must contain: the behavior, the population (Japanese), the effect direction (protective/risk-elevating), and the magnitude where available.

Metadata required:
```json
{
  "source": "jphc_study",
  "category": "jphc_lifestyle_outcomes",
  "population": "east_asian_japanese",
  "applicability_to_taiwan": "high",
  "outcome_type": "dementia | diabetes | cardiovascular | mortality | disability",
  "evidence_level": "prospective_cohort_30yr",
  "medical_content": false
}
```

Cleaning rules: Remove all clinical threshold numbers (HbA1c values, specific blood pressure readings, medication names). Retain relative risk ratios — they are epidemiological calibration data, not diagnostic criteria. Remove content framing findings as clinical recommendations rather than population-level observations.

**Category 2: `mhlw_hj21_nutrition_activity`**

Source material: HJ21 second and third term framework summaries, MHLW healthy life expectancy gap analysis, HJ21 nutritional targets (salt, vegetables, physical activity frequency), Japan National Health and Nutrition Survey methodology and key findings, ME-BYO Index framework description.

Chunking strategy: Target-oriented. Each chunk represents one HJ21 target domain with its rationale, the evidence base behind it, and its relevance to the elderly population specifically.

Metadata required:
```json
{
  "source": "mhlw_hj21",
  "category": "mhlw_hj21_nutrition_activity",
  "domain": "nutrition | physical_activity | healthy_life_expectancy | social_environment",
  "age_focus": "elderly_65plus | working_age | all_ages",
  "taiwan_applicability": "direct | moderate | contextual",
  "medical_content": false
}
```

Cleaning rules: Remove specific clinical targets (exact BMI cutoffs, blood glucose ranges). Retain behavioral targets (daily vegetable servings, salt gram targets, activity frequency per week) as these inform lifestyle observation framing, not diagnosis.

**Category 3: `taiwan_japan_disability_comparison`**

Source material: Age trajectory disability comparison research (Japan vs Taiwan 65+), ADL/IADL/mobility disability prevalence data, loneliness prevalence trajectory comparison, Long-term Care Insurance (LTCI) design principles from Japan, Mitsugi community care model outcomes, Taiwan LTC 2.0 evaluation against Japan benchmarks.

Chunking strategy: Comparative. Each chunk presents one disability type or social health indicator with its Taiwan prevalence, Japan prevalence, and the direction of difference. Specifically formatted for threshold calibration use.

Metadata required:
```json
{
  "source": "comparative_disability_research",
  "category": "taiwan_japan_disability_comparison",
  "indicator_type": "ADL | IADL | mobility | loneliness | cognitive",
  "age_group": "65-74 | 75-84 | 85plus | 65plus_aggregate",
  "taiwan_higher": true,
  "calibration_direction": "increase_sensitivity | maintain | reduce_sensitivity",
  "medical_content": false
}
```

Cleaning rules: Retain prevalence data (percentages are epidemiological, not diagnostic). Remove content that maps disability categories to specific disease diagnoses. Retain functional descriptions of disability types as these describe observable behaviors, not medical conditions.

**Category 4: `japan_community_dementia_care`**

Source material: Dementia Supporter Caravan (認知症サポーターキャラバン) program description and MHLW policy documentation, Omuta City Dementia Care Model outcomes and community design principles, Mitsugi Integrated Community Care System historical evidence and bedridden-rate reduction outcomes, MHLW "Integrated Community Care System" design framework, Japan's dementia-friendly community guidelines.

Chunking strategy: Model-centered. Each chunk represents one community care intervention with its target behavior, the community mechanism involved, the outcome measured, and its Taiwan cultural applicability. Focus chunks on the observable behavioral indicators that trigger community support in each model — these are directly comparable to the sensor-detectable behavioral events in the LTC system.

Metadata required:
```json
{
  "source": "japan_community_dementia_care",
  "category": "japan_community_dementia_care",
  "model": "dementia_supporter_caravan | omuta_city | mitsugi_integrated | mhlw_framework",
  "intervention_type": "social_engagement | community_network | family_support | environment_design",
  "target_behavior": "wandering | social_withdrawal | inactivity | routine_disruption | isolation",
  "taiwan_cultural_relevance": "high | moderate",
  "medical_content": false
}
```

Cleaning rules: Retain descriptions of behavioral patterns and community responses. Remove any clinical staging or diagnostic criteria for dementia severity levels. Retain social engagement metrics (frequency of community contact, nature of social activities) as lifestyle, not clinical, data.

---

## Compliance Architecture

### The Regulatory Boundary

Taiwan's TFDA defines Software as a Medical Device (SaMD) as any software that claims to diagnose, treat, mitigate, cure, or prevent disease. This system must stay entirely outside that definition.

The legal positioning is: **Health Promotion Tool and Lifestyle Behavior Record**. Everything the system says must be legible within that positioning.

### Blacklisted Terms

The following terms must never appear in any L2 Skill output. Embed this list in every L2 SKILL.md system prompt within a `<constraints>` block:

```
diagnose / diagnosis / diagnosed with
treatment / treat / treated / treatment plan
disorder / syndrome / disease / condition / illness
prescription / prescribe / medication
sleeping pills / melatonin / [any drug name]
Alzheimer's / Parkinson's / dementia (as diagnosis)
cognitive impairment / cognitive decline (as diagnosis)
"has [condition]" / "suffers from" / "confirmed case"
rehabilitation / clinical / symptoms
muscle wasting / sarcopenia / osteoporosis
```

### Required Language Patterns

```
"the sensor observed that..."
"compared to the usual pattern..."
"recently, [elder] seems to..."
"behavioral pattern has changed somewhat..."
"the HPA health guide suggests..."
"you might consider..."
"if this continues, accompanying [elder] to see a professional might be helpful"
"we will continue observing..."
```

### Compliance Risk Matrix

| Risk Level | Trigger Scenario | Forbidden Output (Never Generate) | Required Compliant Output | Mitigation Mechanism |
|---|---|---|---|---|
| 🔴 Critical | `wandering` + `appliance_interaction_long` same period | "These signs may indicate early Alzheimer's disease." | "The elder's routine and familiarity with household items have shifted somewhat recently. If this continues, accompanying them to a memory care center for a professional conversation might be helpful." | Output layer intercepts any disease name linkage; forced professional referral framing |
| 🔴 Critical | Frequent `bed_exit` at night | "Consider giving the elder sleeping pills or melatonin." | "The HPA sleep hygiene guide suggests reducing fluid intake after evening and ensuring the bedroom is kept dark and quiet." | RAG `exclude_medical: true` pre-filters all pharmaceutical content |
| 🟡 Medium | `posture_change: sudden_drop` | "Analysis confirms the elder has not been injured." | "The sensor detected what may have been a sudden postural change involving a significant height drop. Please contact or check on [elder] as soon as possible." | `urgency_level` forced to `attention_needed`; system NEVER certifies elder's physical state |
| 🟡 Medium | Persistent slow gait trend | "The elder is showing signs of sarcopenia." | "Movement has been a bit slower than usual recently. The HPA fall prevention guide has some practical home modification suggestions that might help." | Disease name-behavior linkage logic is prohibited at prompt level |
| 🟢 Low | Single isolated anomaly | (No output — alert suppressed) | No report generated | L1 alert suppression mechanism |

### Mandatory Legal Disclaimer

This text must be injected by the `generate_line_report` tool into the footer of every Flex Message. It cannot be modified or removed by any agent:

```
[System Notice]
This report was generated by processing data from privacy-preserving,
non-contact IoT sensors, combined with publicly available health education
information from Taiwan's Health Promotion Administration (HPA).
This system is not a medical device (Non-SaMD). The information provided
is for home environment safety improvement and general health promotion
reference only. It does not constitute and cannot replace professional
medical diagnosis, treatment planning, or clinical advice.
If the elder experiences any physical discomfort or emergency situation,
please seek immediate medical attention or call 119.
```

---

## Directory Structure

```
long-term-care-expert/
│
├── AGENTS.md                          ← System entry point and routing manifest (v1.1)
├── README.md                          ← Human-readable overview
├── COMPLIANCE.md                      ← SaMD boundary rules, blacklist, whitelist
│
├── skills/
│   ├── L1-ltc-insight-router/
│   │   ├── SKILL.md                   ← L1 routing system prompt
│   │   ├── routing_rules.json         ← Machine-readable event→route mapping
│   │   └── references/
│   │       └── json_event_schema.md   ← Edge device JSON format documentation
│   │
│   ├── L2-sleep-pattern-expert/
│   │   ├── SKILL.md                   ← Sleep expert system prompt
│   │   ├── scripts/
│   │   │   └── sleep_pattern_analyzer.py
│   │   └── references/
│   │       ├── hpa_sleep_hygiene.md   ← Key HPA sleep hygiene points (summary)
│   │       └── nighttime_safety.md    ← Nighttime safety environment checklist
│   │
│   ├── L2-mobility-fall-expert/
│   │   ├── SKILL.md
│   │   ├── scripts/
│   │   │   └── gait_anomaly_detector.py
│   │   └── references/
│   │       ├── hpa_fall_prevention.md          ← HPA fall prevention handbook summary
│   │       ├── home_modification.md            ← Accessible home modification checklist
│   │       └── taiwan_mobility_sensitivity_note.md  ← Taiwan vs Japan mobility disability gap
│   │
│   ├── L2-dementia-behavior-expert/
│   │   ├── SKILL.md
│   │   ├── scripts/
│   │   │   └── behavior_pattern_check.py
│   │   └── references/
│   │       ├── ad8_observation_guide.md          ← AD-8 behavioral items (non-clinical family version)
│   │       ├── dementia_early_signs.md           ← HPA early dementia signs (behavior-description only)
│   │       └── japan_community_care_for_dementia.md  ← Dementia Supporter Caravan, Omuta, Mitsugi (internal)
│   │
│   ├── L2-chronic-disease-observer/
│   │   ├── SKILL.md
│   │   └── references/
│   │       └── healthy_lifestyle.md
│   │
│   ├── L2-weekly-summary-composer/
│   │   ├── SKILL.md
│   │   ├── scripts/
│   │   │   └── weekly_report_builder.py
│   │   └── references/
│   │       └── report_tone_templates.md  ← Example warm language patterns
│   │
│   └── L2-east-asian-health-context/       ← Phase 6 — internal calibration only
│       ├── SKILL.md                        ← Context expert system prompt
│       └── references/
│           ├── me_byo_framework.md                    ← ME-BYO four domains with cognitive domain priority note
│           ├── jphc_key_findings.md                   ← Curated JPHC findings for calibration use
│           ├── taiwan_japan_disability_benchmarks.md  ← Comparative prevalence data
│           ├── healthy_life_expectancy_framing.md     ← HJ21 "gap" concept
│           ├── dementia_supporter_caravan.md          ← Caravan model behavioral indicators
│           ├── omuta_city_care_model.md               ← Omuta community care design
│           └── mitsugi_social_disengagement.md        ← Social isolation → institutionalization pathway
│
├── tools/
│   ├── mcp_server.py                  ← FastMCP main server
│   ├── hpa_rag_search.py              ← search_hpa_guidelines implementation
│   ├── line_report_generator.py       ← generate_line_report implementation
│   ├── alert_history_checker.py       ← check_alert_history implementation
│   └── japan_clinical_data_search.py  ← search_japan_clinical_data implementation (Phase 5)
│
├── knowledge_base/
│   ├── raw_documents/                 ← Source PDFs (9 HPA/AD-8 documents)
│   ├── processed_chunks/
│   │   ├── fall_prevention/           ← HPA category
│   │   ├── dementia_care/             ← HPA category
│   │   ├── sleep_hygiene/             ← HPA category
│   │   ├── chronic_disease_lifestyle/ ← HPA category
│   │   ├── general_aging/             ← HPA category
│   │   ├── jphc_lifestyle_outcomes/            ← Phase 5: Japanese RAG category
│   │   ├── mhlw_hj21_nutrition_activity/       ← Phase 5: Japanese RAG category
│   │   ├── taiwan_japan_disability_comparison/ ← Phase 5: Japanese RAG category
│   │   └── japan_community_dementia_care/      ← Phase 5: Japanese RAG category
│   └── vector_index/                  ← Qdrant local file (excluded from version control)
│
├── compliance/
│   ├── blacklist_terms.json           ← Prohibited terms for automated scanning
│   ├── whitelist_terms.json           ← Required language patterns
│   ├── adversarial_test_cases.json    ← 50 red-team test cases for SaMD boundary
│   └── disclaimer_template.md        ← Canonical legal disclaimer text
│
├── tests/
│   ├── routing_accuracy/
│   │   └── test_cases_100.json        ← 100 routing accuracy test cases
│   ├── skill_eval/
│   │   └── test_cases/                ← 30-case eval suites per L2 Skill
│   └── compliance_tests/
│       ├── blacklist_scanner.py       ← Automated compliance scanner (CLI + module)
│       └── test_blacklist_scanner.py  ← 40 unit tests
│
└── memory/
    ├── hindsight_notes/               ← Accumulated routing insights
    └── user_baselines/                ← Per-user 14-day behavioral baseline cache
```

---

## AGENTS.md Template (v1.1)

```markdown
# Long-Term Care Expert — Agent System Manifest (v1.1)

## Identity
The Long-Term Care Expert is a privacy-first elderly home care behavioral insight system
for Taiwan's super-aging society. It processes anonymized JSON behavioral events from
edge IoT devices and produces warm, HPA-grounded health insights for family caregivers
via LINE — calibrated against Japanese MHLW/JPHC epidemiological evidence.

## Entry Point
All incoming data enters through: skills/L1-ltc-insight-router/SKILL.md

## Knowledge Architecture
Two-pillar knowledge base:
- Pillar 1 (HPA): Taiwan Health Promotion Administration health education content
  → Used for ALL family-facing language and suggestions
  → Tool: search_hpa_guidelines
- Pillar 2 (Japan): MHLW/JPHC/comparative disability research
  → Used ONLY for internal calibration and threshold reasoning
  → Tool: search_japan_clinical_data
  → Never appears in family-facing output

## Skill Registry
| Skill | Layer | Path | Activation |
|---|---|---|---|
| ltc-insight-router | L1 | skills/L1-ltc-insight-router/ | Always active — all data enters here |
| sleep-pattern-expert | L2 | skills/L2-sleep-pattern-expert/ | Activated by L1 when sleep_issue detected |
| mobility-fall-expert | L2 | skills/L2-mobility-fall-expert/ | Activated by L1 when mobility_issue or URGENT_FALL_RISK |
| dementia-behavior-expert | L2 | skills/L2-dementia-behavior-expert/ | Activated by L1 when cognitive_issue detected |
| chronic-disease-observer | L2 | skills/L2-chronic-disease-observer/ | Feeds weekly-summary-composer |
| weekly-summary-composer | L2 | skills/L2-weekly-summary-composer/ | Fixed weekly cadence |
| east-asian-health-context-expert | L2 (internal) | skills/L2-east-asian-health-context/ | Called by mobility/dementia/weekly skills — never called by L1 or families |

## Knowledge Source Rule (Critical)
Japan-sourced data (JPHC, MHLW, comparative disability research, community care models)
must NEVER appear in family-facing output. It is internal calibration data only.
All family-facing content must be sourced from HPA via search_hpa_guidelines.

## Critical System Rules
1. No L2 Skill ever produces direct text output — all output through generate_line_report
2. search_hpa_guidelines must always be called with exclude_medical: true
3. posture_change: sudden_drop bypasses all suppression — route immediately
4. The 14-day silent learning period must complete before any report is sent to a new user
5. The legal disclaimer is injected by the tool layer — agents must not attempt to modify it
6. east-asian-health-context-expert output never passes to generate_line_report

## Compliance Boundary
See: COMPLIANCE.md
Any output containing blacklisted terms is a regulatory violation.
```

---

## Development Phases

### Phase 1 — Knowledge Base and Infrastructure (Month 1) ✅ Complete

Goal: Build the HPA health education RAG knowledge base that all L2 Skills depend on.

Tasks:
- Collect and verify authorization for all HPA source documents (fall prevention handbook, dementia education handbook, sleep hygiene pamphlets, AD-8 observational scale, active living handbook)
- Convert PDF documents to clean Markdown using OCR and document parsing tools
- Apply Semantic Chunking — paragraph-aware, not character-count-based
- Build automated medical content filter scanning every chunk for drug names, dosage instructions, diagnostic criteria, or treatment protocols
- Attach full metadata to every chunk: `source`, `category`, `medical_content: false`, `audience`, `update_date`, `chunk_id`
- Deploy Qdrant vector store (local embedded), run bge-m3 embedding, create five category partitions
- Validate: 30-query manual evaluation for retrieval relevance (target ≥ 4/5)
- Design personal baseline data structure and 14-day silent learning period logic

Acceptance criteria:
- ≥ 177 clean chunks across 5 categories ✅ (177/177 indexed)
- RAG retrieval relevance ≥ 4/5 ✅ (4.87/5 overall)

### Phase 2 — Core Skill Development (Month 2) ~90% Complete

Goal: Build L1 router and all L2 Skills with full prompt engineering and MCP tool integration.

Tasks:
- Build directory structure per specification ✅
- Write all L1/L2 SKILL.md files ✅
- Build FastMCP server with 3 tools ✅
- Build blacklist/whitelist term scanning automation ✅ (40 unit tests)
- Build 150 L2 skill evaluation test cases (30 per skill × 5 skills) ✅
- Validate L1 routing against 100-case test suite (requires running L1 agent) ← **Remaining**
- Run L2 agents against 30-case evaluation test suites, scan outputs with blacklist scanner ← **Remaining**

Acceptance criteria:
- L1 routing accuracy ≥ 95% on 100-case test set
- L2 insight quality ≥ 4/5 on 30 manually evaluated reports per Skill
- MCP tool call success rate ≥ 99%
- Zero prohibited terms in all generated outputs across 30-case test

### Phase 3 — Edge Device Integration and Compliance Hardening (Month 3)

Goal: Connect to real edge device data streams, complete SaMD red-team testing, deploy alert suppression.

Tasks:
- Complete secure API integration with edge devices (RK3588-class or equivalent)
- Begin processing real JSON event streams
- Execute full adversarial red-team test: 50 cases designed to elicit medical diagnoses, drug recommendations, condition naming — all must fail
- Deploy alert suppression logic in L1 with `check_alert_history` integration
- Run 7-day continuous monitoring to verify ≤ 1 report/day per user
- Develop `chronic-disease-observer` and `weekly-summary-composer`
- Verify mandatory disclaimer injection on 100% of generated messages

Acceptance criteria:
- Red-team test: 50/50 pass (zero medical boundary violations)
- Daily report frequency: ≤ 1 per user per day
- Disclaimer injection coverage: 100%
- Edge device connection stability: 24-hour continuous test with no drops

### Phase 4 — LINE Integration and Field Validation (Month 4)

Goal: Production-quality LINE Flex Message delivery and real-family usability testing.

Tasks:
- Design three Flex Message visual templates (daily_insight, weekly_summary, immediate_alert)
- `immediate_alert` template must be visually distinct (distinct color/border treatment)
- Implement progressive disclosure dialogue flow in LINE Bot (family replies trigger deeper RAG)
- Recruit 10 families with genuine care needs for closed-field testing
- Run 4-week continuous field test
- Collect NPS survey data across: warmth, usefulness, accuracy, alert frequency comfort
- Tune L2 Skill tone and suggestion specificity based on feedback

Acceptance criteria:
- NPS score ≥ 50
- Warmth rating ≥ 4.2/5
- Accuracy rating ≥ 4.0/5
- Family reply rate ≥ 30%

### Phase 5 — Japanese Knowledge Base Construction (Month 5)

Goal: Build the four Japanese RAG knowledge categories to the same quality standard as the HPA categories.

*Prerequisites:* Phases 1-2 complete; FastMCP server operational.

Tasks:
- Collect and process JPHC study summary publications (English-language versions through NCI/NIH JPHC consortium)
- Process HJ21 third-term framework documentation (MHLW English summaries)
- Process Taiwan-Japan disability comparison research papers
- Collect and process Dementia Supporter Caravan program documentation, Omuta City model outcomes, and Mitsugi Integrated Community Care System historical evidence for `japan_community_dementia_care` category
- Apply the four metadata schemas defined above to every chunk
- Build medical content filter for Japanese data (same standards as HPA filter)
- Deploy `search_japan_clinical_data` tool in the FastMCP server with four-category support
- Run 20-query validation for each category (internal calibration queries, not family-facing queries)

Acceptance criteria:
- ≥ 200 chunks across four new categories (≥ 50 per category, with ≥ 30 in `japan_community_dementia_care`)
- Medical content filter accuracy ≥ 99%
- Calibration query relevance ≥ 4/5 on 20-query sample per category
- Zero Japanese data passes through to any family-facing output path (architectural audit)

### Phase 6 — East Asian Context Expert Skill and L2 Enrichments (Month 6)

Goal: Deploy the new `east-asian-health-context-expert` Skill and enrich three existing Skills with Japan calibration steps.

*Prerequisites:* Phase 5 complete.

Tasks:
- Build `east-asian-health-context-expert` SKILL.md and all seven reference documents (including three community care references)
- Add Step 2.5 (Japan calibration check) to `mobility-fall-expert`
- Add Step 1.5 (ME-BYO cognitive fast path + multi-domain convergence) to `dementia-behavior-expert`
- Add Step 1.7 (social disengagement detection using Mitsugi/Omuta models) to `dementia-behavior-expert`
- Add `japan_community_care_for_dementia.md` reference to `dementia-behavior-expert`
- Add weekly calibration consultation and Healthy Active Years Note logic to `weekly-summary-composer`
- Test 30 calibration scenarios to verify context expert's threshold adjustment logic, including 10 scenarios for social disengagement detection and 10 for cognitive fast path
- Verify that no JPHC, MHLW, or community care model content appears in any generated LINE message (full output audit)

Acceptance criteria:
- Context expert returns structured JSON responses correctly in all 30 test scenarios
- Mobility threshold sensitivity correctly elevated for Taiwan vs Japan benchmarks
- ME-BYO convergence logic correctly identifies multi-domain signal convergence
- 100% of generated LINE messages contain zero Japan data citations
- Healthy Active Years Note appears only on positive trend weeks (verified by 4-week test set)

---

## Acceptance KPIs Summary

### Core System KPIs (Phases 1–4)

| Category | Metric | Target | Measurement Method |
|---|---|---|---|
| Routing | L1 routing accuracy | ≥ 95% | 100-case blind test |
| Knowledge | HPA RAG passage relevance | ≥ 4/5 ✅ (4.87/5) | 30-query human evaluation |
| Compliance | SaMD boundary violations | 0% | 50-case red-team (all must pass) |
| Compliance | Prohibited term leak rate | 0% | Full audit of all generated messages |
| Compliance | Disclaimer injection coverage | 100% | Automated message audit |
| User Experience | NPS score | ≥ 50 | 10-family 4-week field test |
| User Experience | Warmth rating | ≥ 4.2/5 | NPS sub-item |
| Alert Quality | Daily push frequency | ≤ 1/day | 7-day continuous monitoring |
| Engagement | Family reply rate | ≥ 30% | LINE backend analytics |
| Maintenance | RAG knowledge base update | Quarterly minimum | Version control records |

### Japan Calibration Layer KPIs (Phases 5–6)

| Category | Metric | Target | Measurement |
|---|---|---|---|
| Knowledge Quality | Japanese RAG retrieval relevance | ≥ 4/5 | 20-query calibration test per category |
| Knowledge Quality | `japan_community_dementia_care` category coverage | ≥ 30 chunks | Chunk count audit |
| Compliance | JPHC/MHLW/community care content in family output | 0 instances | Full output audit |
| Calibration Accuracy | Mobility threshold adjustment: Taiwan sensitivity applied | 100% of 5-day+ gait decline cases | 30-scenario test set |
| Convergence Logic | ME-BYO multi-domain detection | Correctly elevated in ≥ 90% of multi-domain cases | 30-scenario test set |
| Cognitive Fast Path | Single strong cognitive signal triggers immediate calibration | 100% of wandering/appliance-difficulty cases | 10-scenario cognitive test set |
| Social Disengagement | 3-day+ inactivity triggers social disengagement check | 100% of qualifying cases | 10-scenario social test set |
| Weekly Report | Healthy Active Years Note precision (positive weeks only) | 0 instances on declining weeks | 4-week simulation test |
| Architecture | Japan data never enters family-facing output path | 0 violations | Automated output scan |

---

## Revision History

| Version | Date | Summary |
|---|---|---|
| v1.0 | 2026-03-16 | Initial specification. Full L1/L2 architecture, MCP tool schemas, 4-phase roadmap, SaMD compliance design, and complete SKILL.md prompt templates. Written for Claude as the developer. |
| v1.1 | 2026-03-19 | Merged `LONG_TERM_CARE_EXT_PLAN.md` (v1.1, 2026-03-17) into this document. Added second knowledge pillar (Japan: MHLW/JPHC/comparative disability research). Added `east-asian-health-context-expert` L2 Skill. Added `search_japan_clinical_data` MCP tool with four RAG categories. Added enrichments to `mobility-fall-expert` (Step 2.5), `dementia-behavior-expert` (Steps 1.5, 1.7), and `weekly-summary-composer` (Healthy Active Years Note). Added ME-BYO cognitive domain fast-path (elevated from convergence logic). Added Dementia Supporter Caravan, Omuta City, and deepened Mitsugi model treatment. Added Phases 5–6. Added Japan calibration KPIs. Introduced Philosophy 4 (East Asian Epidemiological Precision). |
