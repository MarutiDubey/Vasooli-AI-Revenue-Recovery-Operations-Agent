# Vasooli — AI Buildathon Execution Manager
## Professional Execution, Winning Strategy & Final Delivery Playbook
### Razorpay AI Buildathon 2026 — Track 03: AI Revenue Recovery

---

# 0. Executive Directive

## Project

**Vasooli — AI Revenue Recovery Agent**

## Selected Track

**Track 03 — AI Revenue Recovery**

## Core problem

Failed recurring payments create revenue at risk. The difficult part is not merely detecting failure; the merchant needs to decide whether to monitor, recover, escalate, or stop, then verify whether the intervention actually recovered money.

## Core product promise

> **Vasooli detects failed recurring subscription payments, diagnoses the recovery situation, selects a bounded intervention, executes the permitted recovery workflow, verifies the actual outcome, and measures recovered revenue across a batch with an audit trail and honest exception reporting.**

## Primary objective

Build the strongest **credible, complete, measurable, reliable** Track 03 submission possible within the available time and with a ₹0 development-budget constraint.

## Winning philosophy

Do not optimize for the largest number of features.

Optimize for:

```text
Problem quality
+
Working product
+
Meaningful AI
+
Strong engineering
+
Measured value
+
Safe money actions
+
Honest evidence
+
Excellent 5-minute story
```

The objective is to make a judge believe:

> **"This builder understood the business problem, built the difficult parts correctly, knows where AI belongs and where it does not, measured the outcome honestly, and can be trusted around financial workflows."**

---

# 1. What Razorpay Is Actually Looking For

Razorpay's current Buildathon page states that the program is student-only, offers a 6- or 12-month AI Builder Internship, and is in-person in Bangalore from September. It explicitly says there is no resume screening and emphasizes building something real, a public repository, a five-minute pitch, and the architecture.  
Source: https://razorpay.com/buildathon/ citeturn145320view0

The page describes Track 03 as:

> "Find revenue that’s slipping away and win it back."

The track requires an agent that:

1. detects revenue at risk,
2. determines the right intervention,
3. executes a bounded recovery workflow,
4. and shows measured money recovered across a batch with compliant escalation, stopping rules, and an audit trail.  
Source: https://razorpay.com/buildathon/ citeturn145320view0

The Buildathon page also states that they are looking at:

- Problem taste
- Build quality
- AI judgment
- Failure recovery

and says they read the work rather than screening on the resume.  
Source: https://razorpay.com/buildathon/ citeturn145320view0

### Management conclusion

Every implementation decision should map to at least one of those signals.

| What we build | Signal demonstrated |
|---|---|
| Revenue-at-risk problem | Problem taste |
| Razorpay integration | Build quality |
| Webhook verification/idempotency | Build quality |
| Bounded policy engine | AI judgment |
| LLM non-authoritative architecture | AI judgment |
| Real recovery workflow | Execution |
| Batch evaluation | Evidence |
| Exception list | Honesty |
| Real broken-case fix | Failure recovery |
| Clean pitch | Communication |

---

# 2. Why Track 03 Remains the Final Choice

The selected scope is:

```text
Track 03
    ↓
Failed Subscription / Recurring Payment Recovery
```

This is narrow enough to finish and broad enough to demonstrate:

```text
Detect
→ Diagnose
→ Decide
→ Execute
→ Verify
→ Measure
```

Razorpay's official Test Subscription documentation explicitly supports testing plans, subscriptions, authentication, simulated subsequent charges, charge failures, `subscription.pending`, `subscription.halted`, and related subscription webhooks.  
Source: https://razorpay.com/docs/payments/subscriptions/test/ citeturn420040search0

This gives the project a real payment-system foundation without requiring live-money processing.

---

# 3. Final Product Scope

## In scope

```text
Razorpay Test Mode
        ↓
Subscription lifecycle
        ↓
Failed recurring payment
        ↓
Webhook
        ↓
Diagnosis
        ↓
Recovery score
        ↓
Policy decision
        ↓
Bounded recovery action
        ↓
Outcome verification
        ↓
Revenue measurement
        ↓
Audit trail
```

## Supported actions

```text
MONITOR
ONE_TIME_RECOVERY
ESCALATE
STOP
NO_ACTION
```

Optional:

```text
MANUAL_CHARGE
```

## Explicitly out of scope

```text
Live-money processing
Production merchant onboarding
Replacing Razorpay's retry engine
Unlimited payment retries
Autonomous LLM-controlled money actions
Full CRM/helpdesk
Large-scale real Razorpay transaction generation
Real customer messaging infrastructure
Multi-domain revenue recovery
```

---

# 4. Final Architecture

```text
                    RAZORPAY TEST MODE
                           │
                           ↓
                    SUBSCRIPTION EVENT
                           │
                           ↓
             SIGNATURE VERIFICATION
                           │
                           ↓
                 EVENT-ID DEDUPLICATION
                           │
                           ↓
                 STATE RECONCILIATION
                           │
                           ↓
                       DETECT
                           │
                           ↓
                      DIAGNOSE
                           │
                  ┌────────┴────────┐
                  ↓                 ↓
           Recovery Score       UNKNOWN
                  ↓                 ↓
           Optional LLM        ESCALATE
           explanation             │
                  ↓                 │
                  └────────┬────────┘
                           ↓
                    POLICY ENGINE
                           │
         ┌───────┬─────────┼──────────┬────────┐
         ↓       ↓         ↓          ↓        ↓
      MONITOR  ONE-TIME  ESCALATE    STOP   NO_ACTION
               RECOVERY
                  ↓
            Razorpay API
                  ↓
              EXECUTION
                  ↓
               VERIFY
                  ↓
       ┌──────────┴──────────┐
       ↓                     ↓
 CASH RECOVERED       SUBSCRIPTION
                      REACTIVATED
       │                     │
       └──────────┬──────────┘
                  ↓
             MEASUREMENT
                  ↓
        AUDIT + EXCEPTIONS
```

---

# 5. Critical Razorpay Reality Checks

These are not optional assumptions; the integration must follow the current official documentation.

## 5.1 Test subscriptions

Razorpay's test subscription flow requires Test Mode API credentials, a plan, a subscription, subscription authentication, and subsequent test charges. Failed test charges can move a subscription to `pending` and trigger `subscription.pending`; exhausted retries can move it to `halted` and trigger `subscription.halted`.  
Source: https://razorpay.com/docs/payments/subscriptions/test/ citeturn420040search0

## 5.2 Subscription Links

Razorpay currently documents a 30 Subscription Links per business limit in Test Mode.  
Source: https://razorpay.com/docs/payments/subscriptions/create-subscription-links/ citeturn420040search1

## 5.3 Payment Links

Razorpay currently documents a 30 Payment Links per business limit in Test Mode. Payment Links are tested using controlled success/failure outcomes.  
Source: https://razorpay.com/docs/payments/payment-links/create/ citeturn420040search4

## 5.4 Payment Link semantics

A Payment Link is a one-time collection mechanism. It must not be represented as automatic subscription reactivation.

## 5.5 Webhooks

Razorpay states that webhook payloads in Test Mode reflect the Live/Test payload structure, signatures use the configured webhook secret and `X-Razorpay-Signature`, and webhook processing must account for idempotency and event ordering.  
Source: https://razorpay.com/docs/webhooks/validate-test/ citeturn420040search2

## 5.6 Payment Link verification

Razorpay documents `payment_link.paid` webhook events containing the payment-link/order/payment context.  
Source: https://razorpay.com/docs/webhooks/payment-links/ citeturn420040search8

## 5.7 Subscription webhook payloads

Razorpay documents that subscription webhook payloads contain the subscription entity and can contain a payment entity when a payment attempt preceded the event.  
Source: https://razorpay.com/docs/webhooks/subscriptions/ citeturn420040search5

### Rule

Never build around memory when the provider documentation can answer the question.

---

# 6. Definition of "Winning"

A winning submission does not need to be the largest system.

A strong submission should make the judge answer "yes" to all of these:

### Problem

- [ ] The problem is real.
- [ ] Revenue leakage is obvious.
- [ ] The chosen slice is focused.
- [ ] The solution addresses an actual merchant workflow.

### Product

- [ ] The system runs.
- [ ] The core loop is complete.
- [ ] A real Razorpay Test Mode flow is demonstrated.
- [ ] The UI clearly communicates value.

### AI

- [ ] AI is genuinely useful.
- [ ] AI is not decorative.
- [ ] Deterministic logic is used where it is safer.
- [ ] LLM has bounded authority.
- [ ] The architecture explains where AI is intentionally not used.

### Financial credibility

- [ ] Money-at-risk is quantified.
- [ ] Verified cash recovery is quantified.
- [ ] Subscription reactivation is separately quantified.
- [ ] Exceptions are visible.
- [ ] No cherry-picking.

### Engineering

- [ ] Webhook signature verification
- [ ] Idempotency
- [ ] Out-of-order tolerance
- [ ] Reconciliation
- [ ] Error handling
- [ ] Audit trail
- [ ] Tests

### Failure recovery

- [ ] At least one genuine engineering failure is explained.
- [ ] Fix is demonstrated.
- [ ] The fix prevents recurrence.

---

# 7. Project Execution Model

Use a professional software delivery loop:

```text
PLAN
  ↓
IMPLEMENT
  ↓
TEST
  ↓
PROVE
  ↓
MEASURE
  ↓
DOCUMENT
  ↓
DEMO
  ↓
REVIEW
```

For each major feature:

```text
Feature
→ acceptance criteria
→ implementation
→ test
→ evidence
→ documentation
```

Never mark a feature complete because "the code exists."

A feature is complete only when it is:

```text
implemented
+
tested
+
observable
+
documented
```

---

# 8. Seven-Step Execution Plan

## STEP 1 — Setup & Foundation Proof

Goal:

```text
Razorpay Test Subscription
        ↓
Simulated failure
        ↓
subscription.pending
        ↓
Vasooli webhook receives event
```

Hard gate:

- Test credentials work
- Plan exists
- Subscription exists
- Test failure can be triggered
- Webhook is received

Do not build AI before this works.

---

## STEP 2 — Webhook Ingestion & State Layer

Goal:

```text
Webhook
→ verify
→ deduplicate
→ persist
→ reconcile
→ stable state
```

Hard gate:

- HMAC verification
- `x-razorpay-event-id` deduplication
- out-of-order tolerance
- subscription/event records
- state reconciliation

---

## STEP 3 — Synthetic Dataset Generator

Goal:

```text
500–2,000 reproducible records
```

Requirements:

- fixed seed
- configurable distribution
- input/output separation
- no leakage
- edge cases
- UNKNOWN cases
- metadata

Hard gate:

```text
same seed
→ same dataset
```

---

## STEP 4 — Diagnose + Decide Engine

Goal:

```text
event
→ normalized reason
→ recovery score
→ policy
→ action
```

Requirements:

- UNKNOWN fallback
- explainable score
- deterministic policy
- guardrails
- optional LLM
- LLM never final authority

Hard gate:

```text
LLM recommendation
≠
final money decision
```

Policy wins.

---

## STEP 5 — Execute Recovery Actions

Goal:

```text
decision
→ bounded execution
→ durable execution record
```

Primary actions:

```text
MONITOR
ONE_TIME_RECOVERY
ESCALATE
STOP
NO_ACTION
```

Optional:

```text
MANUAL_CHARGE
```

Hard gate:

- execution idempotent
- fresh eligibility check
- Payment Link can be created
- duplicate execution cannot create duplicate action
- STOP/ESCALATE cannot mutate payment state

---

## STEP 6 — Verify + Measure + Dashboard

Goal:

```text
execution
→ verified provider evidence
→ financial outcome
→ dashboard
```

Two separate metrics:

```text
₹ Cash Recovered
₹ Subscription Revenue Reactivated
```

Hard gate:

```text
API request ≠ recovery
```

Only verified provider evidence creates recovery credit.

---

## STEP 7 — Batch Evaluation + Demo Prep

Goal:

```text
final batch
→ final metrics
→ final repo
→ final video
→ final form
→ final review
→ submit
```

No major new features.

---

# 9. Engineering Standards

This project should be treated like a small production system, not a notebook demo.

## 9.1 Code quality

- typed Python where practical
- Pydantic request/response models
- clear module boundaries
- no giant `main.py`
- no duplicated provider logic
- constants/configuration centralized
- meaningful error classes
- structured logging

## 9.2 Money

Use integer minor units:

```text
₹999
→ 99900 paise
```

Never use floating point for financial calculations.

## 9.3 Configuration

Use environment variables:

```text
RAZORPAY_KEY_ID
RAZORPAY_KEY_SECRET
RAZORPAY_WEBHOOK_SECRET
LLM_API_KEY
DATABASE_URL
```

Never commit secrets.

## 9.4 API layer

Separate:

```text
Razorpay client
business logic
policy logic
database logic
```

Do not spread Razorpay API calls throughout the application.

---

# 10. Testing Strategy

Use four layers.

## Layer 1 — Unit tests

Examples:

```text
failure normalizer
recovery score
policy guardrails
amount calculations
exception classification
```

## Layer 2 — Integration tests

Examples:

```text
webhook → DB
decision → execution
execution → outcome
```

## Layer 3 — Provider Test Mode

Use real Razorpay Test Mode for:

```text
subscription
failure
webhook
payment link
success/failure outcome
```

## Layer 4 — End-to-end

Complete:

```text
failure
→ webhook
→ diagnosis
→ decision
→ execution
→ verification
→ dashboard
```

This is the strongest demo proof.

---

# 11. Golden Demo Scenarios

Keep three scenarios.

## Scenario A — Successful Recovery

```text
failed subscription
→ pending
→ diagnosis
→ ONE_TIME_RECOVERY
→ Payment Link
→ successful test payment
→ verified cash recovery
```

## Scenario B — Safe Refusal

```text
customer opted out
→ STOP
→ no Payment Link
→ audit trail
```

## Scenario C — AI vs Policy

```text
LLM:
"Recovery recommended"

Policy:
"STOP"

Reason:
hard guardrail

Final:
STOP
```

These three scenarios demonstrate:

```text
CAPABILITY
+
SAFETY
+
AI JUDGMENT
```

---

# 12. What Should Be Real vs Synthetic

This distinction must be intentional.

## Real Razorpay Test Mode

Use for:

- subscription lifecycle
- webhook
- failure event
- Payment Link creation
- test payment
- provider verification

Target:

```text
5–20 controlled flows
```

Not hundreds.

## Synthetic batch

Use for:

- 500–2,000 cases
- distribution
- decision evaluation
- recovery simulation
- exception analysis
- aggregate metrics

### Why

Provider test-mode limits exist; Razorpay currently documents 30 Payment Links and 30 Subscription Links per business in Test Mode.  
Sources: https://razorpay.com/docs/payments/payment-links/create/ and https://razorpay.com/docs/payments/subscriptions/create-subscription-links/

Therefore:

> **Real integration proves authenticity; synthetic scale proves the workflow's batch behavior.**

Do not pretend the synthetic batch is real payment traffic.

---

# 13. Data Quality Rules

Synthetic data must be realistic enough to test decisions without pretending to be real merchant data.

## Must include

- high-value subscriptions
- low-value subscriptions
- new customers
- long-tenure customers
- previous successful customers
- repeated failures
- unknown failures
- opt-outs
- explicit cancellations
- active/pending/halted states
- various attempt counts

## Must avoid

- contradictory fields
- impossible state combinations
- leakage
- hidden outcome fields in model input
- fake "real BFSI percentages"

---

# 14. AI Architecture

Use AI where it provides meaningful reasoning.

## Recommended

```text
Razorpay event
      ↓
Feature engine
      ↓
Recovery score
      ↓
Optional LLM explanation
      ↓
Deterministic policy
      ↓
Action
```

## Do NOT use LLM for

- opt-out enforcement
- cancellation enforcement
- maximum retries
- eligibility
- amount validation
- duplicate prevention
- secret handling
- final authorization of money actions

## Pitch message

> **"We deliberately kept financial guardrails deterministic. The model can recommend and explain, but it cannot override policy."**

This directly demonstrates AI judgment.

---

# 15. Recovery Policy Design

Policy precedence should be explicit.

Suggested order:

```text
1. Customer opt-out
2. Explicit mandate cancellation
3. Already recovered
4. Invalid/inconsistent state
5. High-value escalation threshold
6. Unsupported provider action
7. Unknown evidence
8. Recovery scoring
9. Default recovery action
```

Hard-stop rules must dominate model recommendations.

---

# 16. Financial Truth Model

The system must represent at least three states:

```text
At Risk
Recovered Cash
Recurring Revenue Reactivated
```

Example:

```text
₹999 at risk
↓
Payment Link paid
↓
₹999 cash recovered
↓
subscription remains halted
↓
₹0 recurring revenue reactivated
```

This is not a failure of the accounting model.

It is **correct business measurement**.

---

# 17. Metrics That Matter

## Core

```text
Revenue at Risk
Cash Recovered
Cash Recovery Rate
Subscription Revenue Reactivated
```

## Operational

```text
Cases Processed
Escalation Rate
Stop Rate
Verification Timeout Rate
Action Success Rate
```

## Reliability

```text
Duplicate Event Rate
Duplicate Action Prevention
Webhook Processing Latency
Provider Error Rate
Unknown Outcome Rate
```

## AI / Policy

```text
UNKNOWN Diagnosis Rate
LLM Override Rate
Guardrail Block Rate
Action Distribution
```

Do not overload the pitch with 20 metrics.

The dashboard can expose more; the pitch should emphasize the strongest 3–5.

---

# 18. Winning Metrics Strategy

The Buildathon explicitly wants measured money recovered across a batch.  
Source: https://razorpay.com/buildathon/ citeturn145320view0

Therefore the primary pitch metrics should be:

```text
₹ Revenue At Risk
₹ Cash Recovered
Recovery Rate
₹ Subscription Revenue Reactivated
Exceptions
```

Then:

```text
"What we could not recover — and why"
```

This makes the result credible.

---

# 19. Exception Strategy

An exception is not embarrassment.

An exception is evidence.

Show:

```text
Customer cancelled
→ STOP

Unknown signal
→ ESCALATE

Payment Link not paid
→ UNRECOVERED

Unsupported manual charge
→ ESCALATE

Provider timeout
→ RECONCILE
```

A sophisticated system knows when it cannot safely act.

---

# 20. Failure-Recovery Strategy

During development, maintain:

```text
docs/what-broke.md
```

For every genuine issue:

```text
Problem
Impact
Root cause
Fix
Test added
Final result
```

Strong examples if they actually occur:

```text
duplicate webhook
→ event-id dedup

out-of-order event
→ provider-state reconciliation

LLM unsafe recommendation
→ deterministic guardrail

provider timeout
→ UNKNOWN_OUTCOME + reconciliation

unsupported manual charge
→ eligibility gate + escalation
```

Never fabricate a failure.

---

# 21. Professional Project Management

Use a simple status board.

```text
BACKLOG
   ↓
READY
   ↓
IN PROGRESS
   ↓
TESTING
   ↓
VERIFIED
   ↓
DEMO READY
   ↓
FROZEN
```

A feature does not move to `VERIFIED` until its acceptance criterion passes.

## Priority tags

```text
P0 = submission-critical
P1 = strong differentiator
P2 = polish
P3 = optional
```

### P0

- Razorpay Test integration
- webhook security
- state reconciliation
- decision engine
- bounded execution
- verification
- batch metrics
- audit trail
- exceptions
- pitch

### P1

- AI explanation
- polished dashboard
- policy override visualization
- richer analysis

### P2

- animations
- advanced filtering
- visual polish
- extra charts

### P3

- extra agents
- voice
- additional recovery channels
- multi-tenant architecture

If time gets tight, cut P2/P3 first.

---

# 22. Scope Control

The biggest threat to winning is not lack of ideas.

It is scope explosion.

Do not suddenly add:

```text
Voice recovery
WhatsApp
Email automation
Multiple merchants
Fraud model
Checkout abandonment
B2B receivables
Agent-to-agent commerce
```

The project is:

> **Failed recurring subscription recovery.**

Depth beats breadth.

---

# 23. Repository Professionalism

Public repository should look intentional.

Recommended top-level structure:

```text
vasooli/
├── backend/
├── frontend/
├── scripts/
├── data/
├── reports/
├── docs/
├── tests/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
└── package.json
```

Avoid:

```text
final2.py
test_new.py
new_final_latest.py
working_final_v3/
```

Use meaningful module names.

---

# 24. README Winning Structure

```text
1. Vasooli
2. 30-second pitch
3. Problem
4. Why this problem matters
5. Solution
6. Architecture
7. Razorpay integration
8. AI architecture
9. Guardrails
10. Verification
11. Batch evaluation
12. Results
13. Exception analysis
14. Demo
15. What broke
16. Tech stack
17. Setup
18. Limitations
19. Future scope
```

A judge should understand the project by reading only the first 20–30% of the README.

---

# 25. Demo UX Strategy

The first screen should answer:

```text
How much revenue is at risk?
How much was recovered?
What remains unresolved?
```

Recommended dashboard header:

```text
REVENUE AT RISK       ₹X
CASH RECOVERED        ₹Y
SUBSCRIPTION RESTORED ₹Z
RECOVERY RATE         X%
EXCEPTIONS            N
```

Then:

```text
Recovery Cases
```

Then:

```text
Exception List
```

Then:

```text
Audit Timeline
```

---

# 26. Pitch Strategy

Razorpay explicitly asks for a five-minute pitch video.  
Source: https://razorpay.com/buildathon/ citeturn145320view0

Use:

```text
0:00–0:30 Problem
0:30–1:00 Product
1:00–2:15 Demo
2:15–3:15 AI judgment
3:15–4:15 Batch results
4:15–4:40 Failure
4:40–5:00 Close
```

Do not spend 2 minutes on the technology stack.

Show the product.

---

# 27. Pitch Narrative

## Opening

> Failed subscription payments are not one problem with one solution. Some should be monitored, some need intervention, some should be escalated, and some should be stopped entirely.

## Product

> Vasooli closes that loop.

## Demo

```text
failure
→ diagnosis
→ decision
→ action
→ verified recovery
```

## AI

> The model can reason, but policy owns money safety.

## Evidence

> We ran the system across a full batch instead of showing a cherry-picked success.

## Failure

> Here is what broke, how we diagnosed it, and how we fixed it.

## Close

> Vasooli does not just detect revenue leakage. It manages the recovery loop with evidence at every stage.

---

# 28. 5-Minute Video Rules

## Show

- working product
- real Test Mode event
- recovery decision
- guardrail
- verification
- batch metrics
- exception list

## Avoid

- long IDE typing
- installation commands
- irrelevant theory
- giant architecture animation
- raw logs for 2 minutes
- unsupported claims

---

# 29. Winning Differentiators

The differentiators should be **visible**, not merely mentioned.

## Differentiator 1 — Bounded money action

Show:

```text
LLM recommends
        ↓
Policy validates
        ↓
Action
```

## Differentiator 2 — Honest recovery accounting

Show:

```text
Cash recovered ≠ subscription reactivated
```

## Differentiator 3 — Exception intelligence

Show:

```text
₹X unrecovered
because:
...
```

## Differentiator 4 — Provider-aware architecture

Show:

```text
Razorpay retry engine
        ≠
Vasooli recovery orchestrator
```

## Differentiator 5 — Failure recovery

Show a real engineering failure and fix.

---

# 30. What Could Cause Disqualification / Severe Damage

Avoid:

```text
offense-capable fraud tooling
```

The Buildathon specifically states that the Risk Manager track is defense-only, but financial automation should still remain bounded and compliant.  
Source: https://razorpay.com/buildathon/ citeturn145320view0

For Vasooli, the biggest practical risks are:

- exposing API secrets
- claiming simulated money is real money
- claiming synthetic data is real merchant data
- unsafe autonomous payment behavior
- ignoring opt-out/cancellation
- duplicate money actions
- counting unverified actions as recovery
- fabricating metrics

---

# 31. Cost / Infrastructure Strategy

## Required spending

Target:

```text
₹0
```

for the core build.

## Core stack

```text
Python
FastAPI
SQLite
SQLAlchemy
React/Next.js
Razorpay Test Mode
Faker
pytest
```

## AI

LLM should be optional.

Possible approach:

```text
No LLM
→ core system still works

LLM available
→ explanation layer improves the demo
```

This guarantees that a failed/free-tier API does not destroy the submission.

## Hosting

Local-first.

Only deploy if:

```text
deployment improves the demo
```

Do not spend money for hosting purely for appearances.

---

# 32. Environment Strategy

Use three logical environments:

```text
LOCAL
TEST DEMO
FINAL DEMO
```

All use:

```text
Razorpay Test Mode
```

Keep credentials in environment variables.

Never use production credentials.

---

# 33. Reproducibility

Every final batch run must record:

```text
run_id
dataset_seed
dataset_version
policy_version
model/scorer version
git commit SHA
timestamp
configuration
```

Example:

```text
run_id = final_001
seed = 20260821
policy = v1.0
commit = abc123...
```

Then if a judge asks:

> "Where did this number come from?"

you can answer.

---

# 34. Final Evidence Package

Before submission, collect:

```text
docs/
├── architecture.md
├── problem-statement.md
├── what-broke.md
├── limitations.md
└── demo-script.md

reports/
├── final_metrics.md
├── final_batch_report.json
├── final_batch_report.csv
├── final_exceptions.csv
└── final_run_metadata.json

screenshots/
├── dashboard.png
├── audit-trail.png
└── recovery-result.png
```

Do not expose secrets in screenshots.

---

# 35. Final Review Gate

Run four reviews.

## Review A — Technical

Can the complete system run from clean startup?

## Review B — Financial

Can every recovered rupee be traced to evidence?

## Review C — AI

Can we explain exactly why AI is used and why it is not used in other places?

## Review D — Judge

Can someone understand the value within 60 seconds?

---

# 36. Judge Perspective Test

Read the project from the perspective of a Razorpay judge.

Ask:

### In 10 seconds

> What does this build do?

### In 30 seconds

> Why is it useful?

### In 60 seconds

> What is novel or thoughtful?

### In 2 minutes

> Is the AI actually doing something useful?

### In 3 minutes

> Does it work?

### In 4 minutes

> Do the numbers mean anything?

### In 5 minutes

> Do I trust this builder?

If the answer is "yes" throughout, the submission is strong.

---

# 37. Final Submission Form Strategy

Razorpay's Buildathon page currently emphasizes:

- public repository
- five-minute pitch
- architecture
- project/work over resume screening.  
Source: https://razorpay.com/buildathon/ citeturn145320view0

Therefore prioritize:

```text
WORK > RESUME
```

## Project name

Final:

> **Vasooli — AI Revenue Recovery Agent**

## What it solves

Use the real final product behavior.

Do not describe features that were not actually implemented.

## GitHub

Public and tested from a clean/incognito session.

## Pitch

Under five minutes.

## What broke

Real development story only.

---

# 38. Final "What Broke" Quality Standard

Bad:

> "We had some bugs and fixed them."

Good:

> "Razorpay webhooks can be delivered asynchronously and duplicate delivery must be handled. We initially treated the event as a one-time trigger, which could have caused duplicate recovery actions. We added event-ID deduplication and state reconciliation, then verified the behavior with duplicate and out-of-order test cases."

Only use this narrative if it accurately reflects what happened during development.

---

# 39. What We Should Never Claim

## Do not claim

```text
"₹5L recovered from real customers"
```

when it is synthetic/Test Mode.

Use:

```text
"₹X verified cash-recovery result in our evaluation/demo workflow"
```

and clearly label synthetic vs Test Mode evidence.

## Do not claim

```text
"Subscription reactivated"
```

after only a Payment Link payment.

## Do not claim

```text
"AI autonomously handles payments safely"
```

Instead:

```text
"AI recommends/explains; deterministic policy controls money actions."
```

---

# 40. Final Operational Checklist

## Product

- [ ] Step 1 complete
- [ ] Step 2 complete
- [ ] Step 3 complete
- [ ] Step 4 complete
- [ ] Step 5 complete
- [ ] Step 6 complete

## Quality

- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] End-to-end test passes
- [ ] Security audit passes
- [ ] No secrets in Git
- [ ] No fake data claims

## Evidence

- [ ] Final batch report
- [ ] Exception list
- [ ] Audit trail
- [ ] Dashboard screenshots
- [ ] Test Mode demo

## Pitch

- [ ] 5-minute limit
- [ ] Problem in first 30 seconds
- [ ] Working demo
- [ ] AI judgment
- [ ] Numbers
- [ ] Failure story
- [ ] Clear closing

## Submission

- [ ] Public repo
- [ ] Video link tested
- [ ] Project name final
- [ ] Track final
- [ ] Objective accurate
- [ ] What broke accurate
- [ ] Resume attached
- [ ] Final confirmation reviewed last

---

# 41. Final Go / No-Go Gate

Do not submit unless all P0 requirements are green.

```text
P0 Technical
     ↓
P0 Measurement
     ↓
P0 Demo
     ↓
P0 Documentation
     ↓
P0 Submission
```

If any of these is red:

```text
DO NOT add polish.
FIX THE P0 ISSUE.
```

If all P0 items are green:

```text
STOP BUILDING.
START PACKAGING.
```

---

# 42. Time Allocation Strategy

Use time based on submission impact.

Recommended:

```text
45%  Core implementation + integration
20%  Testing + verification
15%  Evaluation + metrics
10%  Dashboard + visual polish
10%  README + pitch + submission
```

If time becomes limited:

### Cut first

```text
advanced UI
extra charts
optional model complexity
extra recovery actions
deployment
```

### Never cut

```text
webhook correctness
policy guardrails
verification
metrics
exception list
demo
README
pitch
```

---

# 43. Final "Winning Surface"

The strongest final demo screen should tell this story:

```text
REVENUE AT RISK
₹X

VERIFIED CASH RECOVERED
₹Y

SUBSCRIPTION REVENUE REACTIVATED
₹Z

RECOVERY RATE
N%

EXCEPTIONS
N
```

Then:

```text
Why the remaining revenue was not recovered
```

Then:

```text
One detailed audit trail
```

This is the single strongest visual summary of Track 03's bar.

---

# 44. Final Product Story

Vasooli should be presented as:

### Not

> another payment retry bot.

### Not

> an LLM wrapper around Razorpay.

### Not

> a dashboard showing failed payments.

### Instead

> **A bounded AI recovery orchestrator for recurring subscription revenue: it understands what failed, decides what should happen, executes only policy-approved actions, verifies the actual financial outcome, and reports both recovered and unrecovered revenue.**

---

# 45. Final Conclusion

The planning phase is now complete.

The project should now move into **controlled execution**, not additional brainstorming.

The seven technical steps are the implementation plan:

```text
1. Setup & Foundation Proof
2. Webhook Ingestion & State Layer
3. Synthetic Dataset Generator
4. Diagnose + Decide Engine
5. Execute Recovery Actions
6. Verify + Measure + Dashboard
7. Batch Evaluation + Demo Prep
```

After Step 7, the project should enter a **submission freeze**.

The key objective is not to make Vasooli huge.

The key objective is to make it:

```text
Correct
+
Complete
+
Measurable
+
Explainable
+
Safe
+
Demoable
+
Trustworthy
```

Razorpay's current Buildathon framing is unusually favorable to this strategy because Track 03 explicitly asks for measured batch-level recovered money, bounded recovery, escalation, stopping rules, and auditability—not merely a failure detector. citeturn145320view0

Razorpay's own Test Subscription documentation also gives Vasooli a legitimate Test Mode lifecycle to demonstrate: subscription setup, simulated charge success/failure, subscription state transitions, and subscription webhooks. citeturn420040search0turn420040search5

### Final management decision

```text
PROJECT:
Vasooli

TRACK:
03 — AI Revenue Recovery

SCOPE:
Failed Recurring Subscription Payment Recovery

BUDGET:
₹0 target

PRIMARY PROOF:
Verified money recovered across a batch

PRIMARY DEMO:
Failed subscription → recovery decision → bounded action → verified outcome

PRIMARY AI STORY:
AI reasoning + deterministic money-action guardrails

PRIMARY TRUST STORY:
Cash recovered ≠ subscription reactivated
+
full exception list
+
audit trail

PRIMARY WINNING STORY:
Problem → Working Product → AI Judgment → Money Recovered → Failure Recovered
```

**From this point, the correct move is execution. Do not keep redesigning the project unless a real technical constraint forces a change.**

---

# 46. Source Register

## Razorpay Buildathon
https://razorpay.com/buildathon/

Used for:
- program format
- student eligibility
- internship context
- track definitions
- Track 03 requirements
- judging signals
- public repo / pitch expectations

## Razorpay Test Subscriptions
https://razorpay.com/docs/payments/subscriptions/test/

Used for:
- Test Mode subscription flow
- plans
- subscription creation
- authentication
- simulated charge outcomes
- `subscription.pending`
- `subscription.halted`
- test lifecycle

## Razorpay Subscription Webhooks
https://razorpay.com/docs/webhooks/subscriptions/

Used for:
- subscription webhook events
- webhook payload structure

## Razorpay Webhook Validation & Testing
https://razorpay.com/docs/webhooks/validate-test/

Used for:
- webhook signature verification
- Test Mode webhook testing
- idempotency/order considerations

## Razorpay Payment Link Testing
https://razorpay.com/docs/payments/payment-links/create/

Used for:
- Test Mode Payment Links
- test-mode Payment Link limit
- success/failure test flow

## Razorpay Subscription Links
https://razorpay.com/docs/payments/subscriptions/create-subscription-links/

Used for:
- Test Mode Subscription Link limit

---

# 47. Final Status

```text
Planning                 ✅ COMPLETE
Architecture             ✅ LOCKED
Technical steps          ✅ DEFINED
Problem scope            ✅ LOCKED
Track                    ✅ LOCKED
Execution strategy       ✅ DEFINED
Measurement strategy     ✅ DEFINED
Pitch strategy            ✅ DEFINED
Submission strategy       ✅ DEFINED

NEXT:
IMPLEMENT STEP 1
```
