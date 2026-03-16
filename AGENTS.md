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
