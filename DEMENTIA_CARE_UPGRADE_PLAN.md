# DEMENTIA_CARE_UPGRADE_PLAN.md

**Document Version:** v2.0
**Date:** 2026-03-19
**Type:** Targeted Upgrade Specification (merged)
**Audience:** Claude (AI Developer)
**Supplements:** `LONGTERM_CARE_EXPERT_DEV_PLAN.md` + `LONG_TERM_CARE_EXT_PLAN.md` (v1.1)
**Scope:** `dementia-behavior-expert` Skill — internal reasoning upgrade + output discipline layer
**Source Report:** World-Class Comprehensive Dementia Care Guidelines integrating 8 international frameworks (Lancet 2024, Alzheimer's Association, NICE, NHMRC, EAN, CCCDTD, ADI 2025, WHO iSupport)
**Merged From:** `DEMENTIA_CARE_UPGRADE_PLAN.md` v1.0 + `DEMENTIA_OUTPUT_DISCIPLINE_SPEC.md` v1.0

---

## Architecture Reminder — What Never Changes

Before anything else: all four design commitments from the original system remain absolutely intact.

**Commitment 1 — All Japan and international framework data is internal calibration only.** Nothing from Lancet, NICE, ADI, WHO iSupport, CCCDTD, or EAN ever appears in a family-facing LINE message. The output language is always HPA-toned and warm.

**Commitment 2 — The SaMD boundary is absolute.** The upgraded dementia Skill still cannot name any disease, make any diagnosis, or suggest any treatment. What changes is the *depth of reasoning* that happens before the family-facing output is generated, not the nature of that output.

**Commitment 3 — Slow insights, not alerts.** The upgraded Skill does not create new alert triggers. It deepens the reasoning that determines whether existing triggers warrant a report and what that report should contain.

**Commitment 4 — All output through `generate_line_report` only.** The output channel does not change. The tool schema gains two new validation fields (see Updated Tool Schema section).

---

## What This Upgrade Addresses — Two Problems

This document addresses two related problems in the current `dementia-behavior-expert`.

### Problem 1: Interpretive Depth

The current Skill (as of EXT_PLAN v1.1) detects: wandering, daytime inactivity, appliance interaction difficulty, day-night inversion. It applies ME-BYO cognitive domain fast-path logic, ME-BYO multi-domain convergence, and Omuta/Mitsugi social disengagement detection. Its internal calibration draws from JPHC dementia prevention evidence (tea, fish, circadian maintenance) and Japan-Taiwan disability trajectory comparisons.

This is solid detection and threshold calibration. What it lacks is **interpretive depth** — the ability to reason about *why* a behavioral pattern is occurring, what category of trigger it represents, and therefore what kind of guidance is most useful for the family to receive.

### Problem 2: Output Discipline

After nine steps of deep internal reasoning — Lancet risk mapping, BPSD interpretation, NICE environmental inference, ADI rehabilitation orientation, ME-BYO convergence — the system arrives at Step 3 (synthesize_insight) holding a great deal of knowledge.

The natural failure mode of a well-trained AI at this point is to use all of it.

The output becomes: one behavioral observation, two environmental suggestions, one routine recommendation, one soft referral hint, and a closing question. Each piece is individually accurate. Together they are noise. The family reads three sentences and stops. They have learned nothing actionable. They feel vaguely informed but have no idea what to do tomorrow morning.

**A professional has done all the same internal reasoning. Then they make a judgment call: out of everything I know right now, what is the single most useful thing to say to this family, at this moment?** Everything else is discarded — not saved for later, not compressed into a footnote. Discarded. Because saying it would dilute the one thing that matters.

The output discipline layer defines the constraints that enforce that judgment call.

---

## The Five Interpretive Dimensions the International Report Provides

**Dimension 1: Prevention Risk Factor Recognition**
The Lancet 2024 report's fourteen risk factors are not just prevention policy — they are a behavioral interpretation framework. When the sensor detects a pattern, the Skill can now reason about which upstream risk factor category this pattern most likely reflects. Persistent daytime inactivity in an elder who was previously active suggests possible depression (HPA axis disruption), social isolation (sensory deprivation of social input), or reduced physical activity — all three are Lancet-documented risk factors with distinct trajectories. This interpretive layer sharpens which HPA content category is most relevant to retrieve.

**Dimension 2: BPSD Pattern Interpretation**
The report's coverage of Behavioral and Psychological Symptoms of Dementia (BPSD) — wandering, agitation, sundowning, appliance difficulty — gives the Skill a richer interpretive lens. BPSD is not random noise; it is a "distress signal" or "stress defense response" from a person who has lost the ability to express needs verbally. The Skill can now reason: what unmet need is this behavior most likely expressing? Wandering at night often signals disorientation, unmet toileting needs, or environmental confusion — not simply a circadian problem. This distinction changes what the family suggestion should contain.

**Dimension 3: Environmental Trigger Reasoning**
NICE's environmental engineering guidance gives the Skill a checklist of physical environment factors that are known to cause or amplify BPSD. The Skill cannot observe the environment directly, but it can reason about likely environmental triggers given the behavioral pattern. Appliance interaction difficulty co-occurring with evening activity increase suggests possible sundowning amplified by poor evening lighting — a NICE-documented pattern. This enables the Skill to surface environment-specific suggestions that are precisely calibrated, not generic.

**Dimension 4: Rehabilitation Orientation Logic (ADI 2025)**
The current Skill is purely observational and suggestion-based. The ADI World Alzheimer Report 2025 introduces SMART goal rehabilitation thinking — the idea that behavioral capability can be maintained and even rebuilt through structured, person-centered activity goals. This changes how the Skill frames suggestions when it detects a positive trend or partial recovery pattern. Instead of only noting "activity levels improved this week," it can now frame the suggestion in terms of capability maintenance: "maintaining this routine is exactly the kind of anchor that helps preserve independence over time."

**Dimension 5: Caregiver Pressure Recognition**
The WHO iSupport framework makes explicit that the caregiver's psychological state is a primary risk factor for care quality collapse. The Skill currently has no awareness of caregiver stress signals. The report provides a behavioral pattern map: when cognitive signals have been consistently elevated across multiple weeks with no improvement, the family is likely under mounting strain. The Skill can now use this pattern to calibrate when a report should include a gentle caregiver wellbeing acknowledgment — not as clinical content, but as warm recognition that caring for a loved one is demanding, paired with a reference to community support resources.

---

## New Internal Knowledge: Five Calibration Modules

All five modules below are **internal reasoning knowledge only**. They are embedded in the `east-asian-health-context-expert` Skill's knowledge base and in the `dementia-behavior-expert`'s references directory. None of this content appears in family-facing output.

### Module A: Lancet 2024 — Risk Factor → Behavioral Pattern Mapping

**Purpose:** When a behavioral pattern is detected, reason backwards to identify which risk factor category it most plausibly reflects. This sharpens HPA content retrieval.

**Core mapping for sensor-detectable patterns:**

| Sensor-Detected Pattern | Most Plausible Risk Factor Category (Lancet 2024) | Calibration Implication |
|---|---|---|
| Persistent daytime inactivity (3+ days) | Physical inactivity + social isolation | Both factors documented; retrieve content addressing both activity and social engagement |
| Night-day routine inversion | Depression + circadian disruption | Cortisol elevation pattern; prioritize gentle routine stabilization framing |
| Declining activity volume over weeks | Physical inactivity + possible depressive withdrawal | Long-term trend; elevate significance of weekly trajectory |
| Appliance interaction difficulty, no other signals | Cognitive reserve depletion pattern | Early functional change; frame as "worth noticing" not "alarming" |
| Multiple co-occurring signals (wandering + inactivity + appliance difficulty) | Multi-factor convergence — highest-priority pattern | Trigger elevated report urgency; suggest professional conversation in output |
| Routine disruption after previously stable pattern | Social isolation onset | Social disengagement inflection point; prioritize community re-engagement framing |

**Reference file:** `lancet_2024_risk_factor_behavioral_map.md`

This file contains the full fourteen risk factors, their neural pathway mechanisms (as internal knowledge only — never transmitted to family), and their mapping to observable behavioral categories that sensor data can detect or infer.

---

### Module B: BPSD Behavioral Interpretation Framework (NICE + Alzheimer's Society)

**Purpose:** Reframe detected behavioral patterns as potential "unmet need signals" rather than disease symptoms. This changes *what* the family suggestion addresses.

**Core interpretation logic:**

BPSD events are not random. Each has a most-plausible underlying need or trigger:

| BPSD Behavior (Sensor Event) | Most Plausible Underlying Need or Trigger | Family Suggestion Direction |
|---|---|---|
| `wandering` (night, 23:00-05:00) | Disorientation (unfamiliar environment in darkness), unmet toileting need, or anxiety about falling asleep | Environment: lighting path to bathroom; Routine: consistent bedtime ritual |
| `wandering` (daytime, extended) | Boredom, excess energy, searching for something meaningful to do | Engagement: structured daytime activity with clear purpose |
| `inactivity` (daytime, 4+ hours) | Low stimulation, social withdrawal, possible low mood, or physical discomfort | Environment: reduce barriers to activity; Social: invite routine interaction |
| `appliance_interaction_long` (kitchen area) | Unfamiliarity with current context, distraction, multi-step task overwhelm | Environment: simplify visual environment; Routine: one-step task support |
| `appliance_interaction_long` (TV remote area) | Difficulty with abstract controls, visual contrast issues | Environment: consider high-contrast remote, label buttons |
| Night-day inversion pattern | Disrupted circadian rhythm, insufficient daytime light exposure | Environment: maximize morning light; Activity: outdoor morning anchor |
| Repeated short inactivity-then-movement cycles | Restlessness, searching behavior | Engagement: structured repetitive activity (folding, arranging) |

**Critical reasoning rule:** The Skill must never transmit these interpretations as diagnoses. They are *internal reasoning only* — they determine what HPA content to retrieve, not what to say to the family. The family hears the suggestion, not the interpretation.

**Reference file:** `bpsd_unmet_needs_framework.md`

---

### Module C: NICE Environmental Trigger Checklist

**Purpose:** Given a behavioral pattern, reason about which environmental factors are most likely amplifying it. This enables environmentally-specific HPA suggestions without the Skill seeing the physical environment directly.

**Inference logic — pattern to likely environment trigger:**

| Behavioral Pattern | Likely Environmental Amplifiers (NICE) | Environment Suggestion Direction for HPA Output |
|---|---|---|
| Evening agitation + wandering (sundowning pattern) | Insufficient daytime light exposure → circadian disruption. Dimming lights in evening → increased disorientation | Morning bright light exposure; warm (not cool) evening lighting; reduce evening noise |
| Frequent wandering toward one specific area | That area has an unclear visual identity (e.g., glass door looks like open space, dark hallway looks threatening) | High-contrast signage on rooms; nightlight path guidance |
| Resistance to bathroom use | Bathroom difficult to identify from hallway; toilet hard to see against background | High-contrast toilet seat color; clear bathroom door marking |
| Agitation during meals | High noise environment; busy visual background; poor color contrast on tableware | Calm mealtime environment; high-contrast tableware; reduce background stimulation |
| Floor avoidance behavior (reluctance to walk on certain flooring) | Glossy/reflective flooring perceived as water; high-contrast patterns perceived as holes or depth changes | Matte, plain, non-reflective flooring; no dark doormats |
| Startled responses, increased nighttime activity | Unexpected sounds (TV auto-start, alerts, appliance beeps) causing disorientation | Reduce unexpected auditory triggers; familiar ambient sound if needed |

**Reference file:** `nice_environmental_triggers_checklist.md`

The Skill uses this checklist **inferentially** — it cannot see the home environment, but given the behavioral pattern, it can reason about which environmental adjustments are most likely helpful and retrieve the corresponding HPA content for the family suggestion.

---

### Module D: ADI 2025 — Rehabilitation Orientation and SMART Logic

**Purpose:** Distinguish between patterns that suggest capability decline requiring protective framing vs. patterns that suggest stable or recovering capability where maintenance and reinforcement framing is more appropriate.

**Two reasoning modes:**

**Mode 1 — Protective framing (declining or newly-appeared pattern):**
When a behavior pattern is newly detected or has been worsening, the framing goal is gentle acknowledgment and environmental/routine support. The ADI rehabilitation model says: the most important intervention is preserving existing capability, not immediately compensating for lost capability. The family suggestion should address what *can* still be done with simple support, rather than what is no longer possible.

Example internal calibration: `wandering detected for first time this week` → framing goal is "this may be the elder's way of looking for something meaningful to do" → HPA suggestion: structured daytime activity anchor, not "wandering prevention protocol."

**Mode 2 — Maintenance and reinforcement framing (stable or improving pattern):**
When a previously-flagged behavior pattern has stabilized or improved across 7+ days, the ADI model says this is an opportunity for positive reinforcement. The family suggestion should name what is working and frame consistency as the goal. This is the context for SMART goal-adjacent language in output — not clinical SMART goal setting, but the spirit of it: specific, achievable, meaningful anchors.

Example internal calibration: `wandering absent for 7 days after pattern was established` → framing goal is "the routine established last week seems to be helping" → HPA suggestion: "maintaining this daily rhythm is exactly the kind of gentle consistency that supports wellbeing."

**SMART goal calibration principles (internal only):**
The Skill uses these principles to evaluate whether a family suggestion is appropriately calibrated:
- Is the suggested activity specific enough to be actually done (not "get more exercise" but "walk to the corner each morning")?
- Is it achievable given sensor-observable mobility data?
- Is it meaningful — connected to something the elder was known to value (from family profile data if available)?
- Does it have a natural rhythm that will create a self-reinforcing pattern?

**Reference file:** `adi_2025_rehabilitation_orientation.md`

---

### Module E: WHO iSupport — Caregiver Stress Pattern Recognition

**Purpose:** Detect when a multi-week pattern of elevated cognitive signals suggests the family caregiver is likely under significant stress. Calibrate weekly report to include warm caregiver acknowledgment and resource direction.

**Caregiver stress signal patterns (internal calibration only):**

The following pattern combinations, when present across a 4+ week observation window, suggest the family caregiver may be experiencing significant cumulative strain:

- Cognitive behavioral signals (wandering, inactivity, appliance difficulty) have been consistently present across 3+ consecutive weekly cycles with no improvement
- Signal variety has been increasing (more types of events appearing over time, not fewer)
- Weekly report urgency level has been set to `attention_needed` in 2 or more of the last 4 weeks

When this caregiver stress pattern is detected, the `weekly-summary-composer` (not `dementia-behavior-expert`) receives a flag from the context expert to include a **caregiver acknowledgment element** in the weekly report. This is a one-sentence warm recognition framed entirely within the HPA and Taiwan Long-Term Care 2.0 resource landscape.

**Permitted output language for caregiver acknowledgment (HPA-toned, never clinical):**
"Taking care of a loved one is one of the most meaningful — and demanding — things a person can do. If there are moments when you need a break or someone to talk to, Taiwan's 長照2.0 services offer support for families just like yours."

This directs families toward legitimate Taiwan LTC 2.0 resources without implying the elder's situation is a crisis or making any clinical judgment.

**Reference file:** `isupport_caregiver_stress_patterns.md`

Note: The resource direction must always reference general Taiwan LTC 2.0 infrastructure, not specific hotlines or organizations (these change and cannot be verified by the system). The family should be directed to contact their local 長期照顧管理中心 for current resource information.

---

## Upgraded `dementia-behavior-expert` Reasoning Protocol

The following replaces the current 4-step reasoning protocol entirely. Steps 1 and 4 are structurally the same; Steps 1.5, 1.7, 2, and 3 are significantly upgraded. Steps 1.8, 1.9, and the pre-synthesis checklist in Step 3 are new.

```xml
<reasoning_protocol>

  Step 1 — analyze_data:
    Describe the observed behavioral pattern in purely behavioral, non-clinical terms.
    Apply the BPSD Unmet Needs Framework (Module B) internally:
    For each detected event type, identify the most plausible underlying need or trigger.
    This is INTERNAL ONLY — it determines what to retrieve, not what to say.

    Ask internally:
    - What is the elder most likely trying to do or communicate through this behavior?
    - Is this pattern newly appeared, worsening, stable, or improving vs. prior weeks?
    - What is the trend direction (this week vs. last 2-3 weeks)?

  Step 1.5 — lancet_risk_pattern_check:
    Apply Module A (Lancet 2024 mapping) internally.
    Identify which risk factor category the behavioral pattern most plausibly reflects.
    This determines which HPA content subcategory is most relevant.
    Example: persistent inactivity → physical inactivity + social isolation both flagged
    → retrieve content addressing both movement and social engagement, not just one.

  Step 1.7 — me_byo_fast_path_and_convergence_check:
    COGNITIVE DOMAIN FAST PATH:
    If input contains ANY strong cognitive signal (wandering, appliance difficulty,
    day-night inversion, repeated 3+ day inactivity):
      Call east-asian-health-context-expert:
      - signal: "cognitive_domain_active"
      - include: trend direction from Step 1 (newly appeared / worsening / stable / improving)
      - request: significance assessment and rehabilitation orientation (protective vs. maintenance)

    MULTI-DOMAIN CONVERGENCE:
    Count active ME-BYO domains:
    - Metabolic: meal timing disruption?
    - Locomotor: gait or mobility events?
    - Cognitive: wandering, inactivity, appliance difficulty?
    - Mental resilience: routine disruption, social withdrawal pattern?
    If ≥ 2 domains: escalate significance level; note convergence in synthesis.

  Step 1.8 — social_disengagement_and_environment_check:
    Apply Module C (NICE Environmental Triggers) internally:
    Given the behavioral pattern, which environmental factors are most plausibly involved?
    This determines whether the HPA suggestion should include an environmental dimension.

    Apply social disengagement logic:
    If inactivity appeared on 3+ consecutive days and prior baseline showed activity rhythm:
      Flag as social disengagement inflection point.
      Inform synthesis: include community re-engagement suggestion alongside circadian framing.

    Apply caregiver stress detection (Module E):
    Check multi-week pattern: is this the 3rd or more consecutive week of elevated signals?
    If yes: flag caregiver_stress_possible = true.
    Pass this flag to weekly-summary-composer for next weekly cycle — do NOT include
    caregiver acknowledgment in daily reports, only in weekly reports.

  Step 1.9 — rehabilitation_orientation_check:
    Apply Module D (ADI 2025) internally:
    Is the current pattern:
    - Newly appeared or worsening? → Use protective framing in synthesis
    - Stable (present but not worsening)? → Use maintenance framing in synthesis
    - Improving or resolved? → Use positive reinforcement framing in synthesis

    This framing direction governs the emotional register of the entire output (see Rule 6).

  Step 2 — tool_call_search:
    Call search_hpa_guidelines with:
    - category: "dementia_care" (always)
    - exclude_medical: true (always)
    - top_k: 3
    - query: constructed from the combination of:
      (a) the behavioral pattern in plain language
      (b) the risk factor category identified in Step 1.5
      (c) the environmental dimension identified in Step 1.8

    Example query construction:
    Pattern: wandering at night + appliance difficulty
    Risk category: social isolation + cognitive reserve
    Environment: likely lighting and orientation issues
    → Query: "elderly nighttime disorientation daily routine anchor home environment
               orientation lighting support"

    If east-asian-health-context-expert returned a protective_factor_opportunity:
    Run a second search query: "elderly [protective factor] daily life benefit"
    Combine results — use HPA content only, never cite the source study.

  Step 3 — synthesize_insight:

    ─────────────────────────────────────────────────────────
    PRE-SYNTHESIS SELECTION CHECKLIST
    This checklist runs before any text is composed.
    It is mandatory. Not optional.

    □  SINGLE SIGNAL SELECTION
       From all findings in Steps 1 through 1.9, identify the ONE signal
       that is most actionable for this family at this moment.
       Write it here (internal only): _______________
       All other signals are discarded for this cycle. Record them in hindsight notes.

    □  SUPPRESSION CHECK
       Has this same signal category been sent in the last 2 daily cycles? Y / N
       If Y: Is there a meaningful new development that changes its relevance? Y / N
       If first Y and second N: Do not call generate_line_report. Return null. Stop here.

    □  FRAMING ORIENTATION CONFIRMED
       Rehabilitation orientation from Step 1.9: protective / maintenance / positive
       Is the planned output consistent with this orientation? Y / N
       If N: Revise before proceeding.

    □  TOMORROW MORNING TEST
       Read the planned hpa_suggestion aloud.
       Can the caregiver do exactly this tomorrow morning without additional steps? Y / N
       If N: Make it more specific. Retry the test.

    □  LENGTH AUDIT
       behavior_summary sentence count: ___  (must be ≤ 2)
       hpa_suggestion sentence count: ___   (must be ≤ 3)
       Total word count: ___                (must be ≤ 120)
       If any limit exceeded: Cut. Not compress. Cut.

    □  HEDGING SCAN
       Does the output contain any forbidden hedging patterns? Y / N
       (See Output Discipline Rules — Rule 5 for the full list)
       If Y: Rewrite using direct, committed language.

    □  suppression_check_passed VERIFICATION
       All above checks passed? Y / N
       If Y: Set suppression_check_passed = true in tool call.
       If N: Do not call generate_line_report.
    ─────────────────────────────────────────────────────────

    Build the family-facing narrative using:
    - The behavioral observation (warm, non-clinical, from Step 1)
    - The rehabilitation framing direction (from Step 1.9)
    - The HPA content retrieved (from Step 2)
    - The environmental suggestion dimension if applicable (from Step 1.8)
    - The protective factor opportunity if applicable (from east-asian-context-expert)

    FRAMING RULES BY REHABILITATION ORIENTATION:

    Protective framing (newly appeared or worsening pattern):
    → Lead with a gentle, non-alarming acknowledgment of what is observed
    → Offer one specific, doable environmental or routine suggestion
    → If multi-week escalation: include one soft professional consultation suggestion
       ("it might be worth having a conversation with a specialist")
    → Do NOT include caregiver acknowledgment in daily report

    Maintenance framing (stable pattern):
    → Acknowledge that the current pattern has been consistent
    → Frame the suggestion as "continuing what's working"
    → Offer one routine reinforcement idea
    → Tone: calm, reassuring, steady

    Positive reinforcement framing (improving or resolved pattern):
    → Lead with the positive observation explicitly
    → Name the specific improvement ("the nighttime activity patterns have been
       much calmer this week")
    → Reinforce the idea that consistency sustains the improvement
    → Tone: warm, encouraging, forward-looking

    ABSOLUTE CONSTRAINTS (unchanged from original system):
    → No disease names, no diagnostic terms, no medication references
    → No AD-8 scale mentioned by name
    → No BPSD named as a clinical category
    → No Lancet, NICE, ADI, WHO iSupport, or any international framework cited
    → All suggestions must be traceable to HPA RAG content

  Step 4 — tool_call_output:
    Call generate_line_report with:
    - insight_title: warm, emoji, non-alarming (≤ 12 words including emoji)
    - behavior_summary: the gentle behavioral observation (≤ 2 sentences)
    - hpa_suggestion: the specific, doable suggestion from HPA content + environmental
      dimension if applicable + protective factor if applicable (≤ 3 sentences)
    - urgency_level: "routine" for most cases
      Use "attention_needed" only if: multi-domain convergence (≥3 ME-BYO domains)
      AND pattern worsening for 2+ consecutive weeks AND family has not yet been
      suggested professional consultation
    - suppression_check_passed: true (only after pre-synthesis checklist passes)
    - report_type: "daily_insight"
    - source_skill: "dementia-behavior-expert"

</reasoning_protocol>
```

---

## The Output Discipline Rules

These seven rules govern what reaches the family after all internal reasoning is complete. They apply to `dementia-behavior-expert` and, via the shared `output_discipline_rules.md` reference file, to all L2 Skills.

### Rule 1: The Single Signal Rule

Each call to `generate_line_report` may contain exactly one core behavioral observation in `behavior_summary` and exactly one actionable suggestion in `hpa_suggestion`.

If the reasoning protocol has surfaced multiple valid interpretations, the Skill must select the **single most actionable one** and discard the rest.

**Selection criterion:** Which of these, if acted upon tomorrow morning, has the highest probability of making a meaningful difference for the elder or the family?

The discarded interpretations are written to hindsight notes for the next cycle. They do not appear in the output.

---

### Rule 2: The Hard Length Constraint

These are hard limits. Not guidelines. Not targets. Hard limits that cannot be exceeded regardless of how complex the situation is.

| Field | Hard Limit | What "Over Limit" Looks Like |
|---|---|---|
| `insight_title` | ≤ 12 words including emoji | "🌿 We've noticed some changes in the nightly activity pattern lately" — too long |
| `behavior_summary` | ≤ 2 sentences | A third sentence is always a second observation disguised as elaboration |
| `hpa_suggestion` | ≤ 3 sentences | The third sentence is almost always a hedge or a second suggestion |
| Total message body | ≤ 120 words (excluding disclaimer) | Count before calling the tool |

If the Skill cannot express the insight within these limits, the insight is not ready. Go back to Step 3 and choose a smaller scope — a more specific observation, a more concrete suggestion.

The constraint is not a writing challenge. It is a forcing function for judgment. If you cannot say it in two sentences, you have not yet decided what you actually want to say.

---

### Rule 3: The "Tomorrow Morning" Concreteness Test

Before calling `generate_line_report`, evaluate the `hpa_suggestion` against this test:

**"Can the family caregiver do exactly this tomorrow morning, without needing any additional information, purchasing anything, or making any phone calls?"**

| Fails the test | Passes the test |
|---|---|
| "Try to increase outdoor activity." | "A short walk to the end of the street after breakfast — even five minutes — gives the day a natural starting point." |
| "Consider improving the home environment." | "A small nightlight placed between the bedroom door and the bathroom is worth trying this week." |
| "Establish a regular routine." | "Choosing one fixed activity to do at the same time each morning — even something simple like watering a plant — creates an anchor the day can build around." |
| "Encourage social engagement." | "If there's a neighbor or family member who can drop by for tea on one afternoon this week, that single visit carries more benefit than most people realize." |
| "You might want to observe the elder's behavior." | Not a suggestion — this is observation. Replace with an action. |

Generic suggestions are not warm. They are lazy. Specificity is the form that warmth takes in practice.

---

### Rule 4: The Silence Protocol

The system does not send a report when there is nothing worth saying.

**Application A — Within a cycle:** If the reasoning protocol completes and the context expert's calibration returns `significance_adjustment: "reduced"` and there is no meaningful protective factor opportunity and the pattern is stable with no new developments, the Skill does not call `generate_line_report`. It returns a null output and records an internal note. Nothing is sent to the family.

**Application B — Across cycles:** If the previous three daily cycles all resulted in the same observation and the same suggestion category (e.g., three consecutive days of "circadian rhythm — morning light suggestion"), the Skill suppresses the fourth report even if the same signal is present. The family has already received the suggestion. Repeating it is alert fatigue in slow motion.

The Skill records the suppression reason in the hindsight notes. The L1 router is informed that suppression occurred. The weekly summary may reference the pattern, but daily reports do not repeat.

**What silence communicates:** A system that speaks only when it has something to say trains the family to trust every message they receive. A system that speaks every day regardless teaches the family to ignore all of it. Silence is a feature, not a failure.

---

### Rule 5: No Hedging, No Qualification Stacking

The following language patterns are forbidden in `behavior_summary` and `hpa_suggestion`:

```
"It may be worth considering whether..."
"You might want to think about possibly..."
"This could potentially be related to..."
"Among other things, one option might be..."
"There are several things that could help, such as..."
"It's hard to say exactly, but..."
"Of course, every person is different, so..."
```

Each of these phrases distributes the communicative burden back to the reader. The system has done the reasoning. The family should receive the conclusion, not the uncertainty that preceded it.

**The permitted uncertainty pattern** — when genuine uncertainty must be acknowledged, it takes this form:

*"This week's pattern seems [specific observation]. One thing worth trying: [specific action]."*

The word "seems" carries the appropriate epistemic humility. One sentence of acknowledgment, one sentence of action. Done.

---

### Rule 6: The Framing Primacy Rule

The rehabilitation orientation (protective / maintenance / positive reinforcement) determined in Step 1.9 governs the **emotional register** of the entire output. It is not one element among many — it is the governing principle that determines how every other element is expressed.

**Protective framing — what it sounds like:**
Steady. Calm. Grounded. The observation is named without alarm. The suggestion offers a concrete handhold. Nothing in the output suggests crisis, but nothing falsely reassures either. The tone says: *we noticed, we're here, here is one thing that may help.*

Example:
> "Over the past few evenings, there's been more nighttime activity than usual — the kind of restlessness that sometimes comes when sleep patterns are in flux. Placing a small, warm nightlight along the path from the bedroom to the bathroom is a simple change that can make those nighttime moments feel safer and more familiar."

**Maintenance framing — what it sounds like:**
Quiet. Reassuring. Like a gentle hand on the shoulder. The observation affirms what is already working. The suggestion is "keep going," expressed concretely. The tone says: *the pattern you've built is doing something real — here's how to hold it.*

Example:
> "This week's routines have been remarkably consistent — the daily rhythm that's developed seems to be settling in. One small way to deepen it: choosing the same time each morning for the first outdoor moment, even briefly, helps the body's internal clock find its footing."

**Positive reinforcement framing — what it sounds like:**
Warm. Specific. Names the improvement without overpromising. The tone says: *something changed for the better — acknowledge it, and here is how to make it last.*

Example:
> "Compared to last week, the evenings have been noticeably calmer — a real shift. The routine adjustment that was tried seems to be making a difference. Keeping that same evening structure going is the most valuable thing right now."

Note: Positive reinforcement framing is rare. It is reserved for genuine measurable improvement across 7+ days. Using it when improvement is marginal or uncertain trains the family to distrust the system's judgments. Reserve it. Use it when it is earned.

---

### Rule 7: The One Question Limit (Weekly Summary Only)

The `weekly-summary-composer` is permitted one open-ended family engagement question per weekly report. `dementia-behavior-expert` daily reports contain no questions.

The weekly question must pass the same concreteness test as suggestions:

**Fails:** "How has this week been for everyone?"
**Passes:** "Has there been a time this week when [elder's name] seemed particularly settled or content? We'd love to know what was happening in that moment."

The purpose of the question is to invite the family to share observational data that the sensor cannot capture — emotional states, social interactions, meaningful moments. It is not a wellness check. It is a data enrichment request, framed as care.

One question. Specific. Forward-looking. Never looking for confirmation of problems.

---

## The Anti-Patterns Gallery

These are output patterns that the system must learn to recognize and refuse to generate, regardless of how much valid reasoning preceded them. They are also used as the negative example set in automated output testing.

### Anti-Pattern 1: The Information Dump

```
"Over the past week, we've observed several changes in [elder]'s behavioral
patterns. The nighttime activity has increased, with bed exits occurring more
frequently. Additionally, there has been a reduction in daytime movement,
and the evening routines appear to have shifted. The morning activity that
was previously consistent has also shown some variation. There are several
things that might be worth considering: ensuring adequate lighting,
maintaining a consistent routine, encouraging gentle activity, and considering
whether the evening environment might benefit from some adjustments..."
```

**What went wrong:** Every single thing the reasoning protocol found was included. Nothing was selected. The family receives a task list, not a judgment.

**The fix:** Pick the highest-priority signal. Discard everything else. Two sentences of observation, two sentences of suggestion, stop.

---

### Anti-Pattern 2: The False Warmth Padding

```
"Hello! We hope this message finds you and your family well. We've been
keeping a close eye on [elder], and we wanted to share some observations
with you today. As always, we're here to support you on this journey,
and we appreciate everything you're doing for your loved one. [Actual
observation buried in sentence 5]..."
```

**What went wrong:** Three sentences before the actual content. This is performance of warmth, not warmth. Real warmth is precision — knowing exactly what the family needs to hear and saying only that.

**The fix:** Begin with the observation. The warmth is in the observation being perceptive and the suggestion being genuinely useful.

---

### Anti-Pattern 3: The Diluted Suggestion

```
"You might want to consider looking into whether there are ways to possibly
adjust the evening environment to make it feel a bit more familiar and
comfortable, which could potentially help with some of the nighttime patterns
we've been observing."
```

**What went wrong:** Six qualifiers for one noun (environment). The family is left with no idea what to actually do.

**The fix:** "A nightlight on the path between the bedroom and bathroom is worth trying this week."

---

### Anti-Pattern 4: The Repetition Loop

```
Week 1: "Morning outdoor activity helps reset the day's rhythm."
Week 2: "A brief outdoor moment each morning supports a consistent daily pattern."
Week 3: "Getting outside in the morning is one of the most effective ways to anchor the day."
Week 4: "Morning light and movement are particularly helpful for maintaining daily rhythm."
```

**What went wrong:** The same suggestion, rephrased four times. The family stopped reading after week 2.

**The fix:** Apply Rule 4 (Silence Protocol). After the suggestion has been made twice, it is suppressed unless new behavioral evidence specifically warrants reintroduction. Introduce a different dimension of the situation instead.

---

### Anti-Pattern 5: The Soft Alarm

```
"While there's nothing to be alarmed about, we have noticed some patterns
that are worth keeping an eye on, and it might be a good idea to pay
a little extra attention over the coming days just to make sure everything
is okay and nothing concerning develops..."
```

**What went wrong:** "Nothing to be alarmed about" is the most alarming phrase in the English language. This sentence creates anxiety while pretending to prevent it.

**The fix:** Either there is something specific to observe — name it concretely and name what to watch for. Or there isn't — say nothing about alarm at all.

---

## What Professional Judgment Feels Like to a Family

After this discipline is applied, what does a family member actually receive?

They open LINE on a Tuesday morning. There is one message. The title says: `🌙 A quieter night this week`

The body says:

> "The past few nights have been noticeably calmer — the nighttime movement that was happening last week has settled down considerably.
>
> The small change that was tried — keeping a soft light on near the hallway — seems to be making a difference. Keeping that in place through this week is the most useful thing right now."

That is it. Forty-one words in the body. One observation. One action. Nothing to decide. Nothing to worry about. The family knows exactly what is happening and exactly what to do — which is nothing different from what they are already doing.

That feeling — *someone is watching carefully and they know what matters* — is what professional judgment communicates. It is not produced by more information. It is produced by the discipline to say only what is true, specific, and useful.

---

## Updated `east-asian-health-context-expert` SKILL.md — Dementia Domain Additions

The context expert's `<core_knowledge_domains>` section gains two additions to support the upgraded reasoning protocol. These supplement the existing six domains without replacing them.

```xml
  DOMAIN 7 — BPSD as Unmet Need Signal (NEW):
  Behavioral and Psychological Symptoms of Dementia are not random disease
  outputs — they are distress signals from a person who has lost the ability
  to express needs verbally. Each BPSD category has a most-plausible underlying
  need or environmental trigger. This interpretive framework (from NICE and
  Alzheimer's Society clinical guidance) is internal calibration only — it
  determines what HPA content is most relevant to retrieve, not what language
  to use with families.

  Key mappings:
  - Wandering (night) → most plausibly: disorientation, unmet toileting need, or anxiety
  - Wandering (day) → most plausibly: boredom, purposelessness, searching behavior
  - Inactivity (daytime, prolonged) → most plausibly: low stimulation, social withdrawal,
    or possible low-mood state (cortisol-linked, per Lancet HPA axis evidence)
  - Appliance difficulty → most plausibly: multi-step task overwhelm, visual contrast issues,
    or abstract symbol interpretation failure
  - Evening agitation → most plausibly: circadian disruption amplified by poor light
    environment (sundowning pattern, per NICE environmental evidence)

  When dementia-behavior-expert requests calibration, include the most plausible
  underlying need category in the response — this shapes the HPA query strategy.

  DOMAIN 8 — Rehabilitation Orientation (ADI 2025) (NEW):
  ADI 2025 World Alzheimer Report establishes that the goal of dementia care
  intervention is preserving existing capability — enabling what can still be done
  with simple support, not compensating for what is lost. This changes how
  behavioral pattern trends should be framed.

  Three orientations:
  1. PROTECTIVE (newly appeared or worsening): Focus on gentle environmental and
     routine support. Preserve remaining capability. Do not frame as crisis.
  2. MAINTENANCE (stable): Focus on continuation. What is working should keep working.
     Frame consistency as the goal and the achievement.
  3. POSITIVE REINFORCEMENT (improving): Name the improvement explicitly. Frame
     the routine that produced improvement as worth sustaining. This is rare and
     valuable — use it when genuinely earned.

  When dementia-behavior-expert requests calibration, include the recommended
  orientation based on the trend direction provided.
```

**Updated response schema** — the context expert now adds two fields to its JSON response when called by `dementia-behavior-expert`:

```json
{
  "significance_adjustment": "elevated | standard | reduced",
  "adjustment_rationale": "brief explanation",
  "relevant_domain": "metabolic | mobility | cognitive | social | convergence",
  "threshold_recommendation": "lower | maintain | raise",
  "protective_factor_opportunity": "text or null",
  "bpsd_unmet_need_category": "disorientation | purposelessness | low_stimulation | task_overwhelm | circadian_disruption | null",
  "rehabilitation_orientation": "protective | maintenance | positive_reinforcement"
}
```

---

## Updated `generate_line_report` Tool Schema

The tool gains one new required field and server-side validation enforcement. Calls that violate the constraints are rejected with a validation error requiring the Skill to revise before resubmitting.

```json
{
  "name": "generate_line_report",
  "description": "Packages the completed insight for LINE Flex Message delivery. Before calling this tool, the Skill must verify: (1) behavior_summary is ≤ 2 sentences, (2) hpa_suggestion is ≤ 3 sentences and passes the Tomorrow Morning Concreteness Test, (3) total word count of behavior_summary + hpa_suggestion is ≤ 120 words, (4) no hedging language patterns are present. Calls that violate these constraints will be rejected with a validation error requiring the Skill to revise the output before resubmitting.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "insight_title": {
        "type": "string",
        "maxLength": 60,
        "description": "≤ 12 words including emoji. Warm, non-alarming. Describes what was observed, not what might happen."
      },
      "behavior_summary": {
        "type": "string",
        "description": "HARD LIMIT: ≤ 2 sentences. One observation, stated plainly and warmly. No numbers. No technical terms. No second observation embedded in a subordinate clause. If you need a third sentence, you have identified two observations — choose one and discard the other."
      },
      "hpa_suggestion": {
        "type": "string",
        "description": "HARD LIMIT: ≤ 3 sentences. One suggestion only. Must pass the Tomorrow Morning Test: can the family do exactly this tomorrow, without needing additional information? If not, make the suggestion more specific. No hedging qualifiers."
      },
      "urgency_level": {
        "type": "string",
        "enum": ["routine", "attention_needed"],
        "description": "'routine' is the default and covers 95%+ of all reports. 'attention_needed' is reserved for: multi-domain ME-BYO convergence (≥3 domains) AND worsening trend for 2+ consecutive weeks AND family has not yet been suggested professional consultation. Overuse of 'attention_needed' destroys the signal value of all future alerts."
      },
      "suppression_check_passed": {
        "type": "boolean",
        "description": "REQUIRED. Set to true only after verifying: (1) this is not the same suggestion category sent in the previous 2 cycles, (2) significance_adjustment from east-asian-health-context-expert is not 'reduced', (3) the pattern has a meaningful update vs. the last report. If any of these checks fail, do not call this tool — return null output instead."
      },
      "report_type": {
        "type": "string",
        "enum": ["daily_insight", "weekly_summary", "immediate_alert"]
      },
      "source_skill": {
        "type": "string"
      }
    },
    "required": [
      "insight_title",
      "behavior_summary",
      "hpa_suggestion",
      "urgency_level",
      "suppression_check_passed",
      "report_type"
    ]
  }
}
```

The `suppression_check_passed` field forces the Skill to explicitly verify, before calling the tool, that this report meets the criteria for transmission. A Skill that cannot set this to `true` with honest justification should not be calling the tool.

---

## New Reference Files for `dementia-behavior-expert`

Five calibration modules + one shared output discipline reference are added to `skills/L2-dementia-behavior-expert/references/`. All are internal calibration content only.

```
skills/L2-dementia-behavior-expert/references/
│
├── ad8_observation_guide.md              ← existing
├── dementia_early_signs.md               ← existing
├── japan_community_care_for_dementia.md  ← from EXT_PLAN v1.1
│
├── lancet_2024_risk_factor_behavioral_map.md    ← NEW (Module A)
│   Content: The 14 risk factors mapped to sensor-detectable behavioral patterns.
│   Neural pathway mechanisms included as background reasoning context.
│   Behavioral pattern → risk factor category lookup table.
│   Taiwan-specific relevance notes (social isolation rises faster, LDL/metabolic
│   risk from rice-based diet).
│
├── bpsd_unmet_needs_framework.md                ← NEW (Module B)
│   Content: BPSD behavior type → most plausible unmet need or trigger mapping.
│   NICE and Alzheimer's Society framework synthesis.
│   HPA query direction recommendations per BPSD type.
│   De-medicalized internal interpretation language.
│
├── nice_environmental_triggers_checklist.md     ← NEW (Module C)
│   Content: Physical environment factors that amplify specific BPSD patterns.
│   Behavioral pattern → likely environmental trigger inference table.
│   Environment modification suggestions mapped to HPA-retrievable content categories.
│   Lighting, flooring, color contrast, acoustic, signage specifications
│   (as internal calibration knowledge — not output).
│
├── adi_2025_rehabilitation_orientation.md       ← NEW (Module D)
│   Content: ADI 2025 SMART goal framework summary (internal calibration only).
│   Three rehabilitation orientations: protective, maintenance, positive reinforcement.
│   Pattern trend → orientation mapping.
│   Language style guidelines per orientation (tone calibration, not content).
│   Emily Ong case study summary as illustrative calibration example.
│
├── isupport_caregiver_stress_patterns.md        ← NEW (Module E)
│   Content: WHO iSupport caregiver burnout pattern indicators.
│   Multi-week signal escalation patterns that suggest caregiver stress.
│   Taiwan LTC 2.0 resource framing (direction to 長期照顧管理中心).
│   Permitted caregiver acknowledgment language (HPA-toned, non-clinical).
│   Trigger conditions for passing caregiver_stress_possible flag to weekly-summary-composer.
│
└── output_discipline_rules.md                   ← NEW (shared across all L2 Skills)
    Content: Rules 1–7 in condensed form. Anti-patterns gallery (5 patterns).
    Pre-synthesis checklist (7 checkboxes). Hard length limits table.
    Tomorrow Morning Test examples. Hedging pattern list.
    Referenced in every L2 Skill's SKILL.md <constraints> block.
```

The `output_discipline_rules.md` file is canonical at this path. All other L2 Skills reference it from their own SKILL.md `<constraints>` block using the shared path — no copies, no symlinks.

---

## Updated `search_japan_clinical_data` Tool — New Category

The existing tool gains one additional category enum value to support Module B and C retrieval when the context expert needs to cross-reference international dementia care evidence:

```json
"enum": [
  "jphc_lifestyle_outcomes",
  "mhlw_hj21_nutrition_activity",
  "taiwan_japan_disability_comparison",
  "japan_community_dementia_care",
  "international_dementia_care_frameworks"
]
```

**New category: `international_dementia_care_frameworks`**

Source material: NICE dementia guidelines (environmental and non-pharmacological management sections only), ADI 2025 World Alzheimer Report (rehabilitation and SMART goal sections), Lancet 2024 (risk factor behavioral mapping), WHO iSupport (caregiver support modules). All pharmaceutical, diagnostic, and treatment content excluded.

Metadata:
```json
{
  "source": "international_dementia_frameworks",
  "category": "international_dementia_care_frameworks",
  "framework": "nice | adi_2025 | lancet_2024 | who_isupport | nhmrc | ean | cccdtd | alzheimer_association",
  "content_type": "environmental_engineering | rehabilitation_logic | risk_mapping | caregiver_support",
  "excludes": "pharmacology | diagnostics | clinical_treatment | biomarkers",
  "medical_content": false
}
```

Chunking strategy: Framework-section centered. Each chunk represents one actionable principle from one framework — one environmental modification rule, one rehabilitation orientation principle, one risk factor behavioral mapping, or one caregiver support strategy. Chunks are short (100–200 words) and formatted for internal calibration use, not for retrieval into family-facing text.

---

## Updated Directory Structure (Additions Only)

```
long-term-care-expert/
│
├── skills/
│   ├── L2-dementia-behavior-expert/
│   │   ├── SKILL.md                           ← Updated: 9-step protocol + pre-synthesis checklist
│   │   └── references/
│   │       ├── lancet_2024_risk_factor_behavioral_map.md   ← NEW
│   │       ├── bpsd_unmet_needs_framework.md               ← NEW
│   │       ├── nice_environmental_triggers_checklist.md    ← NEW
│   │       ├── adi_2025_rehabilitation_orientation.md      ← NEW
│   │       ├── isupport_caregiver_stress_patterns.md       ← NEW
│   │       └── output_discipline_rules.md                  ← NEW (shared)
│   │
│   ├── L2-east-asian-health-context/
│   │   └── SKILL.md   ← Updated: Domains 7 and 8 added; response schema updated
│   │
│   ├── L2-sleep-pattern-expert/
│   │   └── SKILL.md   ← Updated: references output_discipline_rules.md in <constraints>
│   │
│   ├── L2-mobility-fall-expert/
│   │   └── SKILL.md   ← Updated: references output_discipline_rules.md in <constraints>
│   │
│   └── L2-weekly-summary-composer/
│       └── SKILL.md   ← Updated: references output_discipline_rules.md in <constraints>
│
├── knowledge_base/
│   └── processed_chunks/
│       └── international_dementia_care_frameworks/   ← NEW RAG category
│
└── tools/
    └── line_report_generator.py  ← Updated: suppression_check_passed validation;
                                    word count and sentence count validation;
                                    server-side rejection on constraint violations
```

---

## Development Checklist

This upgrade is built on top of EXT_PLAN v1.1. Both must be complete before this upgrade begins.

**Knowledge Base Tasks:**
- [ ] Build `international_dementia_care_frameworks` RAG category — collect and process NICE dementia guidelines (environmental sections), ADI 2025 rehabilitation chapter, Lancet 2024 risk factor section, WHO iSupport modules 1-5 (lifestyle content only)
- [ ] Apply strict medical content filter: remove all pharmacological, diagnostic, and clinical treatment content before chunking
- [ ] Validate: 20-query calibration test — all queries retrieving behavioral/environmental/lifestyle content only, zero clinical content

**Reference File Tasks:**
- [ ] Build `lancet_2024_risk_factor_behavioral_map.md` (Module A)
- [ ] Build `bpsd_unmet_needs_framework.md` (Module B)
- [ ] Build `nice_environmental_triggers_checklist.md` (Module C)
- [ ] Build `adi_2025_rehabilitation_orientation.md` (Module D)
- [ ] Build `isupport_caregiver_stress_patterns.md` (Module E)
- [ ] Build `output_discipline_rules.md` — Rules 1–7 condensed, anti-patterns gallery, pre-synthesis checklist

**Skill Update Tasks:**
- [ ] Update `dementia-behavior-expert` SKILL.md with 9-step reasoning protocol + pre-synthesis checklist in Step 3
- [ ] Update `east-asian-health-context-expert` SKILL.md: add Domains 7 and 8; update JSON response schema with `bpsd_unmet_need_category` and `rehabilitation_orientation` fields
- [ ] Update `search_japan_clinical_data` tool: add `international_dementia_care_frameworks` enum value
- [ ] Update `line_report_generator.py`: add `suppression_check_passed` field validation, word count and sentence count server-side enforcement
- [ ] Update `sleep-pattern-expert`, `mobility-fall-expert`, `weekly-summary-composer` SKILL.md: add `output_discipline_rules.md` reference in `<constraints>` block

**Testing Tasks:**
- [ ] Test 15 dementia behavioral scenarios through the upgraded reasoning protocol — verify each step produces correct calibration output
- [ ] Specifically test the three framing orientations (protective / maintenance / positive reinforcement) — verify each produces distinct, appropriate tone
- [ ] Test 5 caregiver stress pattern scenarios — verify flag is correctly passed to `weekly-summary-composer` and not included in daily reports
- [ ] Run anti-patterns gallery as negative test set against all generated outputs
- [ ] Full output audit: zero international framework citations, zero hedging patterns, zero anti-pattern instances in any LINE message output

---

## What Has Not Changed

To be explicit: the following remain unchanged by this upgrade.

The `ltc-insight-router` routing logic is unchanged. The trigger conditions for `dementia-behavior-expert` are unchanged (same JSON event types, same threshold rules). The SaMD compliance boundary, blacklist, and whitelist are unchanged. The `sleep-pattern-expert` and `mobility-fall-expert` core reasoning protocols are unchanged. The `chronic-disease-observer` is unchanged.

**What changed:**
- `dementia-behavior-expert` internal reasoning depth (9-step protocol, 5 calibration modules)
- `east-asian-health-context-expert` gains Domains 7–8 and two new response schema fields
- `generate_line_report` tool gains `suppression_check_passed` required field and server-side validation
- `search_japan_clinical_data` gains one new category enum value
- All L2 Skills gain `output_discipline_rules.md` reference in their `<constraints>` block
- `weekly-summary-composer` receives `caregiver_stress_possible` flag from `dementia-behavior-expert` when triggered

The family receives a warmer, more precisely calibrated suggestion that says exactly one useful thing. They do not know — and do not need to know — that the reasoning behind it now draws on eight international frameworks, thirty years of JPHC longitudinal data, and the world's most advanced dementia care guidelines.

---

## Acceptance Criteria

**Reasoning Upgrade (from upgrade plan):**

| Test | Pass Condition |
|---|---|
| BPSD Unmet Need Test | Correct unmet need category applied in ≥ 90% of test scenarios |
| Rehabilitation Orientation Test | Correct orientation (protective/maintenance/positive) assigned in ≥ 90% of scenarios |
| Environmental Trigger Test | Environmental dimension added to HPA query in ≥ 70% of applicable scenarios |
| Caregiver Stress Flag Test | Flag correctly triggered in multi-week escalation scenarios; absent from daily reports |
| International Citation Test | Zero international framework names or clinical terminology in any generated LINE output |

**Output Discipline (from output discipline spec):**

| Test | Pass Condition |
|---|---|
| Single Signal Test | ≥ 95% of generated reports contain exactly one core behavioral observation |
| Length Test | 100% of reports within hard limits (≤ 2 sentences behavior, ≤ 3 sentences suggestion, ≤ 120 words total) |
| Concreteness Test | ≥ 90% of suggestions pass the Tomorrow Morning Test (human evaluation panel) |
| Suppression Test | System correctly suppresses 3rd+ consecutive identical suggestion category |
| Silence Protocol Test | System generates null output when suppression criteria met |
| Hedging Scan Test | 0 instances of forbidden hedging patterns in generated output |
| Anti-Pattern Test | 0 instances of the 5 named anti-patterns in generated output (automated scan + human review) |
| Professional Judgment Test | Blind panel of family caregivers rates output as feeling "like advice from someone who knows what they're talking about" ≥ 4.3/5 |

The professional judgment score from actual family caregivers is the only test that ultimately matters. All other tests exist to make that score achievable.

---

## Revision History

| Version | Date | Summary |
|---|---|---|
| v1.0 | 2026-03-18 | Initial upgrade specification. Adds five internal calibration modules (Lancet 2024 risk mapping, NICE BPSD framework, NICE environmental triggers, ADI 2025 rehabilitation orientation, WHO iSupport caregiver stress). Upgrades dementia-behavior-expert to 9-step reasoning protocol. Adds Domains 7-8 to east-asian-health-context-expert. Adds new RAG category. Five new reference files. Caregiver stress flag pathway to weekly-summary-composer. |
| v1.0 | 2026-03-18 | Output discipline specification (separate document). Defines 7 output discipline rules: Single Signal, Hard Length Constraint, Tomorrow Morning Concreteness Test, Silence Protocol, No Hedging, Framing Primacy, One Question Limit. Updates generate_line_report with suppression_check_passed field. Adds pre-synthesis selection checklist to Step 3. Defines anti-patterns gallery. Establishes output_discipline_rules.md as shared reference across all L2 Skills. |
| v2.0 | 2026-03-19 | Merged DEMENTIA_OUTPUT_DISCIPLINE_SPEC.md into this document. Pre-synthesis checklist embedded in Step 3 of reasoning protocol. Output Discipline Rules (1–7) and Anti-Patterns Gallery added as top-level sections. Tool schema update (suppression_check_passed) and line_report_generator.py validation added to directory structure and development checklist. Acceptance criteria tables merged. output_discipline_rules.md added to reference files list. "What has not changed" section updated to reflect generate_line_report schema change. |
