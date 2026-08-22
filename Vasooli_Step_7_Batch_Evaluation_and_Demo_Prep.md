# Vasooli — Step 7: Batch Evaluation + Demo Prep
### Detailed & Structured Final Submission Plan | Razorpay AI Buildathon — Track 03

---

# 0. Step Purpose

Step 7 is the **final submission gate**.

All core product work from Steps 1–6 must already be functioning.

Step 7 does not introduce major new product features.

Its purpose is to turn the working system into:

```text
Verified Product
      ↓
Full Batch Evaluation
      ↓
Final Evidence
      ↓
Clean GitHub Repository
      ↓
5-Minute Pitch
      ↓
Application Answers
      ↓
Final Submission Review
      ↓
SUBMIT ONCE
```

The Razorpay Buildathon application explicitly asks for:

- Full name
- College
- Graduation year
- In-person from September
- 6 or 12 months
- Resume
- Track
- Project name
- What it solves
- Public GitHub repository URL
- 5-minute pitch video link
- What broke, and how you got out
- Final submission confirmation

The final confirmation states that no further changes/edits can be made after submission.

Therefore:

> **Do not submit until every artifact and every claim in the form has been verified.**

---

# 1. Step 7 Final Objective

By the end of Step 7, Vasooli must have:

```text
1. A reproducible batch evaluation
2. Final measured recovery numbers
3. A complete exception list
4. A working Razorpay Test Mode demo
5. A clean public GitHub repository
6. A strong README
7. A 5-minute pitch video
8. A truthful "What broke" answer
9. Final application answers
10. Final submission checklist completed
```

---

# 2. Final Product Definition

Use this as the final one-line description:

> **Vasooli detects failed recurring subscription payments, diagnoses the recovery situation, chooses a bounded recovery intervention, verifies the actual outcome, and measures recovered revenue across a batch with an audit trail and honest exception reporting.**

### Narrow scope

```text
Razorpay Subscriptions
+
Failed recurring-payment recovery
+
Razorpay Test Mode
```

Do not expand the scope during Step 7.

---

# 3. Step 7 Workstreams

Run Step 7 in these workstreams:

```text
A. Freeze Product
B. Full Batch Evaluation
C. Real Razorpay Demo Validation
D. Final Metrics & Evidence
E. GitHub / README
F. Failure Story
G. 5-Minute Pitch
H. Submission Form
I. Final Security & Reproducibility Audit
J. Submission
```

Priority:

```text
A → B → C → D → E → F → G → H → I → J
```

---

# 4. Workstream A — Freeze Product

Before evaluating the final version:

## 4.1 Freeze the architecture

No new major features after this point.

The final pipeline is:

```text
Razorpay Test Mode
        ↓
Webhook
        ↓
Signature Verification + Deduplication
        ↓
Detect
        ↓
Diagnose
        ↓
Recovery Score
        ↓
LLM Explanation (optional)
        ↓
Deterministic Policy Engine
        ↓
Execute
        ↓
Verify
        ↓
Measure
        ↓
Audit + Exceptions
```

## 4.2 Freeze the action set

Final supported actions:

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

Do not add another recovery action at the last minute.

## 4.3 Freeze policy version

Store a version:

```text
policy_version = v1.0
```

Every final decision should record the policy version.

This makes the final results reproducible.

---

# 5. Workstream B — Full Batch Evaluation

## 5.1 Evaluation dataset

Use the Step 3 generator.

Target:

```text
500–2,000 records
```

Recommended final run:

```text
1,000–2,000 records
```

Use a fixed random seed.

Example:

```text
SEED = 20260821
```

Use the actual run seed in the final README/report.

---

# 6. Evaluation Isolation

The final evaluation must be run without manually selecting favorable cases.

Required:

```text
Generate dataset
      ↓
Freeze dataset
      ↓
Run entire dataset
      ↓
Collect all decisions
      ↓
Collect all execution outcomes
      ↓
Collect all verified outcomes
```

No manual removal of failed cases.

No cherry-picking.

No changing thresholds halfway through the final run.

If thresholds are changed:

```text
mark run invalid
→ re-run from beginning
```

---

# 7. Batch Evaluation Outputs

Generate:

```text
reports/
├── final_batch_report.json
├── final_batch_report.csv
├── final_exceptions.csv
├── final_action_summary.csv
└── final_run_metadata.json
```

`final_run_metadata.json` should contain:

```json
{
  "run_id": "final_001",
  "dataset_size": 2000,
  "seed": 20260821,
  "policy_version": "v1.0",
  "model_version": "v1.0",
  "generated_at": "...",
  "test_mode": true
}
```

---

# 8. Final Financial Metrics

Report at minimum:

```text
Records processed
Revenue at risk
Cash recovered
Cash recovery rate
Subscription revenue reactivated
Subscription reactivation rate
Unrecovered revenue
Exception count
Escalation count
Stop count
Monitor count
```

## Formula

```text
Cash Recovery Rate
=
Verified Cash Recovered
/
Revenue At Risk
× 100
```

Do not change the denominator to make the metric look better.

---

# 9. Action-Level Results

Produce a table like:

| Action | Cases | Amount at Risk | Verified Cash Recovered | Recovery Rate |
|---|---:|---:|---:|---:|
| MONITOR | X | ₹X | ₹X | X% |
| ONE_TIME_RECOVERY | X | ₹X | ₹X | X% |
| ESCALATE | X | ₹X | ₹0* | N/A |
| STOP | X | ₹X | ₹0 | N/A |
| NO_ACTION | X | ₹X | ₹0* | N/A |

Do not report zero-recovery actions as failures when recovery was intentionally not attempted.

Explain the denominator for every rate.

---

# 10. Exception Summary

Every unrecovered case must be categorized.

Example:

```text
UNKNOWN_FAILURE_REASON
CUSTOMER_CANCELLED
CUSTOMER_OPTED_OUT
PAYMENT_NOT_COMPLETED
SUBSCRIPTION_REMAINS_HALTED
VERIFICATION_TIMEOUT
PROVIDER_ERROR
UNSUPPORTED_ACTION
AMOUNT_MISMATCH
```

Generate a count and amount for each.

Example:

```text
Exception                         Cases      Revenue At Risk
------------------------------------------------------------
Customer cancelled                 62             ₹84,000
Payment not completed              47             ₹71,000
Unknown reason                     21             ₹43,000
Verification timeout               9             ₹18,000
...
```

This is part of the proof that results are honest.

---

# 11. Synthetic vs Real Razorpay Evidence

Keep two evidence categories clearly separated.

## A. Synthetic batch

Used for:

- large-scale evaluation
- decision behavior
- recovery metrics
- exception analysis

## B. Razorpay Test Mode

Used for:

- real integration proof
- webhook proof
- Payment Link execution
- actual test payment verification
- demo

Never describe the synthetic batch as:

> "2,000 real Razorpay transactions."

Use:

> **2,000 synthetic evaluation records + controlled Razorpay Test Mode integration flows.**

---

# 12. Workstream C — Real Razorpay Demo Validation

Before recording, perform a final clean run from the actual application.

## Demo Scenario 1 — Recovery

```text
Failed recurring payment
        ↓
Webhook received
        ↓
Diagnosis
        ↓
Policy = ONE_TIME_RECOVERY
        ↓
Payment Link created
        ↓
Test payment completed
        ↓
Verification
        ↓
₹ Cash Recovered updated
```

## Demo Scenario 2 — Safe STOP

```text
Customer opted out
        ↓
Decision = STOP
        ↓
No Payment Link
        ↓
Audit trail records blocked action
```

## Demo Scenario 3 — Policy Overrides AI

```text
LLM recommendation:
RECOVER

Policy:
BLOCK

Reason:
Hard guardrail

Final:
ESCALATE / STOP
```

Prepare all three before recording.

---

# 13. Real Demo Reliability Rules

Before video recording:

- [ ] Test API credentials work
- [ ] Backend starts cleanly
- [ ] Webhook endpoint works
- [ ] Webhook signature verification works
- [ ] Event deduplication works
- [ ] Database is clean for the demo
- [ ] Test subscription exists
- [ ] Failure scenario is reproducible
- [ ] Payment Link flow works
- [ ] Verification result appears
- [ ] Dashboard updates
- [ ] Audit trail is visible

Create a clean demo database/state.

Do not record with stale development records unless they are intentionally part of the story.

---

# 14. Workstream D — Final Metrics & Evidence

Create one authoritative metrics file:

```text
reports/final_metrics.md
```

It should contain:

## Executive result

```text
Dataset: X records
Revenue at risk: ₹X
Verified cash recovered: ₹X
Cash recovery rate: X%
Subscription revenue reactivated: ₹X
Exceptions: X
```

## Method

- dataset generation seed
- policy version
- model/scoring version
- test date
- evaluation procedure

## Action breakdown

- MONITOR
- ONE_TIME_RECOVERY
- ESCALATE
- STOP
- NO_ACTION
- MANUAL_CHARGE if implemented

## Exceptions

Complete summary.

## Limitations

Explicitly mention:

- synthetic batch
- Razorpay Test Mode
- manual-charge limitations if applicable
- test-mode resource limits
- no claim of real merchant performance

This document becomes the source of truth for the README and pitch.

---

# 15. Never Invent Metrics

If the final result is:

```text
Cash recovered = ₹0
```

then say ₹0.

If:

```text
Recovery rate = 22%
```

say 22%.

Do not:

- tune the dataset until the number looks impressive
- remove unsuccessful records
- change the denominator
- count unverified actions
- count Payment Link creation as recovery
- count synthetic "ground truth" as real Razorpay revenue

A lower honest number is better than a fabricated impressive one.

---

# 16. Workstream E — GitHub Repository

The final repository must be public.

## Suggested structure

```text
vasooli/
├── backend/
├── frontend/
├── data/
│   ├── generator/
│   └── sample/
├── reports/
│   ├── final_metrics.md
│   ├── final_batch_report.json
│   ├── final_batch_report.csv
│   └── final_exceptions.csv
├── tests/
├── docs/
├── scripts/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
└── LICENSE
```

Adapt to the actual project structure.

---

# 17. GitHub Secret Audit

Before making the repository public:

```text
Search repository for:
rzp_
api_key
api_secret
secret
token
password
authorization
GROQ
ANTHROPIC
```

Check:

- [ ] no Razorpay secret
- [ ] no LLM API key
- [ ] no personal access token
- [ ] no database password
- [ ] no private webhook secret
- [ ] no `.env`
- [ ] no production credentials
- [ ] no private customer data

Keep:

```text
.env.example
```

with placeholders only.

---

# 18. Git History Audit

Do not check only the current files.

Run a history/secret scan.

If a secret was ever committed:

```text
REMOVE IT FROM GIT HISTORY
+
ROTATE THE SECRET
```

Deleting the file from the latest commit is not enough.

---

# 19. README Structure

README should be written for a judge who has never seen Vasooli.

Recommended order:

```text
# Vasooli

One-line pitch

## Problem
## Solution
## Why This Is Different
## Architecture
## How It Works
## Razorpay Integration
## AI Architecture
## Guardrails
## Verification
## Evaluation
## Results
## Exception Analysis
## Demo
## Tech Stack
## Local Setup
## Environment Variables
## Project Structure
## Known Limitations
## What Broke
## Future Scope
```

---

# 20. README — Problem Section

Explain the problem in business language first.

Example:

> Failed recurring payments create revenue leakage. The problem is not merely detecting a failed charge; a merchant must determine whether to monitor, intervene, escalate, or stop, then verify whether the intervention actually recovered money.

Then explain the technical solution.

Avoid starting with:

> "We use FastAPI, SQLite and LLM."

Technology comes after the problem.

---

# 21. README — AI Judgment Section

Explicitly explain:

```text
Where AI is used:
- explanation / reasoning
- optional recovery scoring support

Where AI is NOT used:
- hard compliance rules
- customer opt-out enforcement
- action eligibility
- final money-action authorization
```

This directly supports the Buildathon's AI-judgment criterion.

---

# 22. README — Honest Limitations

State:

```text
- Evaluation batch is synthetic.
- Payment workflows use Razorpay Test Mode.
- Test-mode resource limits constrain the number of real demo flows.
- Subscription recovery and one-time cash recovery are measured separately.
- Manual charge depends on payment-method eligibility.
```

Never hide these.

---

# 23. Workstream F — "What Broke, How Did You Get Out?"

This answer must use **real problems encountered during development**.

Create:

```text
docs/what-broke.md
```

For each issue:

```text
Problem
Impact
Root Cause
What We Tried
Final Fix
How We Prevented Recurrence
```

Recommended candidates only if they actually occurred:

### Example

```text
Webhook arrived twice
→ duplicate action risk
→ implemented event-id deduplication
```

or:

```text
Webhook arrived out of order
→ local state became stale
→ added state reconciliation
```

or:

```text
LLM recommended an unsafe action
→ policy engine blocked it
→ deterministic guardrail became final authority
```

or:

```text
Manual charge unavailable for domestic-card scenario
→ action eligibility needed tightening
→ routed unsupported cases to escalation
```

Do not claim an issue happened if it did not.

---

# 24. Workstream G — 5-Minute Pitch

The pitch must tell one clear story.

Do not spend 5 minutes explaining every implementation detail.

Recommended structure:

```text
0:00–0:30  Problem
0:30–1:00  Vasooli
1:00–2:00  Live/recorded demo
2:00–3:00  How the agent decides
3:00–4:00  Results
4:00–4:30  Failure + guardrails
4:30–5:00  Why it matters / close
```

---

# 25. Pitch — 0:00–0:30 Problem

Start with money.

Example structure:

```text
"Every failed subscription charge creates revenue at risk.
But a failed payment does not have one universal recovery action."

"Retry."
"Send recovery."
"Escalate."
"Stop."

"The wrong action can waste attempts or annoy a customer."
```

Do not over-explain Razorpay infrastructure here.

---

# 26. Pitch — 0:30–1:00 Product

Introduce:

> **Vasooli — AI Revenue Recovery Agent**

Core loop:

```text
Detect
→ Diagnose
→ Decide
→ Execute
→ Verify
→ Measure
```

Show the architecture briefly.

---

# 27. Pitch — 1:00–2:00 Demo

Prefer a single uninterrupted successful recovery flow.

```text
subscription failure
↓
webhook
↓
Vasooli diagnosis
↓
policy decision
↓
Payment Link
↓
test payment
↓
verified outcome
↓
₹ recovered
```

Show the dashboard changing.

Do not spend the demo navigating multiple screens unnecessarily.

---

# 28. Pitch — 2:00–3:00 AI Judgment

Show:

```text
LLM recommendation
        ↓
Policy engine
        ↓
Final action
```

Then show one explicit override:

```text
LLM:
RECOVER

Policy:
STOP

Reason:
Customer opted out
```

Say:

> The LLM can explain, but it does not get final authority over money actions.

This is one of the strongest technical points.

---

# 29. Pitch — 3:00–4:00 Results

Show final batch metrics:

```text
2,000 synthetic cases
₹X revenue at risk
₹Y verified cash recovered
Z% recovery rate
N exceptions
```

Then immediately show:

```text
Why the remaining revenue was not recovered
```

Use the exception list.

This demonstrates honesty.

---

# 30. Pitch — 4:00–4:30 Failure Recovery

Show one genuine engineering problem.

Ideal format:

```text
What broke:
duplicate/out-of-order webhook

Why:
webhooks are delivered asynchronously

Fix:
event-id deduplication + state reconciliation

Result:
no duplicate recovery action
```

Only use actual development history.

---

# 31. Pitch — 4:30–5:00 Closing

End on measurable value:

```text
Detect revenue at risk
+
Choose bounded recovery action
+
Verify real outcome
+
Show exactly what was recovered
+
Show exactly what was not
```

Closing sentence:

> **Vasooli is not another failed-payment detector. It is a bounded recovery loop with evidence at every step.**

---

# 32. Video Recording Checklist

Before recording:

- [ ] Browser clean
- [ ] Notifications disabled
- [ ] Correct dashboard state
- [ ] Correct demo data
- [ ] No secrets visible
- [ ] No personal information visible
- [ ] Font/UI readable
- [ ] Microphone tested
- [ ] Screen resolution tested
- [ ] Demo flow rehearsed
- [ ] Backup recording available

Record at least:

```text
Take 1 — safety rehearsal
Take 2 — primary
Take 3 — backup
```

Do not keep recording indefinitely.

Choose the clearest version.

---

# 33. Video Quality Priority

Priority order:

```text
1. Clear story
2. Working demo
3. Readable metrics
4. Good audio
5. Stable screen
6. Visual polish
```

A perfect visual edit with a weak technical story is not useful.

---

# 34. Workstream H — Application Form

Fill the form only after final metrics and video are ready.

## Track

```text
AI Revenue Recovery
```

## Project Name

```text
Vasooli — AI Revenue Recovery Agent
```

## Project Objectives

Recommended final structure:

> Vasooli detects failed recurring subscription payments, diagnoses the recovery situation, selects a bounded intervention, executes the permitted recovery workflow, verifies the actual result, and measures recovered revenue across a batch with an audit trail and honest exception reporting.

Update the wording if the final product differs.

---

# 35. GitHub URL

Requirements:

- public repository
- opens in incognito/private browser
- README loads correctly
- setup instructions work
- no secrets
- code matches the recorded demo

Test:

```text
Copy GitHub URL
→ open private/incognito window
→ clone
→ inspect README
```

---

# 36. Pitch Video Link

Before submission:

- [ ] Link works without authentication if intended
- [ ] Video is unlisted/public as required
- [ ] Correct final video
- [ ] Under 5 minutes
- [ ] Audio works
- [ ] Demo is visible

Do not change or replace the video after final submission unless the form allows it before submission.

---

# 37. "What Broke" Answer

Write the final answer from:

```text
docs/what-broke.md
```

Do not fabricate an obstacle because the application asks for one.

Strong answer structure:

```text
1. What broke
2. Why it happened
3. What we changed
4. How we validated the fix
```

Keep it concise.

---

# 38. Form Final Review Table

Before submitting:

| Field | Verified? |
|---|---|
| Full name | [ ] |
| College | [ ] |
| Graduation year | [ ] |
| In-person from September | [ ] |
| 6 or 12 months | [ ] |
| Resume | [ ] |
| Track | [ ] |
| Project name | [ ] |
| What it solves | [ ] |
| GitHub URL | [ ] |
| Pitch video | [ ] |
| What broke/how fixed | [ ] |
| Final confirmation | [ ] |

---

# 39. Final Security Review

Run immediately before submission.

## Credentials

- [ ] No live Razorpay keys
- [ ] No test secret in GitHub
- [ ] No LLM key
- [ ] No webhook secret
- [ ] No database password

## Personal information

- [ ] No personal customer information
- [ ] No phone numbers
- [ ] No email addresses from real users
- [ ] No private college/internal data
- [ ] No screenshots containing secrets

## Repository

- [ ] `.gitignore` correct
- [ ] `.env` ignored
- [ ] `.env.example` contains placeholders
- [ ] Git history checked
- [ ] Public clone tested

---

# 40. Reproducibility Review

A judge/developer should be able to understand:

```text
git clone
→ install dependencies
→ configure .env
→ run backend
→ run frontend
→ run dataset generator
→ run evaluation
```

Document exact commands.

Minimum README commands:

```bash
git clone <repo>
cd vasooli

# backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# frontend
npm install
npm run dev
```

Adapt commands to the actual project.

---

# 41. Final Test Matrix

Run before submission:

### Core

- [ ] Webhook signature valid
- [ ] Duplicate webhook safe
- [ ] Out-of-order webhook safe
- [ ] Diagnosis works
- [ ] UNKNOWN fallback works
- [ ] Policy engine works
- [ ] LLM failure does not break money safety
- [ ] STOP works
- [ ] ESCALATE works
- [ ] Payment Link action works
- [ ] Verification works
- [ ] Metrics work

### Financial

- [ ] Recovery counted once
- [ ] Cash vs subscription metrics separate
- [ ] No unverified recovery counted
- [ ] No negative amount
- [ ] No duplicate amount
- [ ] Exception list complete

### Demo

- [ ] Main recovery scenario
- [ ] STOP scenario
- [ ] AI-policy override scenario

---

# 42. Full Final Batch Run

After code is frozen:

```text
1. Clean environment
2. Generate final dataset
3. Freeze dataset
4. Run full batch
5. Save report
6. Validate metrics
7. Validate exceptions
8. Do not modify logic
9. Use this exact report for README/pitch
```

Record:

```text
run_id
dataset_size
seed
policy_version
model/scoring version
Git commit SHA
timestamp
```

This makes the result traceable.

---

# 43. Git Commit Strategy

Recommended final commits:

```text
feat: complete recovery execution
feat: add outcome verification and metrics
feat: add dashboard
test: finalize batch evaluation
docs: add final results and pitch materials
chore: final submission cleanup
```

Then record the final commit SHA in your run metadata.

Do not make significant code changes after the final metric run without rerunning evaluation.

---

# 44. Final GitHub State

The public repository should contain:

```text
WORKING CODE
+
README
+
SETUP
+
ARCHITECTURE
+
TESTS
+
FINAL METRICS
+
LIMITATIONS
+
WHAT BROKE
```

Avoid dumping:

```text
huge raw datasets
private environment files
temporary logs
unused experiments
broken prototype folders
```

Keep the repository clean enough for a judge to understand quickly.

---

# 45. Pitch Evidence Map

Make sure every Buildathon judging dimension has visible evidence.

## Problem taste

Show:

```text
revenue at risk
```

## Build quality

Show:

```text
webhook verification
event deduplication
state reconciliation
audit trail
```

## AI judgment

Show:

```text
LLM recommendation
vs
deterministic policy decision
```

## Failure recovery

Show:

```text
real engineering problem
→ fix
→ validation
```

## Track 03 bar

Show:

```text
batch
+
₹ recovered
+
stopping rules
+
escalation
+
exception list
+
audit trail
```

---

# 46. What NOT to Do in Step 7

Do not:

- add a new ML model just before submission
- redesign the UI unnecessarily
- switch LLM providers because another one looks better
- change the recovery policy to improve one metric
- claim synthetic results as production performance
- claim Payment Link recovery equals subscription reactivation
- count execution requests as recovered money
- remove exceptions from the final report
- record a demo using fake results
- submit before testing the public GitHub URL
- expose API credentials
- forget to keep a local backup of the final project

---

# 47. Final Submission Freeze

When all artifacts are ready:

```text
FINAL CODE
      ↓
FINAL BATCH RUN
      ↓
FINAL METRICS
      ↓
FINAL README
      ↓
FINAL VIDEO
      ↓
FINAL FORM
      ↓
FINAL SECURITY CHECK
      ↓
FINAL REVIEW
      ↓
SUBMIT
```

Once submitted:

```text
DO NOT ASSUME
you can edit/reupload anything.
```

The buildathon form explicitly warns that the final submission is official and cannot be changed after submission.

---

# 48. Final Submission Checklist

## Product

- [ ] Core system works
- [ ] Razorpay Test Mode integration works
- [ ] Webhook security works
- [ ] Recovery execution works
- [ ] Verification works
- [ ] Dashboard works

## Evaluation

- [ ] 500–2,000 synthetic batch completed
- [ ] Fixed seed recorded
- [ ] Full batch included
- [ ] Revenue at risk calculated
- [ ] Verified cash recovered calculated
- [ ] Subscription reactivation calculated separately
- [ ] Exceptions included
- [ ] No cherry-picking

## Engineering

- [ ] Tests pass
- [ ] No secrets
- [ ] Public repo works
- [ ] README works
- [ ] Setup documented
- [ ] Known limitations documented

## Pitch

- [ ] Under 5 minutes
- [ ] Problem clear
- [ ] Product clear
- [ ] Demo works
- [ ] Metrics visible
- [ ] AI judgment shown
- [ ] Failure story shown
- [ ] Closing is clear

## Submission

- [ ] All 12 requested answers ready
- [ ] GitHub link tested
- [ ] Video link tested
- [ ] "What broke" truthful
- [ ] Resume attached
- [ ] Track = AI Revenue Recovery
- [ ] Project name final
- [ ] Final confirmation checked only after everything else is verified

---

# 49. Final 30-Minute Pre-Submit Procedure

Do not code during this period.

### Minute 0–10

Verify:

```text
GitHub
Video
README
Metrics
```

### Minute 10–20

Verify:

```text
Form answers
Project name
Track
What it solves
What broke
```

### Minute 20–25

Security check:

```text
Secrets
Links
Screenshots
Environment files
```

### Minute 25–30

Read the whole submission once as a judge.

Ask:

```text
What problem does this solve?
How does AI help?
What actually happened?
How much money was recovered?
What failed?
Can I trust their numbers?
```

Only after those answers are obvious:

```text
SUBMIT
```

---

# 50. Step 7 Hard Gate

Step 7 is complete only when:

- [ ] Final batch evaluation completed without cherry-picking.
- [ ] Final financial metrics are reproducible.
- [ ] Exception list is complete.
- [ ] Real Razorpay Test Mode demo works.
- [ ] Dashboard reflects verified outcomes.
- [ ] README explains the system clearly.
- [ ] GitHub is public and secret-free.
- [ ] "What broke" is based on actual development history.
- [ ] Pitch video is under 5 minutes and demonstrates the working system.
- [ ] All application fields are accurate.
- [ ] Final submission has been reviewed once completely.

---

# 51. Final Submission Package

The final package should be:

```text
Vasooli
│
├── Public GitHub Repository
│
├── 5-Minute Pitch Video
│
├── Final Batch Metrics
│
├── Exception Report
│
├── Working Razorpay Test Mode Demo
│
└── Completed Buildathon Form
```

---

# 52. Final Principle

The final submission should make one thing extremely easy for the judges to believe:

> **Vasooli did not just detect failed subscription payments. It took bounded recovery actions, verified what actually happened, measured how much money was recovered, and honestly showed what it could not recover.**

Do not optimize the final submission for the biggest number.

Optimize it for:

```text
Credibility
+
Working Product
+
Measured Value
+
Good AI Judgment
+
Engineering Depth
```

That is the final Step 7 standard.
