# AGENTS.md - Agent Hierarchy & Routing Logic

This document defines the roles, responsibilities, and communication protocols for the hierarchical agent system within the `long-term-care-expert` skill set.

## 📐 Hierarchical Structure

The system is organized into two distinct layers to separate data processing logic from domain-specific health education.

### Layer 1: The Insight Router (`ltc-insight-router`)

**Role:** The system's "Brain" and "Traffic Controller."
- **Input:** 24-72 hour JSON behavioral log arrays and a 14-day personal baseline.
- **Responsibility:**
    - Perform baseline comparison for all incoming events.
    - Execute **Alert Suppression Logic** (48h window) to prevent alert fatigue.
    - Identify multi-day trends (except for urgent fall risks).
    - Route validated trends to the appropriate L2 Expert(s).
- **Constraint:** Does not possess health knowledge and never communicates directly with families.

### Layer 2: Domain Experts

**Role:** The system's "Voice" and "Educator."
- **Common Workflow:** RAG Search (HPA Guidelines) → Synthesis (Data + Guide) → LINE Report.
- **Constraint:** Must strictly follow Non-SaMD language patterns (observational, not diagnostic).

| Agent ID | Domain | Trigger Examples |
| :--- | :--- | :--- |
| `sleep-pattern-expert` | Sleep/Nighttime | Bed exits ≥ 2, Tossing/turning > 30m |
| `mobility-fall-expert` | Movement/Safety | Gait slowdown ≥ 30%, **Sudden drop (Urgent)** |
| `dementia-behavior-expert` | Cognitive/Wandering | Nighttime wandering, Daytime inactivity |
| `chronic-disease-observer` | Routine/Lifestyle | Activity trend shifts, appliance usage changes |
| `weekly-summary-composer` | Cross-domain | Periodic 7-day behavioral synthesis |

## 🚦 Routing & Escalation Logic

### 1. Baseline Period
- **14-Day Silent Period:** New devices are monitored without reporting to establish a personal "Normal" baseline.

### 2. Trend Detection (L1)
- **Isolated Events:** Suppressed and logged in hindsight notes.
- **Trend Confirmed:** Anomaly recurs 2+ times within a 72-hour window.
- **Urgent Bypass:** `posture_change: sudden_drop` (Potential Fall) triggers **immediate** L2 routing, bypassing all trend and suppression checks.

### 3. Alert Suppression
L1 calls `check_alert_history` before routing:
- If a similar report was sent in the last 48 hours AND severity is stable → **Suppress**.
- If severity has significantly worsened → **Route**.

## 💬 Communication Protocol

### Output Formatting
All L2 agents must deliver output via the `generate_line_report` tool, which:
1. Formats the data into a LINE Flex Message.
2. Auto-injects the mandatory legal disclaimer.
3. Ensures all language adheres to the de-medicalized whitelist.

### Progressive Disclosure
1. **Push:** Initial report provides one high-signal observation and one actionable suggestion.
2. **Pull:** If the family replies, the agent retrieves deeper HPA guidance for the conversation.
