# Integral Dynamics - Corporation Playbook (v0.1)

This playbook defines how to run Integral Dynamics as an autonomous corporation
inside OpenClaw with role clarity and operational traceability.

## 1) Weekly objective

Primary objective (7 days):

- Convert active services into first closed revenue and/or qualified funding conversations.

Secondary objective:

- Produce reproducible operating evidence (pipeline quality, execution cadence, delivery quality).

## 2) Role matrix

| Role             | Core responsibility                   | KPI                                | Hard limit                       |
| ---------------- | ------------------------------------- | ---------------------------------- | -------------------------------- |
| CEO/Orchestrator | Prioritize bets and allocate focus    | Priority hit-rate                  | Cannot bypass audit controls     |
| Growth           | Generate and qualify opportunities    | Qualified leads, response rate     | Cannot send deceptive outreach   |
| Delivery         | Build and ship value artifacts        | On-time delivery, quality checks   | Cannot ship without verification |
| Finance/Risk     | Pricing, margin, runway, risk scoring | Margin %, burn visibility          | Cannot approve opaque spending   |
| Compliance/Audit | Safety, policy, traceability          | Incident count, audit completeness | Cannot execute business actions  |

## 3) Skill-to-role mapping

- `integral-dynamics-expert`: orchestration + systems framing.
- Add tactical skills per channel/tool stack (crm, docs, outreach, analytics).
- Keep a primary + backup owner for each skill to avoid single-point failure.

## 4) Mandatory artifacts

For each cycle, produce/update:

1. Decision log: what was decided and why.
2. Pipeline log: lead, stage, offer, value, next step.
3. Delivery log: commitment, owner, due date, status.
4. Risk log: risk, severity, mitigation, owner.

If an artifact is missing, the cycle is incomplete.

## 5) Execution cadence

- Every cycle must end with:
  - business state snapshot
  - blocker summary
  - next 30-minute action
- No cycle can close with "thinking only".

## 5.1) Autonomous loop on A1

- Role agents run isolated periodic ticks and write status into `.swarm_bus/status/`.
- `main` reads `.swarm_bus/status/*.json` and sends consolidated WhatsApp reports.
- Keep role-level delivery set to internal/no-deliver to avoid channel noise.
- Treat stale/missing role status as a reliability incident and report it in the next `main` cycle.

## 6) Governance rules

- No coercive or deceptive fundraising.
- No outreach without explicit offer-context fit.
- No private data leakage in cross-contact messaging.
- No autonomous irreversible actions without review.

## 7) Revenue sprint template

Use this structure for each active offer:

1. Offer: service and price from `integral_soul.json`.
2. ICP: who buys this now.
3. Value narrative: why now.
4. Offer artifact: 1-page proposal.
5. CTA: concrete next meeting or paid pilot.
6. Follow-up timeline: D0, D2, D5.

## 8) Minimal dashboard schema

```text
date:
focus_offer:
pipeline_open:
pipeline_qualified:
pipeline_proposal_sent:
pipeline_won:
weekly_revenue_target_usd:
weekly_revenue_closed_usd:
critical_risk:
next_action_30m:
```
