# GEMINI.md - Long-Term Care Expert Agent Skill Set

This project is an **active development repository** for `long-term-care-expert`, a hierarchical two-layer AI Agent system designed for elderly home care monitoring in Taiwan.

## 🌟 Project Overview

The system serves as a semantic bridge between privacy-first IoT sensor data (thermal/mmWave radar) and actionable, warm caregiving language for families. It transforms cold JSON behavioral logs into meaningful insights while strictly adhering to Taiwan's non-SaMD (Software as a Medical Device) regulations.

- **Primary User:** Family caregivers in Taiwan.
- **Input:** Anonymized JSON behavioral events (e.g., bed exits, gait speed, inactivity).
- **Output:** Structured insights delivered via LINE Messaging Flex Messages.
- **Core Philosophy:** "Slow Insights, Not Real-Time Alerts" — focusing on multi-day trends to avoid alert fatigue.

## 🏗️ System Architecture (v1.1)

The system follows a two-pillar knowledge architecture, integrating Taiwan HPA health education with Japanese MHLW/JPHC epidemiological calibration.

### Layer 1: `ltc-insight-router`
- **Role:** Pattern recognition, trend classification, and traffic control.
- **Urgency:** `posture_change: sudden_drop` (potential fall) bypasses trend checks for immediate routing.

### Layer 2: Domain Experts (6 Skills)
Each expert handles a specific domain and follows a strict **RAG -> Synthesize -> Report** sequence.
1.  **`sleep-pattern-expert`**: Nighttime behavior and sleep environment.
2.  **`mobility-fall-expert`**: Movement patterns, gait, and fall risk.
3.  **`dementia-behavior-expert`**: Cognitive patterns (wandering, inactivity, appliance usage).
4.  **`chronic-disease-observer`**: Long-term activity trends and lifestyle regularity.
5.  **`weekly-summary-composer`**: Cross-domain integration for weekly reports.
6.  **`east-asian-health-context-expert`**: Internal reasoning layer for East Asian-specific calibration.

## 🛠️ Technology Stack

- **AI Engine:** Claude Agent Skill Sets (Anthropic).
- **Protocol:** MCP (Model Context Protocol) for tool integration.
- **Server:** Python-based **FastMCP** server.
- **Knowledge Base:** 
  - **Pillar 1:** Taiwan HPA guidelines (Family-facing suggestions).
  - **Pillar 2:** Japanese MHLW/JPHC data (Internal reasoning calibration).
- **Delivery:** LINE Official Account (Flex Messages).

## ⚖️ Compliance & Constraints (Non-SaMD)

**CRITICAL:** This system must NOT be classified as a Medical Device. All generated language must be observational and educational, never clinical or diagnostic.

- **Prohibited Terms:** `diagnose`, `treatment`, `disorder`, `disease`, `prescription`, `symptoms`, `Alzheimer's`, `Parkinson's`.
- **Required Language:** "we observed...", "compared to the usual pattern...", "behavioral pattern change".
- **Tool Protocol:** Every L2 expert must call `search_hpa_guidelines` with `exclude_medical: true`.

## 📂 Project Status

- **[COMPLETED] Phase 1: Knowledge Base and Infrastructure**
  - HPA source documents processed into clean Markdown chunks in `knowledge_base/processed_chunks/`.
  - PDF processing scripts implemented in `scripts/`.
  - Directory structure and core planning documents (v1.1) established.
- **[IN PROGRESS] Phase 2: Core Skill Development**
  - SKILL.md prompts for L1/L2 agents are currently being drafted.
  - MCP tool implementations (FastMCP) are in the planning stage.

## 🚀 Getting Started

- **Requirement:** Python 3.10+, FastMCP, Anthropic API Key.
- **Key Specifications:**
  - `LONGTERM_CARE_EXPERT_DEV_PLAN.md` (Core Architecture)
  - `LONG_TERM_CARE_EXT_PLAN.md` (Japan Calibration Extension)
  - `ROADMAP.md` (Phases & Acceptance Criteria)
  - `AGENTS.md` (Routing Manifest)

---
*For detailed Claude-specific instructions, see `CLAUDE.md`.*
