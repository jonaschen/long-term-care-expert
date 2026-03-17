# LONG_TERM_CARE_EXT_PLAN.md

**Document Version:** v1.1  
**Date:** 2026-03-17  
**Type:** Extension Specification — supplements `LONGTERM_CARE_EXPERT_DEV_PLAN.md`  
**Audience:** Claude (AI Developer)  
**Purpose:** Integrate Japanese MHLW / JPHC / NCC data as a second knowledge pillar alongside Taiwan HPA data  
**v1.1 Changes:** Added two missing Japanese official sources — Dementia Supporter Caravan / Omuta City community care model, and Integrated Community Care System (Mitsugi model). Elevated ME-BYO cognitive domain to first-class status in `dementia-behavior-expert`. Added new RAG category `japan_community_dementia_care`. Updated `east-asian-health-context-expert` SKILL.md, directory structure, and KPIs accordingly.

---

## Why This Extension Exists — Read Before Anything Else

The original `LONGTERM_CARE_EXPERT_DEV_PLAN.md` built a complete system anchored entirely in Taiwan HPA health education data. That system works. Its compliance architecture, its L1/L2 routing logic, its three MCP tools, its SaMD defensive guardrails — none of that changes.

But the knowledge base it draws from has a structural limitation: **the HPA provides excellent localized health education content, but it does not provide predictive epidemiology.** It can tell a family what to do today. It cannot tell a designer what patterns will emerge in Taiwan's elderly population over the next twenty years, which chronic disease thresholds are clinically meaningful for East Asian metabolism, or which preventive interventions have demonstrated thirty-year longitudinal efficacy for populations biologically similar to Taiwan's.

Japan fills that gap. Not as a replacement for HPA — as a calibration layer above it.

Taiwan is approximately 20-40 years behind Japan in its super-aging trajectory. Japan's Ministry of Health, Labour and Welfare (MHLW) and the Japan Public Health Center-based Prospective Study (JPHC) have already observed what Taiwan is about to experience: what happens to ADL disability rates as the 75+ cohort expands, how dementia prevalence scales with the oldest-old population, which lifestyle risk factors drive the largest chronic disease burden in rice-based East Asian diets, and what community care architectures actually reduce institutionalization rates over time.

This extension adds Japan as a **second knowledge pillar** in the system. The architecture metaphor: HPA is the ground-level practitioner knowledge (what to say to a family today), and Japanese MHLW/JPHC data is the strategic intelligence layer that determines what the system should be watching for, what thresholds are meaningful, and how to contextualize behavioral trends against a proven longitudinal model.

---

## What Changes and What Stays the Same

**Nothing in the original system changes:**
- The L1/L2 routing architecture is unchanged
- All five L2 Skills continue to operate exactly as specified
- The three MCP tools (`search_hpa_guidelines`, `generate_line_report`, `check_alert_history`) are unchanged
- The SaMD compliance boundary, blacklist, whitelist, and mandatory disclaimer are unchanged
- The 14-day silent learning period and personal baseline system are unchanged
- All output goes through LINE Flex Message as before

**What this extension adds:**
1. A new MCP tool: `search_japan_clinical_data`
2. Three new knowledge base categories in the RAG vector store (Japanese data)
3. A new Layer 2 Skill: `east-asian-health-context-expert`
4. Enriched reasoning instructions for three existing L2 Skills
5. A new dimension in the weekly report: contextual health trajectory framing
6. Updated `AGENTS.md` to reflect the expanded knowledge architecture

The core user experience does not change. Families still receive warm, de-medicalized LINE messages. The difference is that those messages are now calibrated against a richer evidence base — the system knows, for instance, that a Japanese woman consuming three or more servings of white rice daily has a measurable T2D risk elevation, and can therefore contextualize a Taiwanese elder's activity patterns against metabolic risk models that HPA alone cannot provide.

---

## Understanding the Japanese Data — What Claude Must Internalize

Before implementing anything, Claude must understand what each Japanese data source contributes and why it is relevant to a home care IoT system in Taiwan.

### Source 1: MHLW and Health Japan 21 (HJ21)

Health Japan 21 is Japan's national health promotion framework, currently in its third term (launched April 2024). Its relevance to this system is not primarily its targets — it is its **PDCA evaluation cycle** and the **"healthy life expectancy" framing**.

Japan recognized a critical insight that Taiwan's HPA data confirms from a different angle: **living longer does not mean living well longer.** In Japan, the gap between total life expectancy and healthy life expectancy (the period without significant daily activity limitation) is approximately 9-12 years. Taiwan's data shows the same structural problem — the 80+ cohort is the fastest-growing segment, and they face the highest burden of mobility and functional disability.

For the LTC Skill Set, this insight changes how the `weekly-summary-composer` should frame long-term behavioral trends. Instead of just reporting "activity levels this week," the system can contextualize trends against a meaningful goal: maintaining the elder's healthy life expectancy. A gradual decline in mobility activity, contextualized this way, becomes "the pattern we want to catch early, because Japan's 40-year experience shows this is the inflection point."

HJ21's specific nutritional targets — particularly salt reduction and increased vegetable intake — are directly relevant because Taiwan shares the same high-salt dietary culture. When the system observes behavioral patterns that suggest dietary irregularity (meal timing disruption captured by activity sensors), it can now anchor suggestions in a dual-validated evidence base: both HPA and HJ21 point toward the same dietary concerns.

### Source 2: JPHC Study (Japan Public Health Center-based Prospective Study)

The JPHC is the most important single data source this extension adds. Launched in 1990, it covers 140,000 participants across 11 public health centers with over 30 years of follow-up. Its value for this system is specific and concrete:

**White rice and T2D risk:** The JPHC found that Japanese women consuming three to four rice servings daily face a 1.5x elevated T2D risk. This is more pronounced than in Western populations and reflects East Asian metabolic architecture. Taiwan shares the same rice-based dietary pattern. When the LTC system observes activity irregularities that could indicate metabolic disruption, the JPHC provides the evidence base for calibrating when to suggest lifestyle review.

**Green tea, coffee, and dementia prevention:** The JPHC found significant protective effects of moderate green tea and coffee consumption on dementia risk reduction. This is culturally highly relevant — Taiwan has a deep tea-drinking tradition. The `dementia-behavior-expert` Skill can now add a culturally resonant, evidence-anchored dimension to its suggestions: the behaviors already natural to Taiwanese culture (tea drinking) have documented protective effects in a biologically similar population.

**Fish, omega-3 PUFAs, and dementia:** The JPHC identified that high fish and n-3 polyunsaturated fatty acid intake is linked to reduced incidence of disabling dementia. This supplements HPA's general nutrition guidance with East Asian-specific longitudinal evidence.

**Lifestyle and mortality:** JPHC data on smoking (1.7x mortality risk for male smokers, 4.5x lung cancer risk) provides Taiwan-relevant calibration for the `chronic-disease-observer` Skill when long-term activity patterns suggest potential smoking-related health decline.

**Critical architectural note:** The JPHC data is used as a **reasoning calibration layer**, not as direct output content. The system never quotes JPHC statistics to family members — that would be medicalization. Instead, JPHC data informs the internal thresholds and pattern significance logic that the L1 router and L2 Skills use when deciding whether a behavioral pattern warrants attention. The output language remains warm and HPA-grounded.

### Source 3: Japan's Disability and Long-Term Care Research

The disability trajectory comparison between Japan and Taiwan is directly actionable for this system. Key findings:

Japan shows higher ADL disability prevalence (14.95% vs Taiwan's 9.65%), but Taiwan shows higher IADL disability (30.36% vs Japan's 19.30%) and mobility disability (49.82% vs Japan's 36.07%). Taiwan's elderly population faces a **higher burden of functional and mobility limitation**, not institutionalized severe disability.

This has a concrete implication for the LTC system's alert calibration: **mobility events should be weighted more heavily for Taiwanese elders than Japan-based benchmarks would suggest.** When the system is deciding whether a gait slowdown constitutes a trend worth reporting, it should apply a Taiwan-specific sensitivity — the population this system serves is statistically more vulnerable to mobility deterioration than the Japanese benchmark population.

Additionally, Taiwan's data shows loneliness rising faster with age compared to Japan (19-29% at age 65 vs Japan's 13-19%), and this divergence accelerates at older ages. The `weekly-summary-composer` should treat social engagement signals (activity regularity that suggests routine maintenance, response patterns from family members) as higher-priority indicators than a Japan-calibrated system would.

### Source 4: Japan's Community Care Architecture — The Mitsugi Model

The town of Mitsugi in 1974 pioneered the Integrated Community Care System that Japan now deploys nationally. The key insight from Mitsugi was that integrating medical care with community mutual support (neighbors checking on neighbors, not just professional care workers) reduced the "bedridden rate" — the proportion of elderly who become fully dependent — while holding down cost growth.

Taiwan's LTC 2.0 has adopted many of these principles. For the LTC Skill Set, the Mitsugi model reinforces a design principle already present in the original system: **the family caregiver is the actual end-user, not a passive recipient.** The system builds family engagement by design — every report contains an invitation to respond, every weekly summary ends with a question. This is the software analog of the mutual support infrastructure Mitsugi built physically.

### Source 5: ME-BYO Index (Kanagawa Prefecture)

The ME-BYO Index is a pre-disease health status measurement tool developed by Kanagawa Prefecture that measures four domains: metabolic function, locomotor function (mobility), cognitive function, and mental resilience. It shifts the paradigm from binary "healthy vs. sick" to a continuum.

This concept is the intellectual framework underlying the LTC system's entire approach, even though the system does not explicitly reference ME-BYO to families. The system was already built on a continuum model — behavioral patterns exist on a spectrum from baseline to concerning, and the alert suppression logic is specifically designed to capture early movement along that spectrum before it reaches clinical severity. The ME-BYO framework validates this architectural choice with 30 years of Japanese policy evidence.

For the new `east-asian-health-context-expert` Skill (detailed below), ME-BYO's four domains map directly onto the Skill's analytical framework: locomotor = mobility events, cognitive = dementia behavior events, metabolic = chronic disease lifestyle signals, mental resilience = loneliness and social isolation patterns.

### Source 6: JPHC-NEXT — The Functional Disability Prevention Framework

JPHC-NEXT (launched 2011) integrates genomic and biomarker data with lifestyle tracking, specifically designed to identify preventive factors for functional disability — fractures, falls, and dementia — which are the primary drivers of long-term care demand in super-aged societies.

The JPHC-NEXT framework confirms the LTC system's preventive orientation: the highest-value intervention point is **before** clinical disability emerges. The sensor system's ability to detect subtle gait changes, nighttime pattern shifts, and activity irregularities months before they manifest as falls or cognitive decline is precisely what JPHC-NEXT validates as the correct intervention timing.

### Source 7: Dementia Supporter Caravan and Omuta City Dementia Care Model ⚠️ PREVIOUSLY MISSING

**Why this source was missing and why it matters:** The original extension plan focused primarily on epidemiological calibration data (JPHC, HJ21, disability comparisons). This missed a critical second dimension of Japanese dementia care expertise: the **social and community-based care models** that Japan has operationalized at scale. The Japanese MHLW document explicitly identifies these as priority references for a Taiwan-context system, specifically because Taiwan shares the same cultural value of filial obligation (孝道) that these models are designed around.

**Dementia Supporter Caravan (認知症サポーターキャラバン):** This is a Japanese government-backed initiative that trains community members — shopkeepers, neighbors, schoolchildren, transit workers — to recognize early dementia behaviors and respond with patience and support rather than alarm or exclusion. By 2025, over 14 million trained "Dementia Supporters" exist across Japan. The goal is not professional care but **ambient social safety nets**: creating environments where an elder who appears confused in public is gently guided rather than distressed.

For the LTC Skill Set, this model has two concrete implications. First, it validates that **early behavioral signals — hesitation with familiar tasks, confusion in routine environments — are actionable at the community level long before clinical intervention is warranted.** This is exactly the observation space the `dementia-behavior-expert` Skill operates in: the pre-clinical grey zone. Second, it confirms that family members are not the only resource — the system's reports that encourage families to **expand the elder's social routine** (morning walks, community center visits) are prescribing the same social safety net infrastructure that Japan built institutionally.

**Omuta City Dementia Care Model (大牟田市認知症ケアモデル):** Omuta City in Fukuoka Prefecture developed a comprehensive community-based dementia care model that is recognized as one of Japan's most successful examples of aging-in-place for dementia patients. Key elements include the "dementia-friendly town" design (wayfinding, public space adaptations), community networks of neighbors who watch for wandering, and regular "café" gathering spaces for elders with early cognitive changes and their caregivers.

The Omuta model is directly relevant to the LTC system's treatment of social isolation signals. Taiwan's elderly population shows loneliness rising faster with age than Japan's — the Omuta model demonstrates that structured social contact, even informal neighborhood café-style gatherings, significantly delays cognitive decline and reduces caregiver burden. When the `dementia-behavior-expert` observes daytime inactivity and disrupted routine patterns, the Omuta model informs *why* the suggestion to encourage structured social activity is evidence-grounded, even when that suggestion is framed in warm HPA-style language.

**Cultural resonance with Taiwan:** Both models are built around the assumption that family and community — not institutions — are the primary care environment. This maps directly onto Taiwan's high-family-involvement caregiving culture. The system's design of engaging family members as active participants (rather than passive recipients of alerts) is architecturally congruent with both models.

### Source 8: Integrated Community Care System — The Mitsugi Model (深化補充)

The Mitsugi model was mentioned in the original extension plan (Source 4) but not given sufficient treatment as a **knowledge source for the `dementia-behavior-expert` Skill's social isolation dimension**. This section deepens that treatment.

The Mitsugi Integrated Community Care System's core innovation was recognizing that **institutionalization is not the inevitable endpoint of dementia progression** — it is the endpoint of *social isolation during dementia progression*. Elders who maintained community connections, even with moderate cognitive impairment, had significantly delayed transitions to bedridden status compared to those who became homebound.

For the LTC system, this finding has a specific operational implication: the `dementia-behavior-expert` Skill's detection of daytime inactivity and disrupted routine should not only trigger suggestions about circadian rhythm correction (the existing HPA angle) — it should now also trigger awareness of the **social disengagement trajectory**. An elder who was previously active in community routines (shopping, park walks, neighborhood interactions) and is now showing extended inactivity is not just showing a circadian problem. They are showing early social withdrawal, which the Mitsugi model identifies as a primary risk factor for accelerated cognitive decline.

The `east-asian-health-context-expert` Skill must hold this distinction and provide it to `dementia-behavior-expert` when inactivity patterns persist for more than 3 days.

---

## New Skill: `east-asian-health-context-expert`

### Role

This is a Layer 2 Skill that does not generate family-facing reports independently. It is a **reasoning enrichment layer** that three other L2 Skills can consult when they need cross-validated, East Asian-specific context to calibrate whether a behavioral pattern is genuinely significant.

Think of it as an internal consultant: when `mobility-fall-expert` detects a persistent gait slowdown pattern, before generating a report, it can call `east-asian-health-context-expert` and ask "given this elder's profile and the pattern I'm seeing, does the Japan/Taiwan epidemiological evidence suggest this warrants family notification?" The context expert returns an assessment that informs the routing decision, not the family-facing language.

### What This Skill Holds

East Asian metabolic risk calibration for rice-based diet patterns and their relationship to T2D and chronic disease progression (JPHC-grounded).

Japan-Taiwan disability trajectory benchmarks: the knowledge that Taiwan's elderly population has higher mobility and IADL disability burden than Japan, meaning Taiwan-specific sensitivity thresholds should be applied.

The ME-BYO four-domain framework as a structured lens for evaluating whether behavioral patterns across multiple domains are converging toward increased care risk.

JPHC dementia prevention evidence: tea consumption, fish intake, and activity regularity as documented protective factors for the biologically similar Japanese population.

Healthy life expectancy framing: the Japan/HJ21 insight that the goal is not longevity but the quality of the active years, which changes how long-term behavioral trends are contextualized.

### When to Call This Skill

`mobility-fall-expert` should call it when gait slowdown has persisted for more than 5 days — to calibrate whether Taiwan's higher mobility disability baseline makes this pattern more significant than a Japan-derived threshold alone would suggest.

`dementia-behavior-expert` should call it when two or more cognitive behavior signals co-occur — to check whether the ME-BYO framework's convergence across multiple domains elevates the significance of what might appear as individual isolated incidents.

`chronic-disease-observer` should call it when evaluating long-term activity trend declines — to calibrate against East Asian metabolic risk patterns and assess whether dietary rhythm signals are consistent with metabolic risk elevation trajectories documented in JPHC data.

### What This Skill Does NOT Do

It never generates family-facing output directly. All its output is consumed internally by the calling L2 Skill. It never cites JPHC statistics in any user-facing text. It never makes clinical assessments — it provides epidemiological context for pattern significance calibration only.

### SKILL.md System Prompt

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

    DOMAIN 6 — Community Care and Social Isolation Prevention (NEW):
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

## New MCP Tool: `search_japan_clinical_data`

This tool extends the RAG infrastructure to include three new knowledge categories sourced from Japanese official data. It operates under the same compliance constraints as `search_hpa_guidelines` — all output is filtered for medical content before being returned. The key difference is that its output is **consumed by the `east-asian-health-context-expert` Skill and the enriched L2 Skills internally**, not passed directly to family-facing report generation.

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

### Japanese Knowledge Base — Three New RAG Categories

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

Cleaning rules: Remove all clinical threshold numbers (HbA1c values, specific blood pressure readings, medication names). Retain relative risk ratios as they are not diagnostic — they are epidemiological calibration data. Remove any content that frames findings as clinical recommendations rather than population-level observations.

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

Cleaning rules: Retain prevalence data (percentages are epidemiological, not diagnostic). Remove any content that maps disability categories to specific disease diagnoses. Retain functional descriptions of disability types (cannot walk 10 meters without assistance) as these describe observable behaviors, not medical conditions.

**Category 4: `japan_community_dementia_care`** ← NEW

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

Cleaning rules: Retain descriptions of behavioral patterns and community responses. Remove any clinical staging or diagnostic criteria for dementia severity levels. Retain social engagement metrics (frequency of community contact, nature of social activities) as these are lifestyle, not clinical, data. The focus is on *what behaviors to look for* and *what community actions help* — not on disease staging or treatment.

---

## Enrichments to Three Existing L2 Skills

The following changes do not alter the core system prompt structure of the existing Skills. They add a new internal reasoning step — the Japan calibration check — that runs before the family-facing report is generated.

### Enrichment 1: `mobility-fall-expert`

**New reasoning step added between Step 2 (tool_call_search) and Step 3 (synthesize_insight):**

```
Step 2.5 — japan_calibration_check (new):
  If gait slowdown has persisted for ≥ 5 days:
    Call east-asian-health-context-expert with:
    - behavioral observation summary
    - request: threshold calibration for Taiwan elderly mobility sensitivity
    If response returns significance_adjustment: "elevated":
      Lower the reporting threshold — route to report generation even if pattern
      would not meet standard Japanese benchmark thresholds
    If protective_factor_opportunity is not null:
      Incorporate the protective behavior suggestion into hpa_suggestion field,
      framed through HPA language (not JPHC language)
```

**New reference added to `references/` directory:**
`taiwan_mobility_sensitivity_note.md` — explains that Taiwan's elderly population shows 49.82% mobility disability prevalence vs Japan's 36.07%, and that gait decline signals therefore warrant earlier attention in the Taiwanese context.

**No changes to output language.** The calibration affects when to generate a report, not what language is used. All output continues through HPA framing.

### Enrichment 2: `dementia-behavior-expert`

**New reasoning step added between Step 1 (analyze_data) and Step 2 (tool_call_search):**

```
Step 1.5 — me_byo_convergence_check (new):
  COGNITIVE DOMAIN FAST PATH (new — elevated from convergence logic):
    If input contains ANY of: wandering (night), appliance_interaction_long,
    repeated inactivity (3+ consecutive days), or day-night routine inversion:
      IMMEDIATELY call east-asian-health-context-expert with:
      - signal: "cognitive_domain_active"
      - request: cognitive signal significance assessment
      Reason: ME-BYO cognitive domain signals have lower reversibility than
      metabolic/locomotor signals. Do not wait for multi-domain convergence.
      One strong cognitive signal warrants immediate calibration.

  MULTI-DOMAIN CONVERGENCE PATH (unchanged logic, now secondary):
  Count how many of the four ME-BYO domains have active signals in this input:
    - Metabolic: activity irregularity suggesting meal timing disruption?
    - Locomotor: any gait or mobility events?
    - Cognitive: wandering, inactivity, or appliance difficulty events?
    - Mental resilience: disrupted routine suggesting social withdrawal?
  If ≥ 2 domains have signals (and cognitive domain fast path already called):
    Escalate significance level further — multi-domain convergence on top of
    cognitive signal is the highest-significance pattern in this system
```

**New social disengagement detection logic (from Omuta/Mitsugi models):**

```
Step 1.7 — social_disengagement_check (new):
  If inactivity events have appeared on 3+ consecutive days:
    Evaluate against Mitsugi model social disengagement pattern:
    Question: Was this elder previously showing regular activity timing
    that suggests community routines (morning walks, regular meal activity)?
    If yes, and that rhythm has now broken:
      This is not only a circadian signal — it is a social withdrawal signal
      Inform Step 3 synthesis: the hpa_suggestion should include a
      community re-engagement element alongside the circadian suggestion
```

**New protective factor integration (expanded from v1.0):**

When the `dementia-behavior-expert` generates a report for an elder showing daytime inactivity and potential social isolation, the Omuta/Mitsugi community care evidence now informs a richer suggestion set. All language remains HPA-toned and warm:

Example `hpa_suggestion` language incorporating the community care dimension:
"Establishing a gentle daily anchor — perhaps a short morning walk to a familiar spot, or a regular time to share tea with family or neighbors — can help restore the rhythm that makes each day feel steady. Small consistent social moments are among the most valuable things we can build into a daily routine."

This language is warm and non-clinical, but it is now grounded in two evidence layers: HPA's general wellness guidance *and* Japan's Omuta/Mitsugi evidence that structured social contact is a primary protective factor against cognitive decline progression. The JPHC protective factor evidence (tea consumption) is woven in naturally.

**Updated `references/` additions for `dementia-behavior-expert`:**
- `japan_community_care_for_dementia.md` — Summary of Dementia Supporter Caravan model, Omuta City model, and Mitsugi system findings, framed as behavioral observation guidance (not clinical content)

### Enrichment 3: `weekly-summary-composer`

**New section in weekly report structure:**

The weekly report gains a fifth element: **Healthy Active Years Framing**. This section appears only in reports where the weekly trend shows improvement or maintenance (positive reinforcement context only — never in decline contexts).

```
Weekly Report Structure (updated)
│
├── 🌟 Weekly Highlights (positive observations first)
├── 📊 Behavioral Trend Summary (sleep, mobility, cognitive)
├── 🏠 Actionable Suggestions (1-2, from HPA RAG)
├── 💬 Family Engagement Prompt (open question)
├── 🌱 Healthy Active Years Note (NEW — only on positive trend weeks)  ←
└── ⚠️ Notable Changes (if any)
```

**🌱 Healthy Active Years Note — specification:**

This element appears only in weeks where at least two of the three behavioral dimensions (sleep, mobility, cognitive routine) show stable or improving patterns. Its purpose is to provide long-term framing that builds the family's understanding of why consistency matters — not just this week, but across years.

Language direction: warm, forward-looking, grounded in the idea that consistent healthy habits compound over time. No statistics, no study citations, no medical framing.

Example:
"This week's consistency in daily activity and regular sleep patterns is exactly the kind of gentle, sustained rhythm that supports healthy active years ahead. Small, steady habits — regular walks, consistent rest, time with family — are the foundation of the wellbeing we're watching over together."

**Internal calibration note for the weekly summary (not visible to families):**

The composer now consults `east-asian-health-context-expert` once per weekly cycle with the aggregated multi-domain trend data. This consultation informs whether the Healthy Active Years Note should be included (positive trend confirmed) and whether any of the behavioral patterns across the week warrant raising to `attention_needed` level based on the ME-BYO convergence logic.

---

## Updated AGENTS.md

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
| ltc-insight-router | L1 | skills/L1-ltc-insight-router/ | Always active |
| sleep-pattern-expert | L2 | skills/L2-sleep-pattern-expert/ | sleep_issue detected |
| mobility-fall-expert | L2 | skills/L2-mobility-fall-expert/ | mobility_issue or URGENT_FALL_RISK |
| dementia-behavior-expert | L2 | skills/L2-dementia-behavior-expert/ | cognitive_issue detected |
| chronic-disease-observer | L2 | skills/L2-chronic-disease-observer/ | feeds weekly-summary-composer |
| weekly-summary-composer | L2 | skills/L2-weekly-summary-composer/ | fixed weekly cadence |
| east-asian-health-context-expert | L2 | skills/L2-east-asian-health-context/ | called by mobility/dementia/weekly skills |

## Knowledge Source Rule (Critical)
Japan-sourced data (JPHC, MHLW, comparative disability research) must NEVER appear in
family-facing output. It is internal calibration data only. All family-facing content
must be sourced from HPA via search_hpa_guidelines.

## Compliance Boundary
See: COMPLIANCE.md — unchanged from v1.0
```

---

## Updated Directory Structure

Only new additions are shown. The existing structure from `LONGTERM_CARE_EXPERT_DEV_PLAN.md` is unchanged.

```
long-term-care-expert/
│
├── AGENTS.md                              ← Updated to v1.1 (see above)
│
├── skills/
│   └── L2-east-asian-health-context/      ← NEW
│       ├── SKILL.md                       ← New Skill system prompt
│       └── references/
│           ├── me_byo_framework.md        ← ME-BYO four domains with cognitive domain priority note
│           ├── jphc_key_findings.md       ← Curated JPHC findings for calibration use
│           ├── taiwan_japan_disability_benchmarks.md ← Comparative prevalence data
│           ├── healthy_life_expectancy_framing.md    ← HJ21 "gap" concept
│           ├── dementia_supporter_caravan.md         ← NEW (v1.1): Caravan model behavioral indicators
│           ├── omuta_city_care_model.md              ← NEW (v1.1): Omuta community care design
│           └── mitsugi_social_disengagement.md       ← NEW (v1.1): Social isolation → institutionalization pathway
│
├── knowledge_base/
│   └── processed_chunks/
│       ├── jphc_lifestyle_outcomes/            ← NEW Japanese RAG category
│       ├── mhlw_hj21_nutrition_activity/       ← NEW Japanese RAG category
│       ├── taiwan_japan_disability_comparison/ ← NEW Japanese RAG category
│       └── japan_community_dementia_care/      ← NEW Japanese RAG category (v1.1)
│
└── tools/
    └── japan_clinical_data_search.py      ← NEW: search_japan_clinical_data implementation
```

---

## Extension Development Phases

This extension is built after the original system reaches Phase 2 completion (all five L2 Skills deployed, MCP server operational). It should not be developed in parallel with the original system — the foundation must be stable before the calibration layer is added.

### Extension Phase 1 — Japanese Knowledge Base Construction (Month 5)

Goal: Build the four Japanese RAG knowledge categories to the same quality standard as the HPA categories.

Tasks:
- Collect and process JPHC study summary publications (English-language versions available through NCI/NIH JPHC consortium)
- Process HJ21 third-term framework documentation (MHLW English summaries)
- Process Taiwan-Japan disability comparison research papers
- **NEW (v1.1):** Collect and process Dementia Supporter Caravan program documentation, Omuta City model outcomes, and Mitsugi Integrated Community Care System historical evidence for `japan_community_dementia_care` category
- Apply the four metadata schemas defined above to every chunk
- Build medical content filter for Japanese data (same standards as HPA filter)
- Deploy `search_japan_clinical_data` tool in the FastMCP server with four-category support
- Run 20-query validation for each category (internal calibration queries, not family-facing queries)

Acceptance criteria:
- ≥ 200 chunks across four new categories (≥ 50 per category, with ≥ 30 in `japan_community_dementia_care`)
- Medical content filter accuracy ≥ 99%
- Calibration query relevance ≥ 4/5 on 20-query sample per category
- Zero Japanese data passes through to any family-facing output path (architectural audit)

### Extension Phase 2 — East Asian Context Expert Skill and L2 Enrichments (Month 6)

Goal: Deploy the new Skill and enrich the three existing Skills with Japan calibration steps.

Tasks:
- Build `east-asian-health-context-expert` SKILL.md and all seven reference documents (including three new community care references)
- Add Step 2.5 (Japan calibration check) to `mobility-fall-expert`
- **Updated (v1.1):** Add Step 1.5 (ME-BYO cognitive fast path + multi-domain convergence) to `dementia-behavior-expert`
- **NEW (v1.1):** Add Step 1.7 (social disengagement detection using Mitsugi/Omuta models) to `dementia-behavior-expert`
- **NEW (v1.1):** Add `japan_community_care_for_dementia.md` reference to `dementia-behavior-expert`
- Add weekly calibration consultation to `weekly-summary-composer`
- Add Healthy Active Years Note logic to weekly report generation
- Test 30 calibration scenarios to verify the context expert's threshold adjustment logic, including 10 scenarios specifically for social disengagement detection
- Verify that no JPHC, MHLW, or community care model content appears in any generated LINE message (full output audit)

Acceptance criteria:
- Context expert returns structured JSON responses correctly in all 30 test scenarios
- Mobility threshold sensitivity correctly elevated for Taiwan vs Japan benchmarks
- ME-BYO convergence logic correctly identifies multi-domain signal convergence
- 100% of generated LINE messages contain zero Japan data citations
- Healthy Active Years Note appears only on positive trend weeks (verified by 4-week test set)

---

## Extension KPIs

These supplement (not replace) the original KPIs from `LONGTERM_CARE_EXPERT_DEV_PLAN.md`.

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

## The Core Design Commitment This Extension Enforces

The original system's three philosophical pillars — Slow Insights, De-medicalized Language, and Progressive Disclosure — remain completely intact. This extension adds a fourth, invisible pillar:

**Pillar 4: East Asian Epidemiological Precision**

Taiwan families deserve insights calibrated against the best available evidence for their population, not borrowed from Western studies that were built on different metabolic architectures, different dietary baselines, and different aging trajectories. Japan's 40-year head start in super-aging, its JPHC cohort's 30-year follow-up, and its documented experience with community care at scale are the most relevant evidence base available anywhere in the world for what Taiwan is entering.

This evidence never speaks directly to families. It speaks to the system's reasoning — sharpening when to pay attention, what patterns matter most, and what protective behaviors are worth gently reinforcing in the warm language that families receive.

The family reads: "Daily activity and a cup of tea are the kind of gentle habits worth keeping."  
The system knows: JPHC documented these exact behaviors as statistically protective against dementia in a biologically similar population across thirty years of follow-up.

That gap between what the family reads and what the system knows is the precise architecture this extension is designed to maintain.

---

## Revision History

| Version | Date | Summary |
|---|---|---|
| v1.0 | 2026-03-17 | Initial extension specification. Japanese MHLW/JPHC/comparative disability data as internal calibration layer. New Skill: east-asian-health-context-expert. New MCP tool: search_japan_clinical_data. Enrichments to three existing L2 Skills. Maintains full SaMD compliance boundary. |
| v1.1 | 2026-03-17 | Review against Japanese MHLW official sources document. Added Source 7 (Dementia Supporter Caravan + Omuta City model) and Source 8 (Mitsugi model — deepened treatment). Added fourth RAG category `japan_community_dementia_care`. Upgraded DOMAIN 4 ME-BYO cognitive domain to first-class fast-path status. Added Step 1.7 social disengagement detection to `dementia-behavior-expert`. Added three new reference files to context expert. Updated KPIs with cognitive fast path and social disengagement metrics. |
