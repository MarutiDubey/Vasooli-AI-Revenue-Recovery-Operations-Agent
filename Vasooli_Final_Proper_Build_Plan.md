# Vasooli — Final Master Build Plan
## AI Revenue Recovery Operations Agent — Revenue Recovery Orchestrator
### Razorpay AI Buildathon 2025 · Track 03: AI Revenue Recovery

---

> **Document Status:** LOCKED
> **Version:** 3.0 — Final
> **Decision:** Build. No more research.

---

## 0. One-Line Pitch

> **Vasooli turns failed recurring payments into managed recovery cases — it synthesizes context, plans the next bounded action, understands customer commitments from unstructured text, enforces merchant guardrails, executes supported Razorpay workflows, verifies what actually recovered, and measures every rupee honestly.**

---

## 1. What Problem Are We Solving?

A failed payment triggers Razorpay native retry machinery. But after retries exhaust, the merchant is left with a **portfolio of revenue stuck in limbo:**

```
1,000 failed subscriptions
Rs 10,00,000 revenue at risk

Questions the merchant cannot answer:
  -> Which 300 cases need urgent manual action?
  -> Which 400 are likely to self-recover?
  -> Which 200 customers have already promised to pay?
  -> Which 100 should be written off?
```

**Razorpay solves the payment execution layer.**
**Vasooli solves the recovery operations layer that comes after.**

---

## 2. What Razorpay Already Does (Never Duplicate These)

| Capability | Status |
|---|---|
| Automatic retry on failed subscriptions | YES — documented retry lifecycle |
| Customer failure notifications | YES — email/SMS on failure |
| Card-update / payment-method recovery | YES — hosted page flow |
| Payment Links with automated reminders | YES — SMS/email reminders |
| Subscription lifecycle (pending to halted) | YES — webhook events |
| Agent Studio with targeted recovery nudges | YES — launched March 2026 |
| Subscription Recovery Agent (voice, Hindi/English) | YES — ElevenLabs + Claude powered |

**Vasooli is NOT any of the above. We are the decision and orchestration layer above Razorpay infrastructure.**

---

## 3. Our Positioning (What Judges Must Hear)

> **"Razorpay manages the payment lifecycle. Vasooli manages the recovery-case lifecycle around it."**

We acknowledge Razorpay Agent Studio publicly in our pitch. This demonstrates deep research on the host — a strong signal to judges.

**What we are NOT building:**
- NOT another retry engine
- NOT a generic Payment Link / reminder bot
- NOT a personalized messaging system
- NOT an LLM with authority to move money
- NOT a causal / uplift-modeling system
- NOT a research ML project

---

## 4. The Core Product: Recovery Case Lifecycle

The **Recovery Case** is our primary unit of work. Every failed payment becomes a managed case.

### 4.1 Case States

```
AT_RISK
  |
ANALYZING          <- AI synthesizes context
  |
PLAN_READY         <- Structured recommendation produced
  |
POLICY_CHECK       <- Policy engine validates / overrides
  |
ACTION_APPROVED
  |
ACTION_EXECUTED    <- Razorpay API called (if applicable)
  |
WAITING_FOR_OUTCOME
  |
[RECOVERED] or [ESCALATED] or [STOPPED]
```

### 4.2 Promise-to-Pay Sub-Flow

```
Customer says: "Friday ko kar dunga"
  |
AI extracts -> intent: PROMISE_TO_PAY, date: Friday
  |
Case moves -> PROMISE_PENDING
  |
Friday arrives -> Scheduler checks Razorpay for payment
  |-- Payment found -> RECOVERED
  |-- No payment -> AI REASSESSES -> next bounded action or ESCALATE
```

### 4.3 The Control Tower View (Dashboard Kanban)

```
CONTROL TOWER — Rs 10,00,000 Revenue at Risk

HIGH PRIORITY
  Rs 45,000  Customer A  — Payment method issue
             Recommended: PAYMENT_METHOD_RECOVERY
  Rs 32,000  Customer B  — Repeated failures
             Recommended: ESCALATE

PROMISE PENDING
  Rs 18,000  Customer C  — Promised: 23 Aug
             Monitoring for payment

MONITORING (Self-Recovery Likely)
  Rs 800     Customer D  — First-time failure
             Razorpay retry in progress

STOPPED
  Rs 2,000   Customer E  — Opted out
             Hard stop — no further action
```

---

## 5. AI Architecture

### 5.1 The AI Recovery Analyst

**Job 1: Multi-Signal Case Diagnosis**

Input to LLM:
```
amount_at_risk
subscription_state (pending / halted)
failure_reason
customer_tenure_days
payment_history (success_count, failure_count)
previous_recovery_attempts
days_overdue
merchant_policy_summary
```

Structured JSON output (schema-validated before use):
```json
{
  "diagnosis": "PAYMENT_METHOD_ISSUE",
  "priority": "HIGH",
  "recommended_action": "ESCALATE",
  "follow_up_hours": 48,
  "stop_conditions": ["CUSTOMER_OPTOUT", "MAX_ATTEMPTS_REACHED"],
  "reason": "Three consecutive failures with different card errors suggests persistent payment-method issue.",
  "confidence": 0.88
}
```

**Job 2: Unstructured Customer Text to Structured State (The Demo Hero)**

| Customer Message | AI Extracts |
|---|---|
| "Friday ko payment kar dunga" | intent: PROMISE_TO_PAY, date: next_friday |
| "Kal salary aa jayegi, tab karta hoon" | intent: PROMISE_TO_PAY, date: tomorrow |
| "Card change karna hai mujhe" | intent: PAYMENT_METHOD_UPDATE_NEEDED |
| "Abhi mat contact karo please" | intent: DEFER_CONTACT |
| "Cancel kar do subscription" | intent: OPT_OUT -> triggers hard STOP |
| "Salary aate hi karunga" | intent: PROMISE_TO_PAY, date: uncertain |

**Job 3: Reassessment When New Evidence Arrives**

When a promise is missed, AI re-examines all signals and recommends a new action — does not blindly re-send a reminder.

### 5.2 LLM Authority Boundaries

| LLM CAN | LLM CANNOT |
|---|---|
| Synthesize multi-signal context | Directly call Razorpay APIs |
| Diagnose failure reason | Set opt-out status |
| Recommend next action | Calculate or modify amounts |
| Extract intent from customer text | Create duplicate actions |
| Explain its reasoning | Bypass the policy engine |
| Reassess a case | Override a STOP decision |

> **If the LLM fails, times out, or returns invalid output -> system falls back to deterministic ESCALATE. The agent never stalls.**

---

## 6. Policy Engine (The Financial Guardrail)

Policy is the final authority. The LLM is advisory only.

```
Priority Order (checked top-to-bottom):

1. customer_opt_out == true          -> HARD STOP (no override)
2. mandate_cancelled == true         -> HARD STOP
3. already_recovered == true         -> NO_ACTION
4. subscription_state == CANCELLED   -> STOP
5. attempt_count >= max_attempts     -> STOP
6. amount > escalation_threshold     -> ESCALATE
7. unsupported_action_requested      -> ESCALATE
8. invalid_diagnosis                 -> ESCALATE
9. stale_decision (> 24h old)        -> REASSESS
10. otherwise                        -> allow AI recommendation
```

**Demo-Critical Example:**

```
AI recommends:  PERSONALIZED_OUTREACH
Policy checks:  customer_opt_out = true
Policy verdict: REJECTED
Final action:   STOP

Audit log entry:
  ai_recommendation: PERSONALIZED_OUTREACH
  policy_override:   STOP
  override_reason:   customer_opt_out_flag
  timestamp:         2025-08-23T14:32:11Z
```

This single demo moment proves: AI judgment present + financial guardrails authoritative.

---

## 7. Action Set

### Core Actions (P0 — Must Build)

| Action | When Used | Razorpay Interaction |
|---|---|---|
| MONITOR | Self-recovery likely, native retry in progress | None — intentional inaction |
| ESCALATE | High-value, uncertain, or complex case | Flag for merchant review |
| STOP | Opt-out / mandate cancelled / max attempts | Record and close case |
| NO_ACTION | Already recovered | No-op |

### Extended Actions (P1 — Build After P0 Works)

| Action | When Used | Razorpay Interaction |
|---|---|---|
| PAYMENT_METHOD_RECOVERY | Card/UPI issue diagnosed | Razorpay hosted card-update page |
| ONE_TIME_RECOVERY | Subscription halted, one-off payment needed | Create Payment Link -> verify payment_link.paid |
| PROMISE_TO_PAY | Customer commits to a date | Record promise, schedule verification |

### Semantic Rules (Non-Negotiable)

- MONITOR = intentional active decision, not silence
- STOP = hard stop, irreversible without merchant override
- ESCALATE = workflow outcome, not revenue recovered
- Payment Link created != recovery. Payment Link paid + verified = Cash Recovered
- Cash Recovered != Subscription Reactivated (two separate metrics, always separate)

---

## 8. Razorpay Integration (Test Mode Only)

### 8.1 Verified Capabilities We Will Use

```
Test API Keys (rzp_test_*)
Create Plan -> POST /v1/plans
Create Subscription -> POST /v1/subscriptions
Webhook: subscription.charged
Webhook: subscription.pending
Webhook: subscription.halted
Webhook: subscription.activated
Webhook: payment_link.paid
Simulate failure -> Test Mode charge simulation
Create Payment Link -> POST /v1/payment_links
Fetch Subscription state -> GET /v1/subscriptions/:id
```

Sources:
- https://razorpay.com/docs/payments/subscriptions/test/
- https://razorpay.com/docs/webhooks/subscriptions/
- https://razorpay.com/docs/payments/payment-links/

### 8.2 Webhook Layer (Non-Negotiable Requirements)

```
Every webhook must:
  -> Verify X-Razorpay-Signature (HMAC-SHA256 on raw body)
  -> Deduplicate by x-razorpay-event-id
  -> Return 200 within 5 seconds (process async)
  -> Be out-of-order tolerant (reconcile from provider state, not sequence)
  -> Never use parsed JSON body for HMAC — use raw bytes
```

Source: https://razorpay.com/docs/webhooks/validate-test/

---

## 9. Data Model

### customers
```sql
id               INTEGER PRIMARY KEY
external_id      TEXT UNIQUE          -- Razorpay customer ID
name             TEXT
email            TEXT
contact          TEXT
tenure_days      INTEGER
opt_out          BOOLEAN DEFAULT FALSE
created_at       DATETIME
updated_at       DATETIME
```

### subscriptions
```sql
id               INTEGER PRIMARY KEY
external_id      TEXT UNIQUE          -- Razorpay subscription ID
customer_id      INTEGER FK
plan_id          TEXT
amount           INTEGER              -- in paise, never float
currency         TEXT DEFAULT 'INR'
state            TEXT                 -- pending | halted | active | cancelled
created_at       DATETIME
updated_at       DATETIME
```

### webhook_events
```sql
id               INTEGER PRIMARY KEY
event_id         TEXT UNIQUE          -- for deduplication
event_type       TEXT
subscription_id  TEXT
payment_id       TEXT
payload_hash     TEXT
received_at      DATETIME
processed_at     DATETIME
```

### recovery_cases
```sql
id                     INTEGER PRIMARY KEY
subscription_id        INTEGER FK
customer_id            INTEGER FK
amount_at_risk         INTEGER              -- in paise
status                 TEXT                 -- AT_RISK | ANALYZING | PLAN_READY | ... | RECOVERED | STOPPED
priority               TEXT                 -- HIGH | MEDIUM | LOW
diagnosis              TEXT
ai_recommendation      TEXT                 -- JSON blob
policy_decision        TEXT
policy_override_reason TEXT
created_at             DATETIME
updated_at             DATETIME
```

### recovery_actions
```sql
id                   INTEGER PRIMARY KEY
case_id              INTEGER FK
action_type          TEXT
status               TEXT                 -- PENDING | EXECUTED | FAILED | CANCELLED
razorpay_resource_id TEXT
ai_recommended       BOOLEAN
policy_approved      BOOLEAN
reason               TEXT
requested_at         DATETIME
executed_at          DATETIME
```

### promises
```sql
id               INTEGER PRIMARY KEY
case_id          INTEGER FK
promised_amount  INTEGER
promised_date    DATE
source_text      TEXT                 -- original customer message
ai_confidence    REAL
status           TEXT                 -- PENDING | KEPT | BROKEN | EXPIRED
created_at       DATETIME
checked_at       DATETIME
```

### recovery_outcomes
```sql
id                       INTEGER PRIMARY KEY
case_id                  INTEGER FK
action_id                INTEGER FK
cash_recovered           BOOLEAN
cash_amount              INTEGER
subscription_reactivated BOOLEAN
razorpay_payment_id      TEXT
razorpay_invoice_id      TEXT
exception_reason         TEXT
verified_at              DATETIME
```

---

## 10. Synthetic Dataset

### Purpose
Simulate a merchant portfolio of 500-2,000 failed subscription cases for batch evaluation.

### Distribution

| Scenario | Approximate Share |
|---|---|
| One-time transient failure | 30% |
| Repeated failure, same card | 20% |
| Payment method change needed | 15% |
| Customer promise-to-pay | 10% |
| Missed promise | 8% |
| Customer opt-out / cancel | 7% |
| High-value uncertain case | 5% |
| Already recovered (test dedup) | 5% |

### Rules
- Fixed random seed for reproducibility
- Input features and output labels are separate columns — no leakage
- State clearly: "This is synthetic simulation data, not real BFSI statistics"
- Do NOT claim synthetic recovery rates represent real-world rates

---

## 11. Evaluation Strategy

### What We Measure (Honest, No Causal Claims)

```
Total cases ingested:         N
Cases analyzed by AI:         N1
Cases STOPPED (opt-out etc):  N2
Cases ESCALATED:              N3
Cases with action executed:   N4
Cases RECOVERED:              N5

Cash Recovered (verified):    Rs X
Subscription Reactivated:     Rs Y   (separate metric)
Promises tracked:             N6
Promises kept:                N7
Promises broken -> reassessed:N8

Policy overrides of AI:       N9   (proves guardrails work)
LLM fallback activations:     N10  (proves resilience)
```

### Optional Baseline Comparison

```
Baseline:  fixed-rule workflow (if failed -> send payment link -> wait -> close)
Vasooli:   AI-driven case orchestration

Compare:
  Recovery rate
  Time-to-resolution
  Unnecessary interventions
  Escalation rate
  Exception rate
```

> WARNING: Do NOT call this "causal incremental revenue" without a valid randomized holdout group. Without a control group, we report operational metrics only — which is completely sufficient and honest.

---

## 12. Tech Stack

| Layer | Technology | Reason |
|---|---|---|
| Backend | FastAPI (Python) | Fast, async, type-safe, great for webhooks |
| Database | SQLite + SQLAlchemy | Zero-infrastructure, hackathon-appropriate |
| AI / LLM | Groq (Llama 3) free tier via OmniRoute | Fast inference, structured output, free |
| Scheduler | APScheduler (in-process) | Promise deadline checks, no Redis needed |
| Dashboard | React + simple REST API | Kanban-style Control Tower view |
| Razorpay | Test Mode API + Webhooks | All integration, zero real money |
| Secrets | .env file, never committed | Basic security hygiene |
| Amount handling | Integer paise only, never float | Correct financial arithmetic |

---

## 13. 7-Step Execution Plan

### Step 1 — Razorpay Foundation Proof
**Goal:** Prove the Razorpay Test Mode pipeline works end-to-end before writing any AI code.

Tasks:
- Create Razorpay Test account -> get rzp_test_* keys
- Create Plan via API (monthly, Rs 999)
- Create Subscription -> simulate first charge
- Trigger simulated failure in Test Mode
- Receive subscription.pending webhook
- Verify X-Razorpay-Signature
- Store raw event in webhook_events table

**Hard Gate:** A real test-failure webhook arrives, signature is verified, event is stored.
**Do not proceed to Step 2 until this gate passes.**

---

### Step 2 — Webhook Ingestion and State Layer
**Goal:** Secure, durable, production-quality event handling.

Tasks:
- Raw-body HMAC verification (not parsed JSON)
- Event-ID deduplication (reject duplicates with 200)
- Async processing (return 200 < 1s, process in background)
- Out-of-order reconciliation (query Razorpay state, do not trust event order)
- Customer + Subscription records created/updated from webhook

**Hard Gate:** Send same webhook twice -> only one record created. Send out-of-order events -> state is correct.

---

### Step 3 — Recovery Case and Synthetic Dataset
**Goal:** Build case management layer and create evaluation data.

Tasks:
- webhook event -> RecoveryCase creation (status: AT_RISK)
- Case schema complete (all columns from Section 9)
- Synthetic dataset generator script (seed-fixed, 500+ cases)
- Cover all 8 scenario types from Section 10
- Verify no input/output leakage in synthetic data

**Hard Gate:** Generator runs twice with same seed -> identical output. Schema validates.

---

### Step 4 — AI Recovery Analyst
**Goal:** Meaningful, structured AI reasoning with hard failure recovery.

Tasks:
- Context builder -> assembles all case signals into LLM prompt
- Structured JSON output with Pydantic schema validation
- Diagnosis classifier (PAYMENT_METHOD_ISSUE, TRANSIENT_FAILURE, UNKNOWN, etc.)
- Priority assignment (HIGH / MEDIUM / LOW)
- Action recommendation + follow-up timing + stop conditions
- Customer-text NLP: extract intent + promise date from free-form messages
- LLM timeout / invalid-output -> auto-fallback to ESCALATE
- AI never calls Razorpay APIs directly

**Hard Gate:** Pass invalid LLM response -> system escalates gracefully. Customer says "cancel karo" -> OPT_OUT extracted -> case goes to STOP.

---

### Step 5 — Policy Engine and Action Executor
**Goal:** Turn AI recommendations into bounded, idempotent Razorpay actions.

Tasks:
- Full policy rule chain (10 rules from Section 6)
- Policy override audit log (ai_said X, policy_said Y, reason Z)
- MONITOR action (no Razorpay call, intentional inaction)
- ESCALATE action (flag + notify, no money movement)
- STOP action (hard close, no further actions allowed)
- ONE_TIME_RECOVERY (Payment Link creation — idempotent, check existing before create)
- Promise-to-Pay recording + scheduler setup
- Idempotency: check recovery_actions before executing any Razorpay call

**Hard Gate:** Full loop: webhook -> case -> AI -> policy -> action -> Razorpay API -> success. Run same case twice -> only one Payment Link created.

---

### Step 6 — Verify, Measure, and Dashboard
**Goal:** Prove what actually recovered. Build the Control Tower UI.

Tasks:
- payment_link.paid webhook handler -> verify amount -> mark RECOVERED
- Cash Recovered and Subscription Reactivated tracked as separate columns
- Batch metrics report (all counts from Section 11)
- Exception report (ESCALATED / unresolved cases with reasons)
- Promise deadline checker (scheduler: check Razorpay state on promise date)
- React dashboard: Control Tower Kanban (AT_RISK | PROMISE | MONITORING | RECOVERED | STOPPED)
- Case detail view: full AI -> Policy -> Action -> Outcome audit trail
- Metrics panel: Rs at risk | Rs cash recovered | Rs subscription reactivated | exceptions

**Hard Gate:** Creating a Payment Link is NOT counted as recovery. Only payment_link.paid verification triggers recovery count.

---

### Step 7 — Batch Evaluation, Demo, and Submission
**Goal:** Turn working product into a winning submission.

Tasks:
- Run full batch on 500+ synthetic cases -> produce metrics report
- Record one genuine "What Broke" moment + fix in demo
- 5-minute video: Control Tower -> case drill-down -> AI vs Policy conflict -> recovery verified
- README: setup, run, architecture, honest limitations
- Public GitHub: no secrets, no .env in history
- Submission form answers
- Security checklist: all secrets in env, no floats for money, HMAC on all webhooks
- Reproducibility check: fresh clone -> pip install -r requirements.txt -> works

**Hard Gate:** Fresh clone -> full demo works -> video submitted -> no secrets in repo.

---

## 14. P0 / P1 / P2 Scope

### P0 — Must Ship (Non-Negotiable)

- Razorpay Test Mode subscription failure -> webhook
- Webhook HMAC verification + deduplication
- Recovery Case creation and lifecycle
- AI Recovery Analyst (diagnosis + recommendation)
- Unstructured text -> structured intent extraction
- Policy Engine with override audit
- MONITOR, ESCALATE, STOP, NO_ACTION
- At least ONE real Razorpay recovery action (Payment Link)
- Idempotent action execution
- Verification (payment_link.paid event)
- Separate Cash Recovered vs Subscription Reactivated metrics
- Audit trail (complete AI -> Policy -> Action -> Outcome log)
- Control Tower Kanban dashboard
- Batch evaluation report
- 5-minute demo video

### P1 — Add Only After P0 Is Stable

- Promise-to-Pay scheduler (deadline checker)
- Customer message input UI (text box in dashboard)
- Payment Method Recovery flow
- Richer case detail page
- Baseline comparison report

### P2 — Do Not Build

- Voice / WhatsApp integration
- Causal / uplift modeling
- Real merchant data
- Multi-tenant platform
- Complex agent memory systems
- Advanced forecasting

---

## 15. Security and Reliability Checklist

- All API keys in .env file only — never hardcoded
- .env in .gitignore — verify before every push
- Webhook HMAC using raw body bytes, not parsed JSON
- Event-ID deduplication on every webhook handler
- All monetary amounts in integer paise (never float, never decimal)
- Idempotency check before every Razorpay API call
- LLM responses validated against Pydantic schema before use
- LLM timeout -> deterministic ESCALATE fallback
- STOP flag cannot be overridden by AI recommendation
- Logs redacted of customer PII in production paths
- No real card or UPI data anywhere (Test Mode only)

---

## 16. The 5-Minute Demo Script

**Opening (30 sec)**
> "A merchant has 1,000 failed subscriptions. Rs 10 lakh is stuck. Razorpay has already done retries and notifications. What happens to the 300 cases that still have not recovered? That is Vasooli problem."

**Show Control Tower (60 sec)**
- Open dashboard. Show Kanban board with live cases.
- Highlight HIGH PRIORITY queue. Drill into one Rs 45,000 case.
- Show full AI reasoning -> Policy check -> action approved.

**Show AI vs Policy Conflict (60 sec)**
> "Watch what happens when AI gets it wrong."
- Show case where AI recommends OUTREACH but customer has opted out.
- Policy rejects it -> STOP logged.
- Audit trail shows: AI said OUTREACH -> Policy said STOP -> reason: opt_out_flag
> "The LLM is advisory. The guardrails are authoritative."

**Show Promise-to-Pay NLP (60 sec)**
- Paste customer message: "Friday ko kar dunga bhai"
- Show AI extraction: intent: PROMISE_TO_PAY, date: Friday
- Case moves to PROMISE_PENDING queue.
> "The AI just turned an unstructured WhatsApp message into a workflow state."

**Show Verified Recovery (60 sec)**
- Trigger payment_link.paid webhook.
- Show case move from ACTION_EXECUTED -> RECOVERED.
- Show metrics: Rs X Cash Recovered (separate from Rs Y Subscription Reactivated).
> "We only count money we can prove recovered."

**What Broke (30 sec)**
> "We discovered that out-of-order webhook delivery created ghost recovery cases. We fixed it with provider-state reconciliation — query Razorpay for ground truth, never trust event sequence alone."

**Close (30 sec)**
> "Vasooli does not replace Razorpay. It handles the recovery operations layer — turning revenue-at-risk events into managed, auditable, measured recovery cases."

---

## 17. Claims We Must NEVER Make

| Do NOT Say | Say Instead |
|---|---|
| "Razorpay cannot recover failed payments" | "Razorpay handles the payment retry layer; we handle the operations layer above it" |
| "We beat Razorpay recovery" | "We provide an auditable case management layer for cases that remain unresolved" |
| "Our AI recovered Rs X incremental revenue" | "Our system verified Rs X cash recovered through tracked actions" |
| "This is based on real BFSI data" | "This is a synthetic simulation dataset designed to cover realistic failure scenarios" |
| "Payment Link created = recovery" | "Recovery is only counted when payment_link.paid is verified" |
| "The LLM safely controls financial actions" | "The LLM is advisory only; the policy engine controls all financial actions" |

---

## 18. Final Success Checklist

The project is submission-ready ONLY when every item is checked:

- [ ] Razorpay Test Mode subscription failure -> webhook received
- [ ] Webhook HMAC verified + event deduplicated
- [ ] Recovery Case created from event
- [ ] AI produces valid structured JSON recommendation
- [ ] Customer free-text -> structured intent extraction works
- [ ] Policy engine overrides AI on opt-out
- [ ] Policy override logged to audit trail
- [ ] At least one Razorpay action executes (Payment Link)
- [ ] Action is idempotent (run twice -> one result)
- [ ] payment_link.paid webhook verifies recovery
- [ ] Cash Recovered != Subscription Reactivated (tracked separately)
- [ ] Exceptions and escalations are visible in dashboard
- [ ] Full audit trail: AI -> Policy -> Action -> Outcome
- [ ] Batch evaluation runs on 500+ synthetic cases
- [ ] Metrics report produced
- [ ] Control Tower Kanban dashboard works
- [ ] LLM failure -> safe fallback (ESCALATE)
- [ ] GitHub public, zero secrets in history
- [ ] .env not committed, .gitignore verified
- [ ] Fresh clone -> runs -> demo works
- [ ] 5-minute video recorded
- [ ] What Broke section documented
- [ ] Submission form answers complete

---

## 19. Final Product Thesis

> **Vasooli is an AI Revenue Recovery Operations Agent. It does not rebuild Razorpay payment infrastructure — it manages the recovery-case lifecycle around it. It synthesizes multi-signal context, extracts structured commitments from unstructured customer text, plans bounded next actions, enforces deterministic merchant policy over LLM recommendations, executes supported Razorpay workflows, and verifies what actually recovered — all in an auditable, measurable, honest way.**

### Core Engineering Principle

> **Build only what solves a real recovery-operations problem, is NOT a Razorpay primitive duplicate, uses AI where reasoning is genuinely valuable, and can be demonstrated and measured honestly in 48-72 hours.**

---

## 20. Official Sources

| Resource | URL |
|---|---|
| Razorpay Buildathon | https://razorpay.com/buildathon/ |
| Test Subscriptions | https://razorpay.com/docs/payments/subscriptions/test/ |
| Payment Retries | https://razorpay.com/docs/payments/subscriptions/payment-retries/ |
| Subscription Notifications | https://razorpay.com/docs/payments/subscriptions/notifications/ |
| Subscription Webhooks | https://razorpay.com/docs/webhooks/subscriptions/ |
| Webhook Validation | https://razorpay.com/docs/webhooks/validate-test/ |
| Payment Links | https://razorpay.com/docs/payments/payment-links/ |
| Payment Link Reminders | https://razorpay.com/docs/payments/payment-links/reminders/ |
| Payment Link Webhooks | https://razorpay.com/docs/webhooks/payment-links/ |

---

*Document Version 3.0 | LOCKED | Ready to Build*
