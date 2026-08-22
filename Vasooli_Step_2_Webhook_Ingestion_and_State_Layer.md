# Vasooli — Step 2: Webhook Ingestion & State Layer

### Razorpay AI Buildathon — Track 03: AI Revenue Recovery

> **Status:** MUST / Core Foundation
>
> **Goal:** Turn the Step 1 webhook proof into a trustworthy ingestion layer that securely verifies Razorpay webhooks, deduplicates events, tolerates out-of-order delivery, persists events and subscription state in SQLite, and exposes a reliable internal state that later steps can consume.
>
> **Step 2 must NOT implement:** diagnosis, recovery scoring, LLM reasoning, recovery actions, Payment Links, batch simulation, or the final dashboard.

---

## 1. Step Objective

Step 1 proved:

```text
Razorpay Test Mode
      ↓
Test Subscription
      ↓
Triggered failure
      ↓
subscription.pending
      ↓
Webhook reaches Vasooli
```

Step 2 turns that proof into a reliable financial-event ingestion layer:

```text
Razorpay webhook
      ↓
Read raw request body
      ↓
Verify HMAC signature
      ↓
Extract event ID
      ↓
Deduplicate
      ↓
Persist immutable event
      ↓
Normalize relevant payload
      ↓
Reconcile current subscription state
      ↓
Persist state transition / snapshot
      ↓
Return fast 2xx
```

### Step 2 is complete only when all of these are demonstrated:

- A genuine Razorpay webhook passes signature verification.
- A deliberately invalid signature is rejected.
- The same webhook event delivered twice is processed only once.
- Duplicate delivery still receives a safe HTTP response and does not trigger duplicate business processing.
- Events can arrive out of order without corrupting the current subscription state.
- Raw event data is persisted for audit/debugging.
- Current subscription state is persisted separately from the immutable event log.
- The database can answer: **"What is the latest known state of subscription X, and which Razorpay event(s) led us there?"**

---

## 2. Scope

### MUST

- FastAPI webhook endpoint from Step 1 retained
- Read raw request body before JSON transformation
- Verify `X-Razorpay-Signature` using the configured webhook secret
- Read `x-razorpay-event-id`
- Reject or safely ignore malformed/unauthenticated requests
- Persist every accepted webhook event exactly once by event ID
- Store enough metadata to reproduce/debug processing
- Parse event type and subscription/payment/invoice identifiers where available
- Maintain a subscription state table/snapshot
- Handle duplicate deliveries safely
- Handle out-of-order events safely
- Reconcile current state from authoritative data rather than assuming arrival order
- Use transactions around event ingestion + state update
- Return HTTP 2xx quickly after safe persistence/queueing boundary
- Add basic automated tests for signature, deduplication, and ordering

### SHOULD

- Store event processing status separately from business state
- Store `received_at` and event timestamp where available
- Store raw payload as JSON
- Store a normalized subset for quick queries
- Add a small reconciliation helper that can fetch the current Razorpay resource when local state is ambiguous
- Add structured logging with correlation/event IDs
- Add a replay-safe internal processing function for previously stored events

### NOT part of Step 2

- Failure diagnosis categories such as `INSUFFICIENT_FUNDS`
- Recovery probability/model
- LLM explanation
- Policy engine
- `MONITOR`, `ONE_TIME_RECOVERY`, `MANUAL_CHARGE`, `ESCALATE`, or `STOP`
- Payment Link creation
- Subscription recovery execution
- Synthetic 500–2,000 record generation
- Final analytics/dashboard UI
- Production hosting

---

## 3. Source-of-Truth Rules

These rules are non-negotiable because this is a financial workflow.

### Rule 1 — Webhook event log is immutable

Once a webhook event has been accepted and persisted, do not overwrite its original payload.

```text
webhook_events
      ↓
append-only record
```

If later processing changes an interpretation, create/update a separate normalized state record instead.

### Rule 2 — Event arrival order is not business truth

Never implement:

```text
pending received after charged
→ therefore subscription must be pending
```

Instead:

```text
incoming event
      ↓
compare with current known state
      ↓
reconcile using authoritative subscription/payment data when needed
```

Razorpay webhook delivery can be duplicated and events can arrive out of order, so the application must be designed around those properties.

### Rule 3 — Event ID is the idempotency key for ingestion

Use:

```text
x-razorpay-event-id
```

as the unique external event identifier.

The database must enforce uniqueness, not just application code.

### Rule 4 — Internal database IDs are not Razorpay IDs

Keep both:

```text
id                → local UUID / integer PK
razorpay_event_id → external unique event ID
subscription_id   → Razorpay subscription ID
payment_id        → Razorpay payment ID
invoice_id        → Razorpay invoice ID
```

Never overload one column for multiple identifier types.

---

## 4. Recommended Project Structure

Expand the Step 1 skeleton to:

```text
vasooli/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   │
│   ├── api/
│   │   └── webhooks.py
│   │
│   ├── db/
│   │   ├── database.py
│   │   ├── models.py
│   │   └── repositories.py
│   │
│   ├── webhook/
│   │   ├── signature.py
│   │   ├── parser.py
│   │   ├── processor.py
│   │   └── reconciliation.py
│   │
│   └── schemas/
│       └── webhook.py
│
├── tests/
│   ├── test_signature.py
│   ├── test_deduplication.py
│   ├── test_webhook_processing.py
│   └── test_ordering.py
│
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

Keep the boundaries clean:

```text
api
 ↓
webhook processor
 ↓
repositories / state reconciliation
 ↓
database
```

Do not put all webhook logic inside `main.py`.

---

## 5. Dependencies

Add only what Step 2 needs.

### `requirements.txt`

```text
fastapi
uvicorn[standard]
python-dotenv
sqlalchemy
httpx
pytest
pytest-asyncio
```

Optional:

```text
pydantic-settings
```

Use standard-library `hmac` + `hashlib` for signature verification. Do not add an extra cryptography dependency for this requirement.

---

## 6. Environment Configuration

Recommended variables:

```text
RAZORPAY_KEY_ID=rzp_test_xxxxxxxxx
RAZORPAY_KEY_SECRET=xxxxxxxxxxxxxxxx
RAZORPAY_WEBHOOK_SECRET=xxxxxxxxxxxxxxxx
DATABASE_URL=sqlite:///./vasooli.db
```

Never expose any secret through:

- logs
- exception messages
- API responses
- GitHub
- screenshots
- README
- frontend source

The webhook secret is separate from the API secret. Do not assume they are interchangeable.

---

## 7. Database Design

For Step 2, use **SQLite + SQLAlchemy**.

Keep the schema deliberately small.

### Table A — `webhook_events`

Purpose: immutable external event journal.

Recommended fields:

```text
id                         local primary key
razorpay_event_id          unique external event ID
event_type                 e.g. subscription.pending
payload_json               full raw JSON payload
signature                  received X-Razorpay-Signature
received_at                local ingestion timestamp
provider_event_created_at event timestamp if available
processing_status          RECEIVED / PROCESSED / FAILED / IGNORED
processing_error           nullable error text
generated_subscription_id  parsed subscription ID if present
generated_payment_id       parsed payment ID if present
generated_invoice_id       parsed invoice ID if present
```

Do not store secrets in this table.

### Table B — `subscriptions`

Purpose: current normalized subscription snapshot.

Recommended fields:

```text
id                        local primary key
razorpay_subscription_id  unique Razorpay subscription ID
status                    active / pending / halted / etc.
plan_id                   Razorpay plan ID
customer_id               Razorpay customer ID if available
amount                    normalized amount representation
currency                  INR / etc.
current_period_start     nullable
current_period_end       nullable
latest_event_id           latest event used for this snapshot
state_version             integer revision counter
last_reconciled_at        timestamp
updated_at                timestamp
```

Do not treat this table as an immutable audit log. It is a **current-state projection**.

### Table C — `state_transitions`

Purpose: trace how the local projection changed.

Recommended fields:

```text
id
subscription_id
razorpay_event_id
previous_status
new_status
reason_event_type
transitioned_at
reconciliation_source
```

This table will be very useful later for the pitch audit trail.

### Optional Table D — `processing_locks`

Do NOT add this unless tests reveal a real concurrency problem. SQLite plus a unique event ID is enough for Step 2's scope.

---

## 8. Signature Verification

### Required verification sequence

The webhook endpoint must:

1. Read the body as raw bytes.
2. Read `X-Razorpay-Signature`.
3. Compute HMAC-SHA256 using `RAZORPAY_WEBHOOK_SECRET`.
4. Compare the calculated digest with the received signature using a constant-time comparison.
5. Reject the request before parsing/processing if verification fails.

Conceptually:

```python
expected = hmac.new(
    webhook_secret.encode(),
    raw_body,
    hashlib.sha256,
).hexdigest()

valid = hmac.compare_digest(expected, received_signature)
```

### Important

Do **not** do:

```python
json.loads(body)
json.dumps(parsed_body)
verify_signature(serialized_again)
```

because formatting changes can alter the signed byte sequence.

Verify the **original raw request body**.

### Test cases

```text
valid signature       → accepted
missing signature     → rejected
wrong signature       → rejected
modified payload      → rejected
same payload + valid signature → accepted once
```

---

## 9. Event-ID Deduplication

### Required behavior

Incoming request:

```text
x-razorpay-event-id = evt_123
```

Processing:

```text
Does evt_123 already exist?
        ↓
YES → do not execute business processing again
NO  → persist + process
```

### Database constraint

Create:

```text
UNIQUE(razorpay_event_id)
```

Do not rely only on:

```python
if event_id not in cache:
```

because a process restart would lose the cache.

### Duplicate scenario to demonstrate

Send the exact same valid webhook twice.

Expected:

```text
Request 1 → event inserted → state processing runs once
Request 2 → duplicate detected → no second state transition
```

The second request should still receive a safe response so Razorpay does not keep retrying purely because we rejected a known duplicate.

---

## 10. Webhook Parsing

After signature verification, parse the JSON.

Do not create a giant Pydantic model for the entire Razorpay payload yet. We only need the fields necessary for Step 2.

Extract at minimum where available:

```text
event
account/entity information
subscription.id
subscription.status
subscription.plan_id
subscription.customer_id
subscription.amount
subscription.currency
payment.id
invoice.id
```

Also retain the entire raw JSON in `payload_json`.

### Reason

Razorpay payload structures differ across event families. Raw storage prevents us from losing information before Step 4/5 needs it.

---

## 11. Event Classes to Support in Step 2

The minimum set should support the subscription lifecycle we proved in Step 1 and the verification flow needed later.

### MUST parse and persist

```text
subscription.pending
subscription.halted
subscription.charged
```

### SHOULD support early if easy

```text
subscription.activated
subscription.cancelled
```

### Payment events

Do not make payment events a separate architectural system yet. Persist them in the same `webhook_events` table and extract identifiers if present.

For later verification, be prepared to ingest payment lifecycle events such as:

```text
payment.authorized
payment.captured
payment.failed
```

If a particular test flow does not generate an event in Step 2, do not invent it. Capture what Razorpay actually sends and expand support during Step 5/6.

---

## 12. State Reconciliation Model

The key design decision:

> **Webhook = trigger, current provider state = truth for reconciliation.**

Do not let a webhook event blindly overwrite the local subscription state if the incoming event is stale.

### Recommended flow

```text
Webhook arrives
      ↓
Signature verified
      ↓
Event deduped
      ↓
Extract subscription ID
      ↓
Load current local subscription
      ↓
Determine whether event can safely update projection
      ↓
If ambiguous/stale → fetch current Razorpay subscription
      ↓
Write reconciled state
      ↓
Write state transition if changed
```

### Example

Suppose local state says:

```text
subscription = sub_123
status = halted
```

Then an older `subscription.pending` event arrives.

Do **not** blindly do:

```text
halted → pending
```

Instead:

```text
pending event
     ↓
provider state check
     ↓
halted is still current
     ↓
keep halted
```

This is the behavior we later need for trustworthy recovery decisions.

---

## 13. Ordering Strategy

Do not try to build a complicated distributed event-ordering engine for the hackathon.

Use a simple strategy:

### Level 1 — event timestamp, when available

Compare provider event timestamps as a first signal.

### Level 2 — current provider state

If timestamps are ambiguous or state transition is potentially stale, reconcile with Razorpay's current resource state.

### Level 3 — database projection

Only update the local projection when the reconciled state is newer / authoritative.

### State transition protection

A safe abstraction:

```python
reconcile_subscription(
    subscription_id,
    incoming_event,
) -> ReconciledSubscriptionState
```

The function should answer:

```text
current provider state
local state
new local state required?
why?
source event ID
```

---

## 14. Processing Transaction

The event ingestion path should behave approximately like:

```text
BEGIN TRANSACTION
    ↓
insert webhook_events
    ↓
if duplicate → safe no-op
    ↓
extract identifiers
    ↓
reconcile subscription
    ↓
update subscriptions
    ↓
insert state_transitions if state changed
COMMIT
```

If the transaction fails:

```text
ROLLBACK
```

Do not leave:

```text
webhook_events = inserted
subscription    = not updated
```

without recording that processing failed and can be retried.

### Important nuance

Do not hold a long-running transaction while calling an external Razorpay API.

Prefer:

```text
persist event
      ↓
short DB transaction
      ↓
perform reconciliation fetch if required
      ↓
short DB transaction for projection update
```

Keep the architecture simple enough for SQLite.

---

## 15. Fast Webhook Response

Razorpay webhook handlers should respond quickly.

Do NOT perform this full chain before returning HTTP response:

```text
Webhook
 ↓
LLM
 ↓
long Razorpay fetches
 ↓
ML scoring
 ↓
Payment Link creation
 ↓
return 200
```

Step 2 should target:

```text
receive
 ↓
verify
 ↓
dedupe
 ↓
persist enough state
 ↓
return 2xx
```

Heavy work will become asynchronous in later steps.

For Step 2, an `asyncio.create_task()`-style background shortcut is acceptable only for local development/tests; do not treat it as production-grade queue infrastructure.

---

## 16. Error Handling Matrix

| Situation | HTTP behavior | DB behavior | Business processing |
|---|---|---|---|
| Valid new event | 2xx | Persist | Process/reconcile |
| Valid duplicate event | 2xx | Keep original; optionally record duplicate attempt elsewhere | Do not process twice |
| Missing signature | 4xx | Do not persist as accepted event | None |
| Invalid signature | 4xx | Do not persist as accepted event | None |
| Invalid JSON | 4xx | Do not create state projection | None |
| Valid event but unknown event type | 2xx | Persist raw event | Mark unsupported/ignored |
| DB temporary failure | 5xx | No false success | Allow provider redelivery |
| Provider reconciliation fetch fails | 5xx or safe queued processing | Persist event as received / pending processing | Do not fabricate state |

The important principle is:

> **Never return success while pretending business processing succeeded if the event was lost.**

---

## 17. Logging

Use structured logs where practical.

Minimum fields:

```text
request_id
razorpay_event_id
event_type
subscription_id
payment_id
invoice_id
processing_status
processing_duration_ms
```

Never log:

```text
RAZORPAY_KEY_SECRET
RAZORPAY_WEBHOOK_SECRET
full Authorization headers
sensitive customer/payment details unnecessarily
```

For development, a useful log line is:

```text
[event=evt_123] [type=subscription.pending] [subscription=sub_abc] [status=PROCESSED]
```

---

## 18. API Endpoints

Keep Step 2 endpoints minimal.

### Health

```text
GET /health
```

Expected:

```json
{"status":"ok"}
```

### Razorpay webhook

```text
POST /webhooks/razorpay
```

### Debug endpoint — local development only

Optional:

```text
GET /debug/subscriptions/{subscription_id}
```

Return sanitized local state only.

**Do not expose raw secrets or the full webhook payload publicly.**

This endpoint should be removed or protected before any public deployment.

---

## 19. Repository Layer

Keep DB operations behind repository functions so Step 4/5 does not depend on raw SQL.

Suggested functions:

```python
get_event_by_razorpay_id(event_id)
create_webhook_event(...)
mark_event_processed(event_id)
mark_event_failed(event_id, error)
get_subscription(subscription_id)
upsert_subscription(...)
create_state_transition(...)
get_latest_subscription_state(subscription_id)
```

Later:

```text
Step 4 → repository reads become features
Step 5 → repository writes become recovery-state updates
Step 6 → repository reads power dashboard metrics
```

---

## 20. State Machine — Keep It Explicit

Do not yet build a complex workflow engine. Define an enum / constant set.

For the subscription projection, support at least:

```text
created
active
pending
halted
cancelled
completed
unknown
```

The exact provider state values observed in Test Mode should be recorded rather than invented.

### Important

Do not equate:

```text
halted == permanently unrecoverable
```

or:

```text
pending == payment will definitely recover
```

State tells us the lifecycle position; Step 4 will later decide what intervention, if any, is appropriate.

---

## 21. Testing Strategy

Step 2 needs real tests, not only manual Postman/curl checks.

### Test 1 — Valid signature

Input:

```text
valid payload
valid HMAC
```

Expected:

```text
2xx
webhook persisted
processing succeeds
```

### Test 2 — Invalid signature

Change one byte in the payload after calculating the original signature.

Expected:

```text
4xx
no accepted event inserted
no state change
```

### Test 3 — Missing signature

Expected:

```text
4xx
no state change
```

### Test 4 — Duplicate event

Send the exact same event twice.

Expected:

```text
first → state transition once
second → duplicate/no-op
```

Database expectation:

```text
COUNT(razorpay_event_id = X) = 1
```

### Test 5 — Out-of-order event

Construct:

```text
Event A → pending
Event B → halted
Event A again → pending
```

Expected final state:

```text
halted
```

assuming provider reconciliation confirms `halted` is current.

### Test 6 — Unknown event

Send a valid Razorpay-signed event type the processor does not yet support.

Expected:

```text
persist raw event
mark unsupported/ignored
no subscription corruption
```

### Test 7 — Restart safety

Process an event, restart the application, send the same event again.

Expected:

```text
dedup still works
```

This proves idempotency is database-backed, not an in-memory trick.

---

## 22. Test Fixtures

Create small JSON fixtures under:

```text
tests/fixtures/
├── subscription_pending.json
├── subscription_halted.json
├── subscription_charged.json
├── duplicate_event.json
└── unknown_event.json
```

Never store real customer/payment secrets in fixtures.

Use redacted or synthetic IDs.

For signature tests, generate signatures dynamically during the test using a test-only webhook secret.

---

## 23. Acceptance Checklist

### Security

- [ ] Raw request body is used for signature verification.
- [ ] HMAC-SHA256 verification implemented.
- [ ] Invalid signature rejected.
- [ ] Missing signature rejected.
- [ ] Secrets never appear in logs or Git.

### Idempotency

- [ ] `x-razorpay-event-id` captured.
- [ ] Event ID has a database UNIQUE constraint.
- [ ] Duplicate webhook cannot create duplicate state transitions.
- [ ] Deduplication survives process restart.

### State

- [ ] `webhook_events` table exists.
- [ ] `subscriptions` table exists.
- [ ] `state_transitions` table exists.
- [ ] Current subscription status is queryable.
- [ ] Raw webhook payload remains available for audit/debugging.

### Ordering

- [ ] Out-of-order delivery does not blindly overwrite current state.
- [ ] Provider reconciliation is available for ambiguous/stale events.
- [ ] Final state can be explained from event history + reconciliation.

### Reliability

- [ ] Webhook endpoint returns quickly.
- [ ] DB failure does not produce a false successful ingestion.
- [ ] Failed processing can be retried safely.

### Tests

- [ ] Valid signature test passes.
- [ ] Invalid signature test passes.
- [ ] Duplicate test passes.
- [ ] Out-of-order test passes.
- [ ] Unknown-event test passes.
- [ ] Restart/idempotency test passes.

### Integration proof

- [ ] Step 1's real `subscription.pending` webhook works through the new handler.
- [ ] A real Test Mode event appears in `webhook_events`.
- [ ] Corresponding subscription snapshot appears in `subscriptions`.
- [ ] A state transition is recorded.

---

## 24. Demo Evidence to Capture

Before leaving Step 2, capture these screenshots/logs for the README/build log.

### Evidence A — Valid webhook

```text
Event ID: evt_xxx
Event Type: subscription.pending
Signature: verified
Processing: PROCESSED
```

### Evidence B — Duplicate

```text
Event ID: evt_xxx
First delivery: PROCESSED
Second delivery: DUPLICATE / NO-OP
```

### Evidence C — Database

Show:

```text
webhook_events
subscriptions
state_transitions
```

### Evidence D — Out-of-order handling

Show a test where an older event arrives after a newer state and the final state remains correct.

### Evidence E — Security failure

Show:

```text
invalid signature → rejected
```

Do not show secret values in any screenshot.

---

## 25. Failure Scenarios to Intentionally Test

At least one real failure should be documented for the buildathon's later:

> **"What broke, and how did you get out?"**

Good Step 2 candidates:

### Failure A — Duplicate webhook

```text
Same event delivered twice
        ↓
Duplicate state mutation detected
        ↓
Unique constraint + idempotent processing added
```

### Failure B — Out-of-order event

```text
Older event arrives after newer state
        ↓
Naive implementation would regress state
        ↓
Provider-state reconciliation added
```

### Failure C — Invalid signature

```text
Payload modified / wrong secret
        ↓
Signature mismatch
        ↓
Request rejected before processing
```

Use whichever issue genuinely occurs during development. Never manufacture a failure story.

---

## 26. Step 2 Definition of Done

Step 2 is **DONE** when this complete scenario works:

```text
Razorpay Test Mode
      ↓
subscription.pending webhook
      ↓
POST /webhooks/razorpay
      ↓
Read raw body
      ↓
Verify HMAC signature
      ↓
Read x-razorpay-event-id
      ↓
Database uniqueness check
      ↓
Persist immutable event
      ↓
Extract subscription ID
      ↓
Reconcile current subscription state
      ↓
Update subscriptions snapshot
      ↓
Record state transition
      ↓
Return 2xx quickly
```

And these safety scenarios also work:

```text
invalid signature → reject
same event twice → process once
old event after new event → final state remains correct
application restart → dedup still works
```

### Final Step 2 gate

Do not move to Step 3 until:

```text
SECURITY          ✅
IDEMPOTENCY       ✅
STATE PERSISTENCE ✅
ORDER TOLERANCE   ✅
TESTS             ✅
REAL WEBHOOK      ✅
```

Step 3 can then safely consume the subscription/event state without having to solve webhook correctness at the same time.

---

## 27. What Step 3 Is Allowed to Assume

After Step 2 is complete, later modules may assume:

```text
subscription state is available
webhook events are persisted
accepted events are authenticated
duplicate events are safe
state is not blindly event-order dependent
```

Step 3 should **not** reimplement webhook verification or database ingestion.

Its only job will be synthetic historical data generation and evaluation inputs.

---

## 28. Final Principle

> **Step 2 is infrastructure, not intelligence.**
>
> If Vasooli cannot reliably determine what Razorpay actually told it, every AI decision made later is built on sand.
>
> Get the event journal, signature verification, idempotency, and state projection correct first. Then build the intelligence layer on top.
