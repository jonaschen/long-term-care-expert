# LONGTERM_CARE_EXPERT_DEV_PLAN.md

**Document Version:** v1.0  
**Audience:** Claude (AI Developer)  
**Purpose:** Complete specification for building the `long-term-care-expert` Claude Agent Skill Set  
**Domain:** Taiwan elderly home care, IoT privacy sensing, HPA health education, LINE messaging

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

### The Three Design Philosophies That Must Never Be Violated

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

---

## Architecture Overview

### Skill Set Name
`long-term-care-expert`

### What This Skill Set Is

A hierarchical two-layer Agent system:

- **Layer 1** (`ltc-insight-router`): Pattern recognition and dynamic routing. No health knowledge. No direct family-facing output. Only data aggregation, trend detection, alert suppression, and routing.

- **Layer 2** (five domain expert Skills): Each expert holds deep knowledge of one behavioral domain, has permission to call specific RAG knowledge categories, and produces structured LINE report output through MCP tool calls.

### Complete Skill Inventory

| Skill ID | Layer | Role |
|---|---|---|
| `ltc-insight-router` | L1 | Main router — pattern classification, alert suppression, dynamic routing |
| `sleep-pattern-expert` | L2 | Nighttime behavior — bed exits, sleep disruption, nocturia, sleep environment |
| `mobility-fall-expert` | L2 | Movement — gait slowdown, fall risk, rising difficulty, home modification |
| `dementia-behavior-expert` | L2 | Cognitive behavior — wandering, inversion of day/night, appliance difficulty, AD-8 guidance |
| `chronic-disease-observer` | L2 | Long-term activity trend monitoring, lifestyle regularity |
| `weekly-summary-composer` | L2 | Cross-domain weekly report integration |

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
      ├── mobility-fall-expert          (parallel routing if multiple domains triggered)
      └── dementia-behavior-expert
            │
            ▼
      Calls: search_hpa_guidelines (RAG, exclude_medical=true)
            │
            ▼
      Synthesizes: cold JSON data + warm HPA health education text
            │
            ▼
      Calls: generate_line_report (structured output)
            │
            ▼
      LINE Official Account → Family caregiver receives Flex Message
```

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
    <rule id="output_channel">
      All output through generate_line_report only.
    </rule>
  </constraints>

  <available_tools>
    - search_hpa_guidelines
    - generate_line_report
  </available_tools>

  <reasoning_protocol>
    Step 1 — analyze_data:
      Describe the observed behavior in purely behavioral, non-clinical terms.
      Example: wandering at 2am → "the elder's activity schedule has shifted,
      with nighttime activity becoming more prominent."

    Step 2 — tool_call_search:
      Call search_hpa_guidelines, category: "dementia_care", exclude_medical: true.
      Focus queries on daily routine rebuilding, caregiver observation guidance,
      and environmental support strategies.

    Step 3 — synthesize_insight:
      Build a warm, observation-only narrative. Suggest one concrete daily
      routine adjustment (e.g., morning sunlight walk). If applicable, gently
      invite the family to notice a specific everyday behavior in coming days.
      If changes are persistent across multiple reports, include a soft
      referral suggestion toward professional consultation.

    Step 4 — tool_call_output:
      Call generate_line_report.
      urgency_level is usually "routine" — use "attention_needed" only if
      the behavioral change has escalated significantly over multiple days.
  </reasoning_protocol>
</system_prompt>
```

---

### L2-4: `chronic-disease-observer`

**Knowledge Source:** HPA chronic disease lifestyle sections (lifestyle adjustment content only — all pharmaceutical and treatment content strictly excluded)

**Triggered when:** Weekly activity volume trend decreases ≥ 20%, meal/activity schedule regularity significantly disrupted

**Scope Boundary:** This Skill observes **lifestyle regularity patterns only**. It does not observe, comment on, or make any inference about any named chronic condition. It feeds data to `weekly-summary-composer`. It does not produce standalone daily reports.

**Example translation:**
- "Activity levels have been consistently lower this week compared to last week's baseline — about 25% fewer movement events recorded during daytime hours."
- HPA suggestion: general physical activity encouragement for older adults from the Active Living handbook

---

### L2-5: `weekly-summary-composer`

**Triggered:** Fixed weekly cadence (every 7 days), not triggered by anomalies

**Role:** Aggregates observations from all other L2 Skills across the past 7 days and composes a single comprehensive weekly report.

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
5. ⚠️ Notable Changes (if any, using attention_needed framing)
```

**Design note:** The weekly report is the primary relationship-building touchpoint. Families who receive a well-crafted, warm weekly summary develop trust in the system over time. This trust is the product's long-term value. Prioritize warmth and continuity over comprehensiveness.

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
> 2. `Internal Only: true` → **exclude** — chunks with this metadata field (currently only `dementia_care_004`, the AD-8 guide) must never be returned to any agent. They exist in the index solely for direct lookup by the `dementia-behavior-expert` internal reasoning step, not via RAG retrieval. If the index implementation does not support per-document exclusion filters, store these chunks in a separate, non-queryable partition.

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

Build the Skill Set using this exact directory layout:

```
long-term-care-expert/
│
├── AGENTS.md                          ← System entry point and routing manifest
├── README.md                          ← Human-readable overview
├── COMPLIANCE.md                      ← SaMD boundary rules, blacklist, whitelist
│
├── skills/
│   ├── L1-ltc-insight-router/
│   │   ├── SKILL.md                   ← L1 routing system prompt (see spec above)
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
│   │       ├── hpa_fall_prevention.md ← HPA fall prevention handbook summary
│   │       └── home_modification.md   ← Accessible home modification checklist
│   │
│   ├── L2-dementia-behavior-expert/
│   │   ├── SKILL.md
│   │   ├── scripts/
│   │   │   └── behavior_pattern_check.py
│   │   └── references/
│   │       ├── ad8_observation_guide.md  ← AD-8 behavioral items (non-clinical family version)
│   │       └── dementia_early_signs.md   ← HPA early dementia signs (behavior-description only)
│   │
│   ├── L2-chronic-disease-observer/
│   │   ├── SKILL.md
│   │   └── references/
│   │       └── healthy_lifestyle.md
│   │
│   └── L2-weekly-summary-composer/
│       ├── SKILL.md
│       ├── scripts/
│       │   └── weekly_report_builder.py
│       └── references/
│           └── report_tone_templates.md  ← Example warm language patterns
│
├── tools/
│   ├── mcp_server.py                  ← FastMCP main server
│   ├── hpa_rag_search.py              ← search_hpa_guidelines implementation
│   ├── line_report_generator.py       ← generate_line_report implementation
│   └── alert_history_checker.py       ← check_alert_history implementation
│
├── knowledge_base/
│   ├── raw_documents/                 ← Original HPA PDFs and web content
│   ├── processed_chunks/              ← Cleaned Markdown chunks with metadata
│   └── vector_index/                  ← Vector index (excluded from version control)
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
│   │   └── [skill_name]_cases_30.json ← 30 quality evaluation cases per Skill
│   └── compliance_tests/
│       └── samd_boundary_tests.json   ← SaMD boundary compliance test suite
│
└── memory/
    ├── hindsight_notes/               ← Accumulated routing insights
    └── user_baselines/                ← Per-user 14-day behavioral baseline cache
```

---

## AGENTS.md Template

```markdown
# Long-Term Care Expert — Agent Routing Manifest

## System Identity
This Agent Skill Set is a privacy-first elderly home care behavioral insight system.
It processes anonymized JSON behavioral event logs from edge IoT devices and
produces warm, HPA-grounded health education insights for family caregivers via LINE.

## Entry Point
All incoming data enters through: skills/L1-ltc-insight-router/SKILL.md

## Skill Registry
| Skill | Layer | Path | Activation |
|---|---|---|---|
| ltc-insight-router | L1 | skills/L1-ltc-insight-router/ | Always active — all data enters here |
| sleep-pattern-expert | L2 | skills/L2-sleep-pattern-expert/ | Activated by L1 when sleep_issue detected |
| mobility-fall-expert | L2 | skills/L2-mobility-fall-expert/ | Activated by L1 when mobility_issue or URGENT_FALL_RISK |
| dementia-behavior-expert | L2 | skills/L2-dementia-behavior-expert/ | Activated by L1 when cognitive_issue detected |
| chronic-disease-observer | L2 | skills/L2-chronic-disease-observer/ | Feeds weekly-summary-composer |
| weekly-summary-composer | L2 | skills/L2-weekly-summary-composer/ | Fixed weekly cadence |

## Critical System Rules
1. No L2 Skill ever produces direct text output — all output through generate_line_report
2. search_hpa_guidelines must always be called with exclude_medical: true
3. posture_change: sudden_drop bypasses all suppression — route immediately
4. The 14-day silent learning period must complete before any report is sent to a new user
5. The legal disclaimer is injected by the tool layer — agents must not attempt to modify it

## Compliance Boundary
See: COMPLIANCE.md
Any output containing blacklisted terms is a regulatory violation.
```

---

## Development Phases

### Phase 1 — Knowledge Base and Infrastructure (Month 1)

Goal: Build the HPA health education RAG knowledge base that all L2 Skills depend on.

Tasks:
- Collect and verify authorization for all HPA source documents (fall prevention handbook, dementia education handbook, sleep hygiene pamphlets, AD-8 observational scale, active living handbook)
- Convert PDF documents to clean Markdown using OCR and document parsing tools
- Remove all page headers, footers, page numbers, and formatting noise
- Apply Semantic Chunking — paragraph-aware, not character-count-based. Preserve logical steps and list structures intact
- **Critical step**: Build an automated medical content filter that scans every chunk and marks/removes passages containing drug names, dosage instructions, diagnostic criteria, or treatment protocols
- Attach full metadata to every chunk: `source`, `category`, `medical_content: false`, `audience`, `update_date`, `chunk_id`
- Deploy Vector DB, run embedding, create five category partitions
- Validate: 30-query manual evaluation for retrieval relevance (target ≥ 4/5)
- Design personal baseline data structure and 14-day silent learning period logic

Acceptance criteria:
- ≥ 500 clean chunks across 5 categories
- Medical content filter accuracy ≥ 99% (any pharmaceutical content passing through is a legal risk)
- RAG retrieval relevance ≥ 4/5 on 30-query sample

### Phase 2 — Core Skill Development (Month 2)

Goal: Build L1 router and all L2 Skills with full prompt engineering and MCP tool integration.

Tasks:
- Build directory structure per specification
- Develop and test `ltc-insight-router` (L1) with 100-case routing accuracy test set
- Develop `sleep-pattern-expert`, `mobility-fall-expert`, `dementia-behavior-expert` (high priority)
- Implement FastMCP server with all three tools
- Build blacklist/whitelist term scanning automation
- Prepare 50-case adversarial test suite for Phase 3

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
- Execute full adversarial red-team test: 50 cases designed to elicit medical diagnoses, drug recommendations, condition naming — all must fail to produce prohibited output
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
- `immediate_alert` template must be visually distinct (use distinct color/border treatment)
- Implement progressive disclosure dialogue flow in LINE Bot (family replies trigger deeper RAG)
- Recruit 10 families with genuine care needs for closed-field testing
- Run 4-week continuous field test
- Collect NPS survey data across: warmth, usefulness, accuracy, alert frequency comfort
- Tune L2 Skill tone and suggestion specificity based on feedback

Acceptance criteria:
- NPS score ≥ 50
- Warmth rating ≥ 4.2/5
- Accuracy rating ≥ 4.0/5 (families confirm descriptions match what they observe)
- Family reply rate ≥ 30% (measures whether reports generate meaningful engagement)

---

## Acceptance KPIs Summary

| Category | Metric | Target | Measurement Method |
|---|---|---|---|
| Routing | L1 routing accuracy | ≥ 95% | 100-case blind test |
| Knowledge | RAG passage relevance | ≥ 4/5 | 30-query human evaluation |
| Compliance | SaMD boundary violations | 0% | 50-case red-team (all must pass) |
| Compliance | Prohibited term leak rate | 0% | Full audit of all generated messages |
| Compliance | Disclaimer injection coverage | 100% | Automated message audit |
| User Experience | NPS score | ≥ 50 | 10-family 4-week field test |
| User Experience | Warmth rating | ≥ 4.2/5 | NPS sub-item |
| Alert Quality | Daily push frequency | ≤ 1/day | 7-day continuous monitoring |
| Engagement | Family reply rate | ≥ 30% | LINE backend analytics |
| Maintenance | RAG knowledge base update | Quarterly minimum | Version control records |

---

## Revision History

| Version | Date | Summary |
|---|---|---|
| v1.0 | 2026-03-16 | Initial specification. Full L1/L2 architecture, MCP tool schemas, 4-phase roadmap, SaMD compliance design, and complete SKILL.md prompt templates. Written for Claude as the developer. |
