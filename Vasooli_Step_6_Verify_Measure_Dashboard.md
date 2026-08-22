# Vasooli — Step 6: Verify + Measure + Dashboard
### Detailed & Structured Implementation Plan | Razorpay AI Buildathon — Track 03

---

# 0. Step 6 Purpose

Step 5 ne recovery action **execute** kiya tha.

Step 6 ka kaam hai prove karna:

> **Kya action ke baad actually money recover hui? Aur kya recurring subscription actually recover/reactivate hui?**

This step converts execution records into **verified financial outcomes**.

## Step 6 responsibilities

```text
Step 5 Execution
      ↓
VERIFY external outcome
      ↓
RECONCILE payment/invoice/subscription state
      ↓
CLASSIFY outcome
      ↓
MEASURE batch-level recovery
      ↓
GENERATE exceptions
      ↓
PRESENT trustworthy dashboard
```

## Hard boundary

Step 6:

- verifies outcomes
- calculates metrics
- builds dashboard/read models

Step 6 does **not**:

- choose the recovery action
- change Step 4 policy
- invent recovery outcomes
- count an API request as recovered revenue

---

# 1. Step 6 Success Definition

A recovery is considered **verified** only when provider evidence supports the relevant outcome.

### Core rule

```text
Action requested
    ≠
Action accepted
    ≠
Recovery verified
```

For example:

```text
Payment Link created
        ↓
NOT recovered yet

Payment Link paid
        ↓
Cash recovered = YES

Subscription state becomes active
        ↓
Subscription reactivated = YES
```

These are separate facts.

---

# 2. Two Financial Metrics — NEVER MIX THEM

The dashboard must always display these separately.

## 2.1 Cash Recovered

Money successfully collected as a result of the recovery workflow.

```text
₹ Cash Recovered
```

This may include:

- one-time Payment Link collection
- successful recurring subscription charge
- other verified eligible collection

## 2.2 Subscription Revenue Reactivated

Recurring subscription revenue where the subscription itself successfully returns to the required active state.

```text
₹ Subscription Revenue Reactivated
```

A Payment Link payment alone does **not** automatically count here.

### Example

```text
Outstanding subscription amount: ₹999

Payment Link paid:
Cash Recovered = ₹999

Subscription remains halted:
Subscription Revenue Reactivated = ₹0
```

This distinction must appear everywhere:

- database
- dashboard
- batch report
- pitch
- README

---

# 3. Verification Architecture

Use **action-specific verification**.

```text
                  EXECUTION RESULT
                        ↓
                 VERIFY ROUTER
                        ↓
        ┌───────────────┼────────────────┐
        ↓               ↓                ↓
  ONE_TIME_RECOVERY   MANUAL_CHARGE    MONITOR
        ↓               ↓                ↓
 Payment Link event   payment/invoice   subscription
 / payment evidence  evidence           state
        │               │                │
        └───────────────┼────────────────┘
                        ↓
                STATE RECONCILIATION
                        ↓
                 VERIFIED OUTCOME
                        ↓
                    MEASURE
```

`ESCALATE`, `STOP`, and `NO_ACTION` do not create a recovery outcome by themselves.

---

# 4. Verification Evidence Hierarchy

Use provider evidence in this order.

## Strong evidence

- successful payment event
- captured payment
- paid invoice
- verified Payment Link paid event
- confirmed subscription state transition

## Weak evidence

- API request accepted
- Payment Link created
- invoice created
- action queued
- execution worker completed

Weak evidence must **never** be treated as money recovered.

---

# 5. Verification State Machine

Each execution should have a verification state.

```text
NOT_STARTED
    ↓
WAITING_FOR_EVIDENCE
    ↓
EVIDENCE_FOUND
    ↓
RECONCILING
    ↓
 ┌───────────────┬──────────────────┬─────────────────┐
 ↓               ↓                  ↓
RECOVERED     NOT_RECOVERED    PARTIAL/AMBIGUOUS
                                        ↓
                                   EXCEPTION
```

Recommended values:

```text
NOT_STARTED
WAITING
RECOVERED
NOT_RECOVERED
PARTIAL
UNKNOWN
```

---

# 6. ONE_TIME_RECOVERY Verification

## 6.1 Creation is not recovery

After Step 5:

```text
Payment Link created
```

set:

```text
verification_status = WAITING
cash_recovered = false
```

## 6.2 Evidence

Watch for the relevant Payment Link/payment evidence.

The exact provider event or current resource state should be used according to the Razorpay Test Mode flow implemented in Step 5.

Successful evidence should contain enough information to identify:

- Payment Link
- payment
- amount
- currency
- paid status

## 6.3 Verify amount

Do not rely only on a local expected amount.

Compare:

```text
expected_amount
vs
provider-confirmed amount
```

Only count the amount supported by the provider evidence.

## 6.4 Result

```text
Payment Link paid
     ↓
cash_recovered = true
     ↓
cash_recovered_amount = verified provider amount
```

Then separately reconcile subscription state.

---

# 7. Subscription Reactivation Verification

A one-time collection does not automatically mean recurring recovery.

After any successful collection:

```text
Fetch/reconcile subscription
        ↓
Current subscription state?
```

Possible outcomes:

```text
ACTIVE
PENDING
HALTED
CANCELLED
UNKNOWN
```

### Example

```text
Payment Link paid
+
subscription still HALTED

→ Cash Recovered = ₹999
→ Subscription Reactivated = ₹0
```

This is a valid successful cash recovery with unsuccessful subscription recovery.

---

# 8. MANUAL_CHARGE Verification

For an eligible manual charge:

```text
charge requested
      ↓
payment created?
      ↓
authorized?
      ↓
captured?
      ↓
invoice paid?
      ↓
subscription state reconciled
```

Do not mark recovery from the manual-charge request alone.

For unsupported domestic-card cases:

```text
MANUAL_CHARGE
      ↓
eligibility rejected
      ↓
NO recovery attempt
      ↓
ESCALATED / EXCEPTION
```

---

# 9. MONITOR Verification

`MONITOR` intentionally does not create an immediate recovery.

Its verification responsibility is:

```text
current subscription state
+
retry lifecycle status
```

Example:

```text
MONITOR
↓
subscription still pending
↓
not recovered yet
```

Later:

```text
subscription charged
↓
payment captured
↓
verified recovery
```

Therefore MONITOR cases may move from:

```text
WAITING
```

to:

```text
RECOVERED
```

without Vasooli directly executing a new payment action.

---

# 10. ESCALATE / STOP Verification

These actions should never be counted as recovered.

## ESCALATE

```text
verification_status = NOT_APPLICABLE
recovery_status = UNRECOVERED
reason = HUMAN_INTERVENTION_REQUIRED
```

## STOP

```text
verification_status = NOT_APPLICABLE
recovery_status = STOPPED
recovered_amount = 0
```

If a later human action successfully recovers the money, that should become a **new linked recovery record**, not silently mutate the original STOP result.

---

# 11. Provider Reconciliation

Never trust only webhook arrival order.

Use:

```text
Webhook
   ↓
identify resource
   ↓
read current DB projection
   ↓
if state is stale/ambiguous
   ↓
fetch current provider state where necessary
   ↓
update projection
```

This protects against:

- duplicate webhooks
- out-of-order events
- delayed events
- missed events
- worker restarts

Step 2 owns the ingestion/state mechanics; Step 6 consumes the reconciled state.

---

# 12. Idempotent Verification

Verification must also be idempotent.

Example:

```text
payment.captured received
payment.captured received again
```

should result in:

```text
recovered_amount counted once
```

Use a unique provider event identifier where available plus an outcome/recovery key.

### Never:

```text
event 1 → +₹999
event 2 duplicate → +₹999
```

Correct:

```text
event 1 → +₹999
event 2 duplicate → +₹0 incremental
```

---

# 13. Recovery Outcome Schema

Create a durable `recovery_outcomes` record.

Suggested fields:

```text
id
execution_id
decision_id
subscription_id
customer_id

action
verification_status

cash_recovered
cash_recovered_amount
cash_recovered_at

subscription_reactivated
subscription_reactivated_amount
subscription_reactivated_at

provider_payment_id
provider_invoice_id
provider_payment_link_id

verification_source
verification_evidence_id

failure_reason
exception_reason

verified_at
created_at
updated_at
```

---

# 14. Exception Classification

Every unresolved case must have a structured reason.

Recommended categories:

```text
PAYMENT_NOT_COMPLETED
SUBSCRIPTION_REMAINS_HALTED
CUSTOMER_CANCELLED
CUSTOMER_OPTED_OUT
UNKNOWN_PROVIDER_STATE
PROVIDER_ERROR
PAYMENT_LINK_EXPIRED
MANUAL_CHARGE_UNSUPPORTED
VERIFICATION_TIMEOUT
AMOUNT_MISMATCH
DUPLICATE_RECOVERY_PREVENTED
```

Allow:

```text
UNKNOWN / INSUFFICIENT_EVIDENCE
```

when evidence does not support a stronger classification.

---

# 15. Verification Timeout

A recovery cannot remain `WAITING` forever.

Configure a verification window, for example:

```text
VERIFICATION_TIMEOUT_MINUTES = configurable
```

Do not hard-code a business assumption that every payment must verify within one exact duration.

After timeout:

```text
WAITING
  ↓
VERIFICATION_TIMEOUT
  ↓
EXCEPTION
```

Do not call it:

```text
RECOVERED
```

and do not automatically call it:

```text FAILED
```

unless provider evidence proves failure.

---

# 16. Amount Accounting Rules

Use integer minor units internally.

For INR:

```text
₹999 = 99900 paise
```

Avoid floating-point arithmetic for money.

### Required invariants

```text
recovered_amount >= 0

recovered_amount <= eligible outstanding amount
```

unless the business rule explicitly permits another interpretation.

### Duplicate safeguard

For a subscription/recovery case:

```text
total_verified_cash_recovered
```

must not exceed the amount legitimately recoverable without an explicit reason.

---

# 17. Batch Measurement

After individual outcomes are verified, compute batch metrics.

## Required headline metrics

```text
Total records processed
Total revenue at risk
Total cash recovered
Cash recovery rate
Total unrecovered revenue
Subscription revenue reactivated
Subscription recovery rate
```

### Formula

```text
Cash Recovery Rate
= Verified Cash Recovered / Revenue At Risk × 100
```

```text
Subscription Reactivation Rate
= Reactivated Subscription Revenue /
  Revenue At Risk Eligible for Subscription Recovery × 100
```

Use denominators carefully and document them.

---

# 18. Do Not Cherry-Pick

The batch report must include every evaluation record.

Example:

```text
2,000 records

Revenue at risk:        ₹12,40,000
Cash recovered:          ₹7,30,000
Unrecovered:              ₹5,10,000

Recovery rate:               58.87%
```

Then show the exception breakdown:

```text
₹1.8L  customer cancellation
₹1.4L  unresolved/unknown
₹0.9L  payment not completed
₹0.6L  unsupported recovery
₹0.4L  verification timeout
```

Do not remove unsuccessful cases from the denominator.

---

# 19. Action-Level Metrics

Break results down by action.

```text
MONITOR
→ cases observed
→ cases eventually recovered

ONE_TIME_RECOVERY
→ links created
→ links paid
→ cash recovered

MANUAL_CHARGE
→ eligible attempts
→ successful
→ unsupported
→ escalated

ESCALATE
→ cases routed
→ pending human resolution

STOP
→ cases blocked
```

This allows the pitch to show:

> Which intervention actually produced the most recovered revenue?

---

# 20. AI / Policy Metrics

Step 6 can also measure Step 4 decision quality.

Suggested metrics:

```text
Policy actions by category
LLM recommendation vs final policy decision
Policy override count
Guardrail block count
UNKNOWN diagnosis count
Escalation rate
No-action rate
```

Particularly useful:

```text
LLM recommended action
        ↓
Policy final action
```

Example:

```text
LLM: ONE_TIME_RECOVERY
Policy: STOP
Reason: customer opted out
```

Count this as a **safe policy override**, not a model failure.

---

# 21. Exception List — First-Class Dashboard Feature

The dashboard must have a dedicated exception table.

Suggested columns:

| Field | Purpose |
|---|---|
| Subscription | Identify case |
| Amount | Revenue at risk |
| Diagnosis | Why it failed |
| Action | What Vasooli attempted |
| Outcome | Recovered / not recovered / stopped |
| Exception | Why unresolved |
| Cash recovered | Verified amount |
| Subscription state | Current state |
| Timestamp | Auditability |

Filters:

```text
all
recovered
unrecovered
exceptions
stopped
escalated
pending verification
```

---

# 22. Audit Trail View

A user should be able to open one recovery case and see:

```text
EVENT
  ↓
DIAGNOSIS
  ↓
DECISION
  ↓
POLICY
  ↓
EXECUTION
  ↓
PROVIDER RESPONSE
  ↓
VERIFICATION
  ↓
FINAL OUTCOME
```

Example:

```text
10:01:02
subscription.pending received

10:01:03
Diagnosis:
CARD_EXPIRED

10:01:03
Recovery score:
0.74

10:01:03
LLM recommendation:
ONE_TIME_RECOVERY

10:01:03
Policy:
ONE_TIME_RECOVERY
Guardrails:
PASSED

10:01:04
Payment Link created

10:05:44
Payment Link paid

10:05:45
Cash recovered:
₹999

10:05:46
Subscription state:
HALTED

FINAL:
Cash Recovered = ₹999
Subscription Reactivated = ₹0
```

This is an excellent pitch artifact.

---

# 23. Dashboard Structure

Keep the UI simple.

## Page 1 — Overview

Top cards:

```text
₹ Revenue At Risk
₹ Cash Recovered
₹ Subscription Revenue Reactivated
Cash Recovery Rate
Cases Processed
Exceptions
```

## Page 2 — Recovery Cases

Table:

```text
Subscription
Amount
Diagnosis
Action
Status
Cash Recovered
Subscription State
```

## Page 3 — Exceptions

Dedicated unresolved/stopped/escalated cases.

## Page 4 — Audit Trail

Timeline for one selected case.

## Page 5 — Batch Results

Charts/tables showing action-level performance.

Do not build a complex analytics product.

---

# 24. Dashboard Data Model

The frontend should read from **read models/aggregations**, not directly reconstruct financial metrics from raw webhook events.

Recommended endpoints:

```text
GET /dashboard/summary
GET /dashboard/recovery-cases
GET /dashboard/exceptions
GET /dashboard/recovery-actions
GET /dashboard/audit/{subscription_id}
GET /dashboard/batch-metrics
```

Example summary:

```json
{
  "records_processed": 1000,
  "revenue_at_risk": 740000,
  "cash_recovered": 421000,
  "subscription_reactivated": 318000,
  "cash_recovery_rate": 56.89,
  "exception_count": 184
}
```

---

# 25. Aggregation Rules

Every dashboard metric must be reproducible from stored recovery outcomes.

For example:

```text
cash_recovered
=
SUM(recovery_outcomes.cash_recovered_amount
    WHERE verification_status = RECOVERED)
```

Never use:

```text
SUM(executions.amount
    WHERE execution.status = SUCCESS)
```

because execution success does not necessarily mean payment success.

---

# 26. Batch Evaluation Separation

Keep these two concepts separate:

## Evaluation dataset

```text
500–2,000 synthetic records
```

Used for:

- recovery strategy evaluation
- batch metrics
- exception rates

## Real Razorpay Test Mode flows

```text
small controlled set
```

Used for:

- integration proof
- webhook proof
- real API execution
- demo verification

Do not pretend the synthetic batch is made of real Razorpay transactions.

---

# 27. Synthetic Ground Truth vs Verified Outcome

Step 3 may contain ground-truth information for evaluation.

Do **not** use ground truth to claim actual Razorpay revenue recovery.

Use:

```text
Synthetic ground truth
→ evaluate decision quality
```

and:

```text
Razorpay Test Mode evidence
→ prove integration/outcome mechanics
```

Keep those evidence sources labeled separately.

---

# 28. Evaluation Report

Generate a machine-readable report:

```text
reports/
└── step6_report.json
```

Suggested sections:

```json
{
  "dataset": {
    "records": 2000
  },
  "financials": {
    "revenue_at_risk": 1240000,
    "cash_recovered": 730000,
    "subscription_reactivated": 510000
  },
  "rates": {
    "cash_recovery_rate": 58.87
  },
  "actions": {},
  "exceptions": {},
  "verification": {}
}
```

Also generate:

```text
reports/step6_report.csv
```

for audit/debug use.

---

# 29. Required Tests

## Verification tests

- [ ] Payment Link created but unpaid → not recovered
- [ ] Payment Link paid → cash recovered exactly once
- [ ] Duplicate paid event → no double count
- [ ] Subscription remains halted → cash recovered, subscription not reactivated
- [ ] Subscription becomes active → subscription recovery counted
- [ ] Provider state unknown → UNKNOWN, not recovered
- [ ] Verification timeout → exception
- [ ] Amount mismatch → exception
- [ ] Duplicate verification event → idempotent result
- [ ] STOP execution → no recovery
- [ ] ESCALATE execution → no recovery

## Accounting tests

- [ ] No negative recovery
- [ ] No floating-point money calculations
- [ ] Duplicate events do not inflate totals
- [ ] Batch denominator is stable
- [ ] Recovery totals are reproducible
- [ ] Cash and subscription metrics never get mixed

## Dashboard tests

- [ ] Summary matches database aggregation
- [ ] Exception list matches stored outcomes
- [ ] Case audit timeline is complete
- [ ] Filters do not change underlying totals incorrectly

---

# 30. Failure Scenarios To Intentionally Test

### Scenario 1 — Payment Link created, customer never pays

Expected:

```text
cash_recovered = 0
status = NOT_RECOVERED / WAITING depending on configured window
```

### Scenario 2 — Payment Link paid twice event received

Expected:

```text
cash counted once
```

### Scenario 3 — Payment succeeds but subscription remains halted

Expected:

```text
cash recovered > 0
subscription reactivated = 0
```

### Scenario 4 — Webhook delayed

Expected:

```text
WAITING
→ later reconcile
→ correct final state
```

### Scenario 5 — Provider state inconsistent with local DB

Expected:

```text
provider becomes source for reconciliation
local projection updated
```

### Scenario 6 — Amount mismatch

Expected:

```text
NO recovery credit
EXCEPTION
```

---

# 31. Dashboard Design Principle

The dashboard should make it impossible to accidentally confuse:

```text
Money Collected
```

with:

```text
Recurring Revenue Restored
```

Recommended visual hierarchy:

```text
                 REVENUE AT RISK
                      ₹X

        ┌─────────────────────────────┐
        │      CASH RECOVERED         │
        │          ₹Y                 │
        └─────────────────────────────┘

        ┌─────────────────────────────┐
        │ SUBSCRIPTION REACTIVATED    │
        │          ₹Z                 │
        └─────────────────────────────┘

        Exceptions: N
```

Then show the exception table immediately below.

---

# 32. Step 6 Implementation Order

## Phase A — Verification service

Build:

```text
verification/
├── verifier.py
├── payment_link_verifier.py
├── subscription_verifier.py
├── manual_charge_verifier.py
└── reconciliation.py
```

## Phase B — Recovery outcome model

Add:

```text
recovery_outcomes
```

and indexes/unique constraints.

## Phase C — Idempotent outcome processing

Implement:

```text
provider event
→ outcome lookup
→ apply once
```

## Phase D — Financial accounting

Implement:

```text
cash recovered
subscription reactivated
revenue at risk
```

## Phase E — Exception classification

Map unresolved outcomes into structured exception categories.

## Phase F — Batch aggregation

Generate summary metrics and action-level metrics.

## Phase G — Dashboard API

Create read-only summary/case/exception/audit endpoints.

## Phase H — Frontend

Build only the views needed for the demo.

## Phase I — End-to-end tests

Run real + synthetic verification scenarios.

---

# 33. Recommended Repository Structure

Adapt to the existing Step 1–5 codebase:

```text
backend/
├── app/
│   ├── verification/
│   │   ├── verifier.py
│   │   ├── payment_link.py
│   │   ├── subscription.py
│   │   ├── reconciliation.py
│   │   └── exceptions.py
│   │
│   ├── measurement/
│   │   ├── accounting.py
│   │   ├── aggregations.py
│   │   └── batch_metrics.py
│   │
│   ├── dashboard/
│   │   ├── routes.py
│   │   ├── schemas.py
│   │   └── queries.py
│   │
│   └── models/
│       └── recovery_outcome.py
│
├── reports/
│   ├── step6_report.json
│   └── step6_report.csv
│
└── tests/
    ├── verification/
    ├── measurement/
    └── dashboard/
```

---

# 34. Step 6 Demo Scenarios

Prepare at least three.

## Demo A — Successful cash recovery

```text
failed subscription
      ↓
ONE_TIME_RECOVERY
      ↓
Payment Link created
      ↓
test payment succeeds
      ↓
dashboard:
₹999 CASH RECOVERED
```

## Demo B — Cash recovered but subscription not restored

```text
Payment Link paid
      ↓
subscription still halted
      ↓
dashboard:
Cash Recovered = ₹999
Subscription Reactivated = ₹0
```

This demonstrates honesty.

## Demo C — No unsafe recovery

```text
customer opted out
      ↓
STOP
      ↓
₹0 recovered
      ↓
exception/audit trail
```

This demonstrates bounded execution.

---

# 35. Step 6 Hard Gate

Step 6 is complete only when:

```text
Step 5 action
      ↓
provider outcome
      ↓
action-specific verification
      ↓
idempotent recovery outcome
      ↓
cash/subscription metrics
      ↓
exception list
      ↓
dashboard
```

and all of these are true:

- [ ] A created-but-unpaid Payment Link is NOT counted as recovered.
- [ ] A paid Payment Link is counted exactly once.
- [ ] Subscription reactivation is measured separately.
- [ ] Provider evidence is required before recovery credit.
- [ ] Duplicate events cannot double-count revenue.
- [ ] Unknown/ambiguous states are exceptions.
- [ ] Batch metrics are reproducible.
- [ ] Dashboard totals match backend aggregations.
- [ ] Exception list is complete.
- [ ] Real Razorpay Test Mode result and synthetic evaluation results are clearly labeled separately.

---

# 36. Step 6 Deliverables

At the end of Step 6:

```text
1. Verification engine
2. Recovery outcome model
3. Provider reconciliation logic
4. Financial accounting logic
5. Exception classifier
6. Batch metrics generator
7. Dashboard API
8. Basic dashboard UI
9. Step 6 JSON/CSV report
10. Automated verification/accounting tests
11. Three reliable demo scenarios
12. Updated audit trail
```

---

# 37. Step 6 → Step 7 Contract

Step 7 must receive:

```text
Verified recovery outcomes
+
Batch metrics
+
Exception report
+
Audit evidence
+
Working dashboard
```

Step 7 can then focus on:

- full batch evaluation
- final metrics
- README
- repository cleanup
- pitch narrative
- 5-minute recording
- submission answers

Step 7 should **not** discover that the recovery accounting is wrong.

---

# 38. Final Principle

The most important Step 6 rule is:

> **Never say "we recovered ₹X" because our system requested an action. Say it only when provider evidence proves the collection.**

And keep these two numbers separate:

```text
₹ CASH RECOVERED
        ≠
₹ SUBSCRIPTION REVENUE REACTIVATED
```

That distinction is one of the strongest trust signals in the Vasooli build.
