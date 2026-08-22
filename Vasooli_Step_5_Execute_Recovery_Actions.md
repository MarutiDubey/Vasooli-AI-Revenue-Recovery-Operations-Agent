# Vasooli — Step 5: Execute Recovery Actions
### Detailed Implementation Plan | Razorpay AI Buildathon — Track 03

---

## 0. Step Purpose

Step 5 converts the **decision package produced by Step 4** into bounded, auditable execution.

### Step 5 input

A validated decision package containing:

- `subscription_id`
- `customer_id`
- `policy_decision`
- `action`
- `reason`
- `confidence/recovery_score` if available
- `guardrail_result`
- `idempotency_key`
- relevant Razorpay identifiers
- execution context

### Step 5 output

A durable execution record containing:

- requested action
- eligibility check
- execution attempt
- Razorpay/API result where applicable
- resulting external identifier
- execution status
- failure/exception reason
- verification status
- timestamps
- audit information

### Hard boundary

Step 5 **executes actions**.

It does **not** redefine diagnosis or policy.  
Step 4 owns the decision.  
Step 6 owns final verification/measurement/dashboard aggregation.

---

# 1. Action Contract

Vasooli supports these actions:

| Action | Purpose | Real Test-Mode execution? | Step 5 priority |
|---|---|---:|---|
| `MONITOR` | Do nothing and allow the existing Razorpay retry lifecycle to continue | No external mutation | MUST |
| `ONE_TIME_RECOVERY` | Create a one-time recovery Payment Link where policy permits | Yes | MUST |
| `ESCALATE` | Route case to human/merchant review queue | Internal only | MUST |
| `STOP` | Explicitly prevent further automated recovery | Internal only | MUST |
| `MANUAL_CHARGE` | Charge an eligible issued invoice when supported | Conditional | SHOULD |
| `NO_ACTION` | Record that no intervention is required | No external mutation | SHOULD |

Do **not** add an unbounded `RETRY` action that bypasses Razorpay's own subscription retry lifecycle.

---

# 2. Execution Architecture

```text
Step 4 Decision Package
        ↓
Validate decision contract
        ↓
Execution Idempotency Check
        ↓
Eligibility / Guardrail Re-check
        ↓
Action Dispatcher
        ↓
 ┌────────────┬──────────────────┬────────────┬────────┐
 ↓            ↓                  ↓            ↓
MONITOR   ONE_TIME_RECOVERY   ESCALATE      STOP
             ↓
        Payment Link API
             ↓
      Persist external ID
             ↓
      Wait for outcome event

Optional:
MANUAL_CHARGE
      ↓
issued invoice + supported payment method
      ↓
payment/invoice API result
```

---

# 3. Preconditions

Before any execution:

## 3.1 Validate decision package

Required:

```text
decision_id
subscription_id
action
policy_version
decision_timestamp
```

For `ONE_TIME_RECOVERY`:

```text
amount
currency
customer/reference information
recovery reason
```

For `MANUAL_CHARGE`:

```text
invoice_id
invoice_status = issued
payment_method_supported = true
```

If required fields are missing:

```text
execution_status = REJECTED
reason = INVALID_DECISION_PACKAGE
```

Never attempt a money action with incomplete context.

---

# 4. Global Execution Guardrails

These checks run **again** immediately before execution.

Why?

Because state can change between Step 4 decision time and Step 5 execution time.

Example:

```text
10:00 → Step 4 says PAYMENT_LINK
10:01 → subscription becomes paid
10:02 → Step 5 executes
```

That would be a duplicate recovery attempt.

Therefore:

```text
Decision
  ↓
Fresh state check
  ↓
Still eligible?
  ├── NO → reject / no-op
  └── YES → execute
```

### Mandatory pre-execution checks

- Customer is not opted out.
- Mandate/subscription has not been explicitly cancelled.
- Recovery has not already succeeded.
- Decision has not expired.
- Action is allowed for the current subscription state.
- Amount is positive and valid.
- Currency is supported by the configured workflow.
- Test-mode budget/limits are not exceeded.
- Same `decision_id` has not already executed.
- Same logical recovery case has not already created the same external action.

---

# 5. Execution Idempotency

Financial workflows must be safe against retries.

Create a unique execution key such as:

```text
vasooli:{subscription_id}:{decision_id}:{action}
```

Store it in the database with a unique constraint.

### Before execution

```text
execution_key exists?
    ├── YES + SUCCESS → return prior result
    ├── YES + IN_PROGRESS → do not duplicate
    ├── YES + FAILED_RETRYABLE → controlled retry
    └── NO → create execution record
```

### Important

Do not use a timestamp alone as an idempotency key.

The same logical decision must map to the same key.

---

# 6. MONITOR Action

## Purpose

Deliberately do nothing because Razorpay's own retry lifecycle is already handling the failed recurring payment.

Example:

```text
subscription.pending
+
retries remain
+
recovery likelihood high
+
no additional intervention justified
```

### Execution

No Razorpay mutation.

Persist:

```text
action = MONITOR
status = ACCEPTED
external_action = NONE
reason = "Allow Razorpay-managed retry lifecycle to continue"
```

### Important

`MONITOR` must not be reported as recovered.

It means:

> Vasooli intentionally chose not to intervene.

---

# 7. ONE_TIME_RECOVERY

## Purpose

Collect an outstanding amount through a one-time Razorpay Payment Link when the policy explicitly permits it.

### Critical semantic rule

A successful Payment Link payment means:

```text
cash recovered = true
```

It does **not automatically mean**:

```text
subscription reactivated = true
```

Keep those states separate.

---

## 7.1 Eligibility

Allow only when:

- customer has not opted out
- subscription is not explicitly cancelled by the customer
- amount is eligible for one-time collection
- recovery case is not already settled
- policy decision = `ONE_TIME_RECOVERY`
- test-mode Payment Link budget remains available
- required customer/reference fields are valid

### Reject when

- amount already paid
- active duplicate recovery exists
- opt-out/cancellation is present
- action budget exhausted
- decision is stale
- invalid amount/currency

---

## 7.2 Payment Link creation

Construct the request from the decision package.

Persist before/after the API call:

```text
execution_id
decision_id
subscription_id
amount
currency
created_at
```

After successful API response, persist:

```text
payment_link_id
short_url
provider_response
provider_created_at
```

Never store API secrets in the database or logs.

---

## 7.3 Result states

Use explicit states:

```text
PENDING
CREATED
PAID
EXPIRED
CANCELLED
FAILED
UNKNOWN
```

At Step 5:

```text
created ≠ recovered
```

Only Step 6 verification can promote the case to:

```text
recovered = true
```

---

## 7.4 Test-mode budget

Razorpay test environments have documented Payment Link limits.

Maintain an internal counter:

```text
payment_links_created_test_mode
payment_links_remaining_budget
```

Add a configurable safety ceiling lower than the provider hard limit.

Example:

```text
MAX_DEMO_PAYMENT_LINKS = 20
```

Do not spend all available test resources accidentally.

---

# 8. ESCALATE Action

## Purpose

Move cases requiring human judgment out of automated execution.

Typical reasons:

- `UNKNOWN / INSUFFICIENT_EVIDENCE`
- high-value recovery
- unsupported payment method
- manual-charge eligibility failure
- policy conflict
- repeated unsuccessful interventions
- suspicious or inconsistent state

### Minimum implementation

A database queue is sufficient for the hackathon.

Record:

```text
case_id
subscription_id
amount
reason
recommended_next_step
priority
created_at
status = OPEN
```

Example:

```text
ESCALATE
reason = UNKNOWN_FAILURE_REASON
priority = HIGH
```

Do not claim this is a full human workflow if the prototype only creates a queue entry.

---

# 9. STOP Action

## Purpose

Hard-stop automated recovery.

### Mandatory STOP scenarios

```text
customer_opt_out = true
OR
mandate explicitly cancelled
OR
policy says stop
OR
maximum intervention threshold reached
```

Persist:

```text
action = STOP
status = BLOCKED
automation_allowed = false
stop_reason = ...
```

### Critical property

Once STOP is recorded, later automated workers must respect it unless a new explicit decision supersedes it.

This prevents:

```text
STOP
↓
background worker
↓
creates Payment Link anyway
```

---

# 10. NO_ACTION

Use when the system intentionally concludes that no recovery intervention is appropriate.

Examples:

```text
payment already recovered
subscription active
nothing is currently overdue
risk too low for intervention
```

Persist it separately from `MONITOR`:

- `MONITOR` = continue observing an active recovery lifecycle.
- `NO_ACTION` = no recovery workflow is required at this time.

Neither counts as recovered by itself.

---

# 11. MANUAL_CHARGE — SHOULD

This is optional for the build.

## Eligibility

All of the following must be true:

```text
invoice exists
AND invoice.status = issued
AND payment method supports manual charging
AND policy decision = MANUAL_CHARGE
AND customer is not opted out
AND no successful recovery already exists
```

Domestic-card manual charging must **not** be assumed to work.

### Implementation strategy

Build the eligibility gate and code path, but do not make this the hero demo action.

If unsupported:

```text
MANUAL_CHARGE
   ↓
eligibility check fails
   ↓
ESCALATE
```

This is preferable to making an unsupported API call.

---

# 12. Provider API Error Handling

Classify execution errors.

## 12.1 Retryable

Examples:

```text
network timeout
temporary 5xx
transient transport failure
```

Response:

```text
FAILED_RETRYABLE
```

Use bounded retries with backoff.

Do not retry indefinitely.

---

## 12.2 Non-retryable

Examples:

```text
invalid request
unsupported operation
invalid state
authorization/configuration error
```

Response:

```text
FAILED_PERMANENT
```

Route to exception handling/escalation where appropriate.

---

## 12.3 Unknown outcome

Most dangerous case:

```text
request sent
      ↓
network timeout
      ↓
we don't know whether Razorpay created the action
```

Do **NOT** blindly issue the same action again.

Instead:

```text
UNKNOWN_OUTCOME
      ↓
reconcile provider state
      ↓
did action exist?
   ├── YES → persist external result
   └── NO  → controlled retry if safe
```

---

# 13. Action State Machine

Use a consistent execution state machine:

```text
CREATED
  ↓
ELIGIBILITY_CHECK
  ↓
 ┌───────────────┐
 │ eligible?     │
 └──────┬────────┘
        │
   NO   │   YES
   ↓    │    ↓
REJECTED │ EXECUTING
         │    ↓
         │ RESULT
         │
         ├── SUCCESS
         ├── FAILED_RETRYABLE
         ├── FAILED_PERMANENT
         └── UNKNOWN_OUTCOME
```

Never jump directly from:

```text
EXECUTING → RECOVERED
```

Recovery requires verification in Step 6.

---

# 14. Database Records

Step 5 should add execution-level persistence to the Step 2/4 schema.

## `executions`

```text
id
decision_id
subscription_id
customer_id
action
execution_key
status
eligibility_status
provider_name
provider_resource_id
amount
currency
requested_at
started_at
completed_at
error_code
error_message
metadata_json
```

## `escalations`

```text
id
execution_id
subscription_id
priority
reason
status
created_at
resolved_at
resolution_note
```

## `recovery_actions`

Optional normalized audit view:

```text
id
subscription_id
action
status
amount
external_id
source
created_at
```

---

# 15. Audit Trail

Every execution must answer:

```text
WHO/WHAT made the decision?
WHY was the action allowed?
WHAT action was requested?
WHEN was it requested?
WHAT did Razorpay return?
WHAT happened afterward?
```

Example:

```text
Decision:
ONE_TIME_RECOVERY

Reason:
Pending subscription + eligible outstanding amount

Guardrail:
Passed

Action:
Create Payment Link

Provider:
Razorpay Test Mode

Result:
Payment Link created

External ID:
plink_...

Verification:
Pending

Recovered:
Not yet confirmed
```

This is more trustworthy than a simple `success=true`.

---

# 16. Logging Rules

## Log

- execution ID
- decision ID
- subscription ID
- action
- status
- external IDs
- error class
- latency
- timestamps

## Never log

- Razorpay API secret
- authorization credentials
- full payment-method secrets
- unnecessary sensitive customer data
- raw secrets from environment variables

For debugging, redact sensitive request/response fields.

---

# 17. API Endpoints

Suggested internal endpoints:

```text
POST /internal/executions/run
POST /internal/executions/{execution_id}/reconcile
GET  /internal/executions/{execution_id}
GET  /internal/subscriptions/{subscription_id}/recovery-history
GET  /internal/escalations
```

Do not expose privileged execution endpoints publicly without authentication.

For the hackathon prototype, these may remain local/internal.

---

# 18. Execution Worker

Do not make the webhook handler perform the full action synchronously.

Recommended flow:

```text
Webhook
   ↓
Persist event
   ↓
Queue decision/execution job
   ↓
Worker executes action
   ↓
Persist result
```

For the first implementation, a simple background worker/job table is enough.

Do not introduce Redis/Celery unless needed.

SQLite + a lightweight worker loop is sufficient for the prototype.

---

# 19. Test Scenarios

At minimum, implement these.

## Scenario A — MONITOR

```text
pending
high recovery score
retry still active

→ MONITOR
→ no provider mutation
```

Expected:

```text
execution.status = ACCEPTED
recovered = false
```

---

## Scenario B — ONE_TIME_RECOVERY success path

```text
pending/halted
eligible
policy = ONE_TIME_RECOVERY

→ create Payment Link
→ store payment_link_id
→ later verify paid
```

Expected:

```text
cash_recovered = true
subscription_reactivated = separately evaluated
```

---

## Scenario C — ONE_TIME_RECOVERY rejected by guardrail

```text
customer_opt_out = true
```

Expected:

```text
action = STOP
Payment Link must NOT be created
```

This is a critical negative test.

---

## Scenario D — ESCALATE

```text
diagnosis = UNKNOWN
```

Expected:

```text
no provider mutation
escalation queue entry created
```

---

## Scenario E — STOP

```text
mandate cancelled
```

Expected:

```text
no provider mutation
automation disabled
```

---

## Scenario F — MANUAL_CHARGE unsupported

```text
invoice = issued
payment method = domestic card
```

Expected:

```text
manual charge rejected by eligibility gate
no unsafe API call
ESCALATE
```

---

## Scenario G — Duplicate execution

Send the same `decision_id` twice.

Expected:

```text
only one logical provider action
second request returns prior execution/result
```

---

## Scenario H — Provider timeout

Simulate:

```text
API request timeout
```

Expected:

```text
FAILED_RETRYABLE or UNKNOWN_OUTCOME
```

Never blindly create a second money action before reconciliation.

---

# 20. Integration Test Matrix

| Test | Expected |
|---|---|
| valid MONITOR | no external mutation |
| valid Payment Link decision | one link created |
| duplicate decision | no duplicate link |
| opted-out customer | STOP |
| cancelled mandate | STOP |
| UNKNOWN diagnosis | ESCALATE |
| unsupported manual charge | ESCALATE |
| invalid amount | REJECTED |
| provider 5xx | bounded retry |
| provider timeout | UNKNOWN_OUTCOME + reconcile |
| Payment Link already paid | no duplicate recovery |
| stale decision | rejected/re-evaluated |

All should be automated where practical.

---

# 21. Metrics for Step 5

Do not claim final revenue recovery metrics here.

Step 5 should produce execution metrics:

```text
execution_attempts
successful_provider_requests
failed_provider_requests
retryable_failures
unknown_outcomes
guardrail_rejections
escalations
stops
payment_links_created
manual_charge_attempts
average_execution_latency
```

Step 6 will convert verified outcomes into:

```text
₹ Cash Recovered
₹ Subscription Revenue Reactivated
```

---

# 22. Demo-Critical Execution Flow

The main demo should use a flow that is reliable and easy to explain.

Recommended hero path:

```text
Failed subscription event
        ↓
Vasooli decides:
ONE_TIME_RECOVERY
        ↓
Guardrails pass
        ↓
Razorpay Test Payment Link created
        ↓
Customer completes test payment
        ↓
Verification event/status
        ↓
Dashboard shows:
₹999 CASH RECOVERED
```

Then a second short path:

```text
Customer opted out
        ↓
Policy = STOP
        ↓
NO PAYMENT LINK CREATED
        ↓
Audit log shows blocked action
```

And a third:

```text
LLM recommends recovery
        ↓
Policy blocks it
        ↓
ESCALATE
```

These three together demonstrate:

- execution
- safety
- AI judgment

---

# 23. What NOT to Build in Step 5

Do not add:

- a general-purpose payment engine
- a custom subscription retry scheduler
- unlimited retries
- automatic action based solely on LLM output
- large-scale real Razorpay API loops
- production payment processing
- unnecessary queues/infrastructure
- a full CRM/helpdesk
- customer messaging infrastructure unless required for the demo

Keep execution narrow and reliable.

---

# 24. Suggested File Structure

```text
backend/
├── app/
│   ├── execution/
│   │   ├── dispatcher.py
│   │   ├── eligibility.py
│   │   ├── idempotency.py
│   │   ├── state_machine.py
│   │   ├── actions/
│   │   │   ├── monitor.py
│   │   │   ├── one_time_recovery.py
│   │   │   ├── escalate.py
│   │   │   ├── stop.py
│   │   │   └── manual_charge.py
│   │   └── reconciliation.py
│   ├── integrations/
│   │   └── razorpay/
│   │       ├── client.py
│   │       ├── payment_links.py
│   │       └── invoices.py
│   ├── models/
│   │   ├── execution.py
│   │   └── escalation.py
│   └── schemas/
│       └── execution.py
└── tests/
    └── execution/
        ├── test_monitor.py
        ├── test_payment_link.py
        ├── test_guardrails.py
        ├── test_idempotency.py
        ├── test_manual_charge.py
        └── test_unknown_outcome.py
```

Adapt this to the existing Step 1–4 project structure rather than duplicating models/configuration.

---

# 25. Implementation Order

Build in this order:

### Phase A — Execution contract

- Define execution request/response schemas.
- Define action enum.
- Define execution status enum.
- Define database records.

### Phase B — Shared controls

- Eligibility validator.
- Execution idempotency.
- stale-decision check.
- global STOP/opt-out enforcement.

### Phase C — Safe actions first

1. `MONITOR`
2. `ESCALATE`
3. `STOP`

These don't require external money mutation.

### Phase D — Razorpay action

4. `ONE_TIME_RECOVERY`

Implement:

```text
decision
→ eligibility
→ Payment Link creation
→ persist external ID
```

Do not call it recovered yet.

### Phase E — Optional path

5. `MANUAL_CHARGE`

Only after eligibility rules are reliable.

### Phase F — Failure handling

- timeout
- 5xx
- invalid response
- duplicate execution
- unknown outcome

### Phase G — Tests

Run the complete execution matrix before integrating the dashboard.

---

# 26. Step 5 Acceptance Criteria

Step 5 is complete only when all of these are true:

### MUST

- [ ] Step 4 decision package can trigger Step 5.
- [ ] Every action passes a fresh eligibility/guardrail check.
- [ ] Execution is idempotent.
- [ ] `MONITOR` performs no provider mutation.
- [ ] `ESCALATE` creates a durable escalation record.
- [ ] `STOP` prevents automated execution.
- [ ] `ONE_TIME_RECOVERY` creates a real Razorpay Test Mode Payment Link when eligible.
- [ ] Payment Link external ID is persisted.
- [ ] Execution result is persisted.
- [ ] Provider errors are classified.
- [ ] Unknown outcomes are reconciled rather than blindly replayed.
- [ ] Secrets are never logged.
- [ ] Automated tests cover critical negative cases.

### SHOULD

- [ ] `MANUAL_CHARGE` eligibility is implemented.
- [ ] Lightweight execution worker is implemented.
- [ ] Execution latency and failure metrics are recorded.

### NICE

- [ ] Beautiful execution timeline UI.
- [ ] LLM recommendation vs policy decision side-by-side.
- [ ] Human-readable action explanations.
- [ ] One-click local demo scenario runner.

---

# 27. Step 5 Hard Gate

Do **not** start Step 6 until this exact flow works:

```text
Step 4 decision
      ↓
fresh eligibility check
      ↓
ONE_TIME_RECOVERY
      ↓
execution idempotency key
      ↓
Razorpay Test Mode Payment Link created
      ↓
external Payment Link ID persisted
      ↓
execution status = CREATED
      ↓
duplicate execution attempt
      ↓
NO second Payment Link
```

And independently:

```text
customer_opt_out = true
      ↓
STOP
      ↓
NO Razorpay mutation
```

And:

```text
UNKNOWN diagnosis
      ↓
ESCALATE
      ↓
NO Razorpay mutation
```

These three proofs establish that Vasooli can **act, refuse to act, and route to humans safely**.

---

# 28. Step 5 Deliverables

At the end of Step 5, the repository should contain:

```text
1. Execution dispatcher
2. Eligibility/guardrail layer
3. Idempotent execution layer
4. Razorpay Test Mode client
5. Payment Link action
6. Monitor action
7. Escalate action
8. Stop action
9. Optional manual-charge path
10. Execution database tables
11. Error/reconciliation handling
12. Automated execution tests
13. Demo scenario scripts
14. Step 5 notes / what broke
```

---

# 29. Step 5 → Step 6 Contract

Step 5 must hand Step 6 a clean execution record:

```json
{
  "execution_id": "exec_123",
  "decision_id": "dec_123",
  "subscription_id": "sub_123",
  "action": "ONE_TIME_RECOVERY",
  "status": "CREATED",
  "provider": "razorpay_test",
  "external_id": "plink_xxx",
  "amount": 99900,
  "currency": "INR",
  "requested_at": "..."
}
```

Step 6 then verifies:

```text
Was it actually paid?
Was money actually collected?
Did subscription state change?
How much revenue should be counted?
```

**Step 5 never turns `CREATED` into `RECOVERED` just because the API request succeeded.**

---

# 30. Final Principle

The most important rule in Step 5:

> **An accepted API request is an execution result, not a recovery result.**

Vasooli earns the right to say **"₹999 recovered"** only after Step 6 finds actual payment evidence.

That distinction is central to the credibility of the entire build.
