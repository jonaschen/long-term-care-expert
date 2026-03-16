# Long-Term Care Expert Agent Skill Set

An AI-driven semantic bridge for privacy-first elderly home care monitoring in Taiwan.

## 🌟 Overview

`long-term-care-expert` is a hierarchical two-layer Claude Agent Skill Set designed to transform anonymized JSON behavioral events from IoT edge devices (thermal imaging and mmWave radar) into actionable, warm, and compliant caregiving insights for families.

This system is specifically engineered to adhere to Taiwan's **Non-SaMD (Software as a Medical Device)** regulations, focusing on health promotion and behavioral observation rather than clinical diagnosis.

## 🏗️ Architecture

The system operates using a two-layer agent model:

-   **Layer 1 (L1-ltc-insight-router):** A pattern recognition and traffic control agent that analyzes behavioral trends against a 14-day personal baseline.
-   **Layer 2 (L2 Domain Experts):** Five specialized agents (Sleep, Mobility, Dementia, Chronic Disease, and Weekly Summary) that synthesize behavioral data with Taiwan Health Promotion Administration (HPA) guidelines.

## 🚀 Key Features

-   **Privacy-First:** Processes only anonymized JSON event logs—no images or biometric data.
-   **Slow Insights:** Reduces alert fatigue by suppressing single anomalies in favor of multi-day trends.
-   **Compliance-Engineered:** Automated term filtering and RAG-based educational output to ensure non-medical classification.
-   **LINE Integration:** Delivers insights via LINE Messaging Flex Messages for high accessibility.

## 📂 Project Documentation

-   [LONGTERM_CARE_EXPERT_DEV_PLAN.md](./LONGTERM_CARE_EXPERT_DEV_PLAN.md) - Full technical specification and roadmap.
-   [AGENTS.md](./AGENTS.md) - Detailed agent hierarchy, roles, and routing logic.
-   [GEMINI.md](./GEMINI.md) - Core instructional context for AI development.
-   [CLAUDE.md](./CLAUDE.md) - Development guidelines and environment setup.

## 🛠️ Tech Stack (Planned)

-   **Language:** Python 3.10+
-   **Framework:** FastMCP (Model Context Protocol)
-   **AI Platform:** Anthropic Claude Agent Skill Sets
-   **Knowledge Base:** RAG-indexed Taiwan HPA guidelines
-   **Messaging:** LINE Messaging API

---
*This project is currently in the **Planning Phase**. No code has been implemented yet.*
