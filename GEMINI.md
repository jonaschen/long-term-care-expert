# GEMINI.md - Long-Term Care Expert Agent Skill Set

This project is a **planning-phase architectural specification** for `long-term-care-expert`, a hierarchical two-layer AI Agent system designed for elderly home care monitoring in Taiwan.

## 🌟 Project Overview

The system serves as a semantic bridge between privacy-first IoT sensor data (thermal/mmWave radar) and actionable, warm caregiving language for families. It transforms cold JSON behavioral logs into meaningful insights while strictly adhering to Taiwan's non-SaMD (Software as a Medical Device) regulations.

- **Primary User:** Family caregivers in Taiwan.
- **Input:** Anonymized JSON behavioral events (e.g., bed exits, gait speed, inactivity).
- **Output:** Structured insights delivered via LINE Messaging Flex Messages.
- **Core Philosophy:** "Slow Insights, Not Real-Time Alerts" — focusing on multi-day trends to avoid alert fatigue.

## 🏗️ System Architecture

The system follows a hierarchical two-layer "Skill Set" architecture:

### Layer 1: `ltc-insight-router`
- **Role:** Pattern recognition, trend classification, and traffic control.
- **Logic:** Compares 24-72 hours of data against a personal 14-day baseline.
- **Suppression:** Suppresses isolated events and duplicate alerts (48h window) to ensure high-signal reporting.
- **Urgency:** Only `posture_change: sudden_drop` (potential fall) bypasses trend checks for immediate routing.

### Layer 2: Domain Experts (5 Skills)
Each expert handles a specific behavioral domain and follows a strict **RAG -> Synthesize -> Report** tool sequence.
1.  **`sleep-pattern-expert`**: Nighttime behavior and sleep environment.
2.  **`mobility-fall-expert`**: Movement patterns, gait, and fall risk.
3.  **`dementia-behavior-expert`**: Cognitive patterns (wandering, inactivity, appliance usage).
4.  **`chronic-disease-observer`**: Long-term activity trends and lifestyle regularity.
5.  **`weekly-summary-composer`**: Cross-domain integration for weekly reports.

## 🛠️ Technology Stack (Planned)

- **AI Engine:** Claude Agent Skill Sets (Anthropic).
- **Protocol:** MCP (Model Context Protocol) for tool integration.
- **Server:** Python-based **FastMCP** server.
- **Knowledge Base:** Taiwan Health Promotion Administration (HPA) guidelines (RAG).
- **Delivery:** LINE Official Account (Flex Messages).

## ⚖️ Compliance & Constraints (Non-SaMD)

**CRITICAL:** This system must NOT be classified as a Medical Device. All generated language must be observational and educational, never clinical or diagnostic.

- **Prohibited Terms:** `diagnose`, `treatment`, `disorder`, `disease`, `prescription`, `symptoms`, `Alzheimer's`, `Parkinson's`.
- **Required Language:** "we observed...", "compared to the usual pattern...", "behavioral pattern change", "you might consider...".
- **Tool Protocol:** Every L2 expert must call `search_hpa_guidelines` with `exclude_medical: true`.

## 📂 Directory Structure (Planned)

```text
long-term-care-expert/
├── skills/              # Agent Skill prompts (SKILL.md)
├── tools/               # MCP Server and Python tool implementations
├── knowledge_base/      # HPA documents and vector index
├── compliance/          # Term blacklists and adversarial test cases
└── tests/               # Routing accuracy and compliance validation
```

## 🚀 Getting Started (Future)

*Note: The project is currently in the planning phase. No code has been implemented yet.*

- **Requirement:** Python 3.10+, FastMCP, Anthropic API Key.
- **Main Entry Point:** `python tools/mcp_server.py`.
- **Primary Spec:** Refer to `LONGTERM_CARE_EXPERT_DEV_PLAN.md` for full implementation details.

---
*For detailed Claude-specific instructions, see `CLAUDE.md`.*
