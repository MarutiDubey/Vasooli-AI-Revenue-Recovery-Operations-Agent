# Vasooli — AI Revenue Recovery Agent
### Full Build Plan | Razorpay AI Buildathon — Track 03: AI Revenue Recovery

---

## 1. Overview

**Track:** 03 — AI Revenue Recovery
**Project name:** Vasooli (working title)
**One-line pitch:** Vasooli detects failed recurring subscription payments, diagnoses the cause, chooses a bounded recovery intervention, verifies the actual outcome, and measures recovered revenue across a batch — with an audit trail and honest exception reporting.

**Scope (deliberately narrow):** Failed recurring subscription payment recovery on Razorpay Subscriptions, Test Mode only.

**What this project is NOT:**
- ❌ Not a replacement for Razorpay's own retry engine
- ❌ Not an AI that "retries every failed payment" on its own authority
- ❌ Not claiming a Payment Link = subscription reactivation
- ❌ Not claiming synthetic failure-reason distribution reflects real BFSI statistics
- ❌ Not processing 10,000 real Razorpay transactions (batch eval is synthetic; only ~10–20 flows are real Test Mode demos)

---

## 2. Core Architecture

```
RAZORPAY TEST MODE
        ↓
     WEBHOOK
        ↓
VERIFY SIGNATURE + DEDUP (x-razorpay-event-id)
        ↓
      DETECT
   (pending / halted / charged — state reconciled from DB,
    NOT assumed from webhook arrival order)
        ↓
     DIAGNOSE
  (normalize Razorpay signal → internal reason,
   or UNKNOWN / INSUFFICIENT_EVIDENCE if unclear)
        ↓
      DECIDE
  (feature engine → recovery score → LLM explanation
   [non-authoritative] → POLICY ENGINE [final word])
        ↓
  EXECUTE RECOVERY ACTION
   ┌─────────┬────────────────┬───────────────┬──────────┐
   MONITOR   ONE_TIME_        MANUAL_CHARGE   ESCALATE   STOP
             RECOVERY         (issued invoice +
             (Payment Link)    non-domestic card
                                only)
   └─────────┴────────────────┴───────────────┴──────────┘
        ↓
   VERIFY OUTCOME
  (payment.authorized → payment.captured → invoice.paid →
   actual subscription state — not just "action requested")
        ↓
      MEASURE
  (₹ Cash Recovered  —vs—  ₹ Subscription Revenue Reactivated,
   tracked as TWO separate numbers)
        ↓
  AUDIT TRAIL + EXCEPTION LIST
  (first-class output, not an afterthought)
```

---

## 3. Non-Negotiable Design Principles

These came out of repeated review and should not be relaxed under time pressure:

1. **Razorpay's retry engine is the source of truth for auto-retries.** Vasooli orchestrates recovery *around* it — it does not reimplement or override retry timing.
2. **UNKNOWN is a valid diagnosis.** Never force a reason when evidence is insufficient — escalate instead of guessing.
3. **The LLM never has final authority over a money action.** It may explain or score; the deterministic policy engine always makes the final call. This is a demo-critical differentiator.
4. **Cash recovered ≠ subscription recovered.** A completed Payment Link means money changed hands, not that the subscription state changed. Track both, never conflate them.
5. **No fabricated real-world statistics.** Synthetic failure-reason distributions are simulation parameters, explicitly labeled as such — never presented as real BFSI data.
6. **Webhooks are at-least-once and may arrive out of order.** State must be reconciled from the database / API, never assumed from event sequence.
7. **"Verified" means payment evidence exists**, not "action was requested." VERIFY is a real pipeline stage, not a formality.

---

## 4. The 7-Step Build Plan

| Step | Name | Core Deliverable | Tier |
|---|---|---|---|
| 1 | Setup & Foundation Proof | Working Razorpay Test Mode account, plan, subscription, and a confirmed webhook hit from a real triggered failure | MUST |
| 2 | Webhook Ingestion & State Layer | Signature-verified, deduped, order-tolerant webhook handler + DB schema | MUST |
| 3 | Synthetic Dataset Generator | 500–2,000 record generator, input/output fields separated, configurable failure distribution | MUST (core), configurability = SHOULD |
| 4 | Diagnose + Decide Engine | Failure normalizer with UNKNOWN fallback, recovery scorer, deterministic policy engine | MUST (policy engine); LLM explanation layer = NICE |
| 5 | Execute Recovery Actions | MONITOR / ONE_TIME_RECOVERY / ESCALATE / STOP wired to real Test Mode API calls | MUST; MANUAL_CHARGE = SHOULD |
| 6 | Verify + Measure + Dashboard | Payment-state verification chain, basic ₹-recovered number | MUST (basic); dual metrics + exception-list UI = SHOULD/NICE |
| 7 | Batch Evaluation + Demo Prep | Full batch run + stats, README, repo cleanup, pitch video, 12 form answers | MUST |

Each step below gets its own detailed MD plan (to be written next). This master plan is the reference all of them roll up to.

---

## 5. Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| Backend | FastAPI (Python) | |
| Database | SQLite + SQLAlchemy | No MongoDB — unnecessary complexity for this scope |
| Payment | Razorpay Test Mode API (Subscriptions + Payment Links) | Free, no card/setup required |
| LLM (optional layer) | Groq free tier (Llama) or free-trial credits | Explanation-only, never decision-making |
| Frontend | Simple React/Next.js dashboard | Recovery stats, audit trail, exception list |
| Synthetic data | Python + Faker | Configurable class distribution via flags |
| Hosting | Deferred — local-first until core loop works | Render/Vercel only if time allows |

---

## 6. Synthetic Dataset Schema

**Inputs (no leakage — these are the only fields the system "sees" going in):**
```
subscription_id
customer_id
plan_id
amount
due_date
subscription_age
customer_tenure
previous_success_count
previous_failure_count
days_since_last_success
attempt_count
failure_signal          (raw Razorpay-style signal, not pre-labeled)
subscription_state      (pending / halted / active)
customer_opt_out        (boolean)
```

**Generated by the system (outputs — never fed back in as input):**
```
diagnosed_reason         (INSUFFICIENT_FUNDS / CARD_EXPIRED / BANK_DECLINE /
                           MANDATE_CANCELLED / UNKNOWN)
recovery_score
recommended_action       (from LLM, non-binding)
policy_decision          (final — from policy engine)
execution_result
recovered_amount
exception_reason
```

**Distribution:** configurable via CLI flags (e.g. `--insufficient-funds 0.35 --expired-card 0.20 ...`), documented in the README as *simulation assumptions*, never claimed as real-world proportions.

**Scale:** 500–2,000 synthetic records for batch evaluation. 10–20 of these get run through *real* Razorpay Test Mode flows for the live demo (mind the 30 Payment Link / 30 Subscription Link test-mode caps).

---

## 7. Recovery Actions — Precise Eligibility Rules

| Action | Trigger / Eligibility | Notes |
|---|---|---|
| **MONITOR** | Razorpay's own retry cycle is still active (pending, retries remaining) and recovery likelihood is already high | No intervention — deliberately doing nothing is a valid, demonstrable AI-judgment decision |
| **ONE_TIME_RECOVERY** (Payment Link) | Any failed/pending/halted state where a one-time collection makes sense | Recovers **cash**, not automatically the subscription. Track separately. Capped at 30 test-mode links — budget these carefully across the demo |
| **MANUAL_CHARGE** | Invoice status = `issued` **AND** payment method supports manual charging (domestic cards are NOT supported for manual charge) | Keep in the architecture for completeness / AI-judgment scoring, but do not rely on this as the live demo's hero action — likely untestable with standard Indian test cards |
| **ESCALATE** | UNKNOWN diagnosis, high-value subscription above a policy threshold, or MANUAL_CHARGE ineligible | Routes to a human/merchant queue in the design (can be a log entry for hackathon scope) |
| **STOP** | `customer_opt_out = true` or mandate explicitly cancelled | Hard stop — compliance-first, never retry a customer who opted out |

---

## 8. Decide Stage — Policy Engine Logic

```
Event
  ↓
Feature Engine (subscription age, tenure, past success/failure counts...)
  ↓
Recovery Score (simple model or rule-based scoring — keep it explainable)
  ↓
LLM Explanation (optional, natural-language reasoning — NON-AUTHORITATIVE)
  ↓
POLICY ENGINE (deterministic, hardcoded guardrails — FINAL WORD)
  ↓
Action
```

**Reference example for the pitch:**
```
LLM says:      "Retry recommended, high confidence."
Policy says:    max_attempts = 3, already at 3 → no further auto-retry
Final:          STOP / ESCALATE
```
This — the policy engine overriding the LLM — is one of the strongest "AI judgment: where you chose not to use one" moments in the whole build. Make sure it's visibly demoable, not buried in logs.

---

## 9. Webhook Handling Requirements

- **Signature verification:** HMAC-SHA256 against the *raw* request body (not parsed/re-serialized JSON).
- **Deduplication:** Use `x-razorpay-event-id` header — Razorpay uses at-least-once delivery, duplicates are expected and normal.
- **Respond fast:** Return 2xx quickly; do heavy processing (diagnose/decide/execute) asynchronously — Razorpay times out slow responses and will redeliver.
- **Out-of-order tolerance:** Do not assume events arrive in the logical sequence (e.g. `charged` after `pending`). Reconcile against current DB state, not against "expected next event."
- **Card-specific retry model:** T+1/T+2/T+3 auto-retry applies to the *card* retry model specifically — do not generalize this timing to every payment method (eMandate/UPI have separate documented models).

---

## 10. Verify & Measure

**VERIFY chain (don't skip steps):**
```
Action requested → Action accepted by Razorpay → payment created →
payment.authorized → payment.captured → invoice.paid → subscription state re-checked
```
Only after this chain completes does a record count as recovered.

**MEASURE — report as two distinct numbers, always:**
- ₹ **Cash Recovered** (any successful collection, one-time or recurring)
- ₹ **Subscription Revenue Reactivated** (subscription state actually returned to active)

**Exception list — first-class output, not a debug log:**
```
sub_id | amount | diagnosed_reason | action_attempted | why_it_stopped | recovered?
```
This is what makes the batch result trustworthy to judges — show it prominently in the dashboard/pitch.

---

## 11. Known Constraints (documented, not hidden)

| Constraint | Detail | Mitigation |
|---|---|---|
| 30 Payment Links / business in test mode | Hard API limit | Budget real demo flows carefully (10–20), do the rest via synthetic batch |
| 30 Subscription Links / business in test mode | Same as above | Same |
| Manual charge unsupported for domestic cards | Confirmed in Razorpay docs | Keep the code path, don't depend on it for the live demo |
| Webhooks may arrive out of order | Confirmed in Razorpay docs | State-reconciliation design, not sequence-dependent logic |
| Retry timing is card-specific (T+1/T+2/T+3) | Other methods differ | Say "Razorpay-managed retry lifecycle," not a blanket claim |

These constraints, if mentioned in the pitch or the "what broke, how you got out" answer, work in your favor — they show you actually read the docs rather than assuming.

---

## 12. Timeline (approx. 60 hours available)

- **Steps 1–2 (Hours 0–15):** Razorpay foundation + webhook layer proven end-to-end before anything else is built.
- **Step 3 (Hours 10–18, overlaps with 1–2):** Synthetic data generator — no dependency on Razorpay side, build in parallel.
- **Steps 4–5 (Hours 15–35):** Diagnose/Decide/Execute — the core intelligence and the strongest "AI judgment" material.
- **Step 6 (Hours 35–45):** Verify/Measure/Dashboard — at minimum, one honest recovered-₹ number; dual metrics and exception UI if time allows.
- **Step 7 (Hours 45–60):** Batch run, README, GitHub cleanup, pitch video, form answers. Do not compress this — a half-finished submission scores worse than a smaller, fully-packaged one.

---

## 13. Application Form — Prep Checklist

| Field | Status |
|---|---|
| Full name, college, graduation year | Ready |
| In-person from September / 6 vs 12 months | Decide before submission |
| Resume | Have ready, not the focus |
| Track | AI Revenue Recovery |
| Project name | Vasooli (or finalize alternative) |
| What it solves | 1–2 lines, draw from Section 1 pitch |
| GitHub repo (public) | Clean README, no leaked keys |
| 5-min pitch video (unlisted) | Script first, then record — 2–3 takes expected |
| **What broke, how you got out** | Log real issues *as they happen* — the manual-charge domestic-card limitation and the out-of-order webhook handling are strong, genuine candidates |

---

## Next

Each of the 7 steps above gets a dedicated, detailed MD plan (setup commands, file structure, exact API calls, code-level checklist). Start with Step 1.
