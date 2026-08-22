# Vasooli — Step 4: Diagnose + Decide Engine
### Detailed Build Plan | Track 03 — AI Revenue Recovery

---

## 1. Step Objective

Step 4 converts the Step 3 synthetic input data plus the subscription/payment state produced by Step 2 into a **defensible recovery decision**.

The engine must do four things:

```text
RAW EVIDENCE
    ↓
DIAGNOSE
    ↓
RECOVERY SCORE
    ↓
POLICY DECISION
```

The implementation must remain explainable and deterministic at the money-action boundary.

### Hard boundary

This step does **not** execute Razorpay actions.

It must not:

- create Payment Links;
- charge invoices;
- modify subscriptions;
- send customer communications;
- call Razorpay payment APIs;
- depend on an LLM being available.

Those belong to Step 5.

The output of Step 4 is a **decision package** that Step 5 can execute.

---

# 2. Deliverables

At the end of Step 4, the repository should contain:

```text
app/
├── diagnose/
│   ├── normalizer.py
│   ├── evidence.py
│   ├── scorer.py
│   ├── policy.py
│   ├── decision.py
│   └── schemas.py
│
├── services/
│   └── decision_service.py
│
└── config/
    └── policy.yaml

scripts/
└── evaluate_diagnosis.py

tests/
├── test_normalizer.py
├── test_scorer.py
├── test_policy.py
└── test_decision_engine.py

docs/
└── diagnose-decide.md
```

The exact package structure can change to match the repository, but the responsibilities must remain separated.

---

# 3. Step 4 Architecture

```text
Step 2 State + Step 3 Input Data
                 ↓
          Evidence Builder
                 ↓
          Failure Normalizer
                 ↓
        UNKNOWN-safe Diagnose
                 ↓
          Feature Builder
                 ↓
        Recovery Score (0–1)
                 ↓
      Optional LLM Explanation
                 ↓
       Deterministic Policy
                 ↓
          Decision Package
                 ↓
              Step 5
```

### Most important rule

The LLM can **never** bypass the deterministic policy engine.

```text
LLM recommendation
       ↓
Policy validation
       ↓
Allowed? ── NO ──→ Override / escalate / stop
       │
      YES
       ↓
Final action
```

---

# 4. Responsibilities of Each Layer

## 4.1 Evidence Builder

Input:

- synthetic subscription record from Step 3;
- current subscription/payment state from Step 2;
- raw failure signal;
- historical payment features.

Output:

A normalized evidence object containing only information available **before the recovery action**.

Example:

```json
{
  "subscription_state": "pending",
  "amount": 999,
  "attempt_count": 1,
  "previous_success_count": 8,
  "previous_failure_count": 1,
  "customer_opt_out": false,
  "failure_signal": {
    "gateway_code": "BANK_TEMP_UNAVAILABLE"
  }
}
```

Do not add `recovered_amount`, `execution_result`, or `policy_decision` to this object.

---

# 5. Diagnosis / Failure Normalization

## 5.1 Goal

Convert raw payment/subscription evidence into one internal reason that the rest of the application can understand.

Internal categories:

```text
INSUFFICIENT_FUNDS
CARD_EXPIRED
BANK_DECLINE
MANDATE_CANCELLED
UNKNOWN
```

## 5.2 Normalizer Contract

Recommended interface:

```python
def diagnose(evidence: Evidence) -> DiagnosisResult:
    ...
```

Example result:

```json
{
  "reason": "BANK_DECLINE",
  "confidence": 0.82,
  "evidence": [
    "gateway_code=BANK_TEMP_UNAVAILABLE",
    "attempt_count=2"
  ]
}
```

## 5.3 UNKNOWN is mandatory

The engine must return `UNKNOWN` when:

- evidence is missing;
- signal is conflicting;
- signal is outside the supported mapping;
- confidence falls below the configured threshold;
- the system cannot safely distinguish two categories.

Example:

```text
Unknown gateway code
      ↓
UNKNOWN
      ↓
ESCALATE later
```

Never fabricate a diagnosis just to increase the apparent success rate.

---

# 6. Do Not Overfit the Synthetic Labels

The Step 3 dataset contains ground truth for evaluation, but the Diagnose engine must **not directly read the hidden ground-truth label**.

Correct:

```text
raw failure signal + history
        ↓
Diagnose
        ↓
predicted reason
        ↓
compare against hidden ground truth
```

Incorrect:

```text
ground_truth_reason
        ↓
Diagnose
```

The second approach invalidates the evaluation.

---

# 7. Diagnosis Evaluation

Before building recovery policy, evaluate the normalizer on the synthetic test set.

For the diagnosis stage, report at minimum:

```text
Overall diagnosis accuracy
Per-class precision
Per-class recall
Confusion matrix
UNKNOWN rate
```

For the hackathon, the goal is not to maximize a fake score by making the synthetic signals trivial. Keep the signal-to-label relationship meaningful and document the assumptions.

### Recommended target

The diagnostic layer should produce useful signals for decisioning, but **UNKNOWN is allowed and should not be treated as a failure of the system when evidence genuinely lacks certainty**.

---

# 8. Feature Engine

After diagnosis, construct the features required for the recovery score.

Example features:

```text
amount
subscription_age_days
customer_tenure_days
previous_success_count
previous_failure_count
success_to_failure_ratio
attempt_count
days_since_last_success
subscription_state
customer_opt_out
normalized_failure_reason
```

Derived features must be calculated from input/history, not from future outcomes.

### Example

```python
success_to_failure_ratio = \
    previous_success_count / max(previous_failure_count, 1)
```

Avoid unnecessary features. Start with a small explainable set.

---

# 9. Recovery Score

The recovery score estimates how appropriate an automated recovery intervention is.

It is **not** the same as diagnosis confidence.

Example:

```text
Diagnosis confidence = 0.88
Recovery score        = 0.76
```

Meaning:

> We are fairly confident about the failure reason, but the expected value of automatic intervention is 76%.

## 9.1 V1 implementation

Start with an explainable deterministic score rather than training a complex model immediately.

Example conceptual structure:

```text
Recovery Score =
    history component
  + failure component
  + attempt component
  + state component
  - risk penalties
```

Keep each contribution visible.

Example output:

```json
{
  "recovery_score": 0.78,
  "score_reasons": [
    "8 previous successful payments",
    "only 1 previous failure",
    "current attempt count is low",
    "failure appears temporary"
  ]
}
```

Do not claim this score is a statistically calibrated probability unless it has actually been calibrated and evaluated as such.

Therefore label it:

> `recovery_score`

rather than:

> `probability_of_recovery`

until calibration exists.

---

# 10. Recommended Recovery Actions

The decision engine can return only the actions allowed by the overall architecture:

```text
MONITOR
ONE_TIME_RECOVERY
MANUAL_CHARGE
ESCALATE
STOP
NO_ACTION
```

### Meaning

| Action | Meaning |
|---|---|
| `MONITOR` | Let Razorpay's own retry lifecycle continue; no extra intervention now |
| `ONE_TIME_RECOVERY` | Use a bounded one-time collection workflow such as a Payment Link where appropriate |
| `MANUAL_CHARGE` | Attempt only when an issued invoice and supported payment method make this eligible |
| `ESCALATE` | Human/merchant review required |
| `STOP` | Hard stop; no further automated recovery |
| `NO_ACTION` | Deliberately do nothing because no intervention is justified |

Step 4 decides which action is appropriate. Step 5 performs it.

---

# 11. Deterministic Policy Engine

This is the **final authority**.

Recommended interface:

```python
def apply_policy(context: DecisionContext) -> PolicyDecision:
    ...
```

The policy engine must validate the proposed action against hard safety/business rules.

---

# 12. Mandatory Guardrails

## Rule 1 — Customer opt-out

```text
customer_opt_out == true
        ↓
STOP
```

No model or LLM can override this.

---

## Rule 2 — Explicit mandate cancellation

```text
mandate explicitly cancelled
        ↓
STOP
```

Do not repeatedly pursue a customer who has explicitly cancelled the mandate.

---

## Rule 3 — Unknown diagnosis

```text
reason == UNKNOWN
        ↓
ESCALATE
```

Do not automatically select a money action when the evidence is insufficient.

---

## Rule 4 — Attempt threshold

Example configuration:

```yaml
max_automated_attempts: 3
```

If the internal policy context indicates that the limit has already been reached:

```text
→ STOP or ESCALATE
```

Do not let the LLM raise the limit.

---

## Rule 5 — High-value threshold

Example:

```yaml
high_value_threshold_inr: 50000
```

Above the threshold:

```text
→ ESCALATE
```

Do not let the LLM approve an automatic action beyond the configured monetary boundary.

The exact threshold is a project configuration value, not a Razorpay rule.

---

## Rule 6 — Ineligible Manual Charge

If:

```text
invoice.status != issued
OR payment method unsupported
```

then:

```text
MANUAL_CHARGE → ESCALATE / alternate permitted action
```

Do not pretend the action is executable.

---

## Rule 7 — Already recovered

If the current state already indicates a successful collection or recovered outcome:

```text
→ NO_ACTION
```

This prevents duplicate recovery actions.

---

# 13. Policy Precedence

Rules must be deterministic and ordered.

Recommended precedence:

```text
1. Already recovered           → NO_ACTION
2. Customer opt-out            → STOP
3. Explicit mandate cancel     → STOP
4. Unknown / insufficient data → ESCALATE
5. High-value transaction      → ESCALATE
6. Action eligibility failure  → ESCALATE / alternate
7. Attempt limit reached       → STOP / ESCALATE
8. Otherwise                   → score-driven action
```

This ordering must be encoded in code and covered by tests.

---

# 14. LLM Explanation Layer — Optional

The LLM is a **NICE / optional** component, not a dependency for core functionality.

Its job is to produce a short human-readable explanation such as:

> "The subscription has 8 prior successful payments, only one previous failure, and the current bank decline appears temporary. Monitoring the existing retry cycle is preferred over an additional intervention."

## LLM MUST NOT

- choose an action that bypasses policy;
- increase retry limits;
- ignore customer opt-out;
- approve high-value automatic recovery;
- invent payment evidence;
- claim money was recovered.

## Recommended contract

```python
def explain_decision(context: DecisionContext) -> str:
    ...
```

If the LLM is unavailable:

```text
System continues using deterministic scoring + policy.
```

This is an explicit design goal.

---

# 15. Decision Package

Step 4 should output a complete, immutable decision package for Step 5.

Example:

```json
{
  "subscription_id": "sub_00123",
  "diagnosis": {
    "reason": "BANK_DECLINE",
    "confidence": 0.82
  },
  "recovery_score": 0.76,
  "recommended_action": "MONITOR",
  "policy_decision": "MONITOR",
  "policy_reason": "High recovery score and Razorpay retry cycle remains active",
  "guardrails_triggered": [],
  "llm_explanation": "Existing retry lifecycle should continue without additional intervention."
}
```

### Important distinction

`recommended_action` may come from an advisory scoring/LLM layer.

`policy_decision` is the **actual authoritative decision**.

If they differ, preserve both values.

Example:

```json
{
  "recommended_action": "ONE_TIME_RECOVERY",
  "policy_decision": "ESCALATE",
  "policy_reason": "Amount exceeds automatic-action threshold"
}
```

This difference should be visible in logs and demo data.

---

# 16. Example Decision Scenarios

## Scenario A — Healthy historical payer, temporary decline

```text
Amount: ₹999
Previous successes: 8
Previous failures: 1
Attempt count: 1
Reason: BANK_DECLINE
Opt-out: false
```

Expected:

```text
Diagnosis → BANK_DECLINE
Recovery score → high
Policy → MONITOR
```

---

## Scenario B — Customer cancelled

```text
Reason: MANDATE_CANCELLED
Customer opt-out: true
```

Expected:

```text
Diagnosis → MANDATE_CANCELLED
Policy → STOP
```

No LLM output may override this.

---

## Scenario C — Unknown evidence

```text
Unknown gateway code
Conflicting signals
```

Expected:

```text
Diagnosis → UNKNOWN
Policy → ESCALATE
```

---

## Scenario D — High-value recovery

```text
Amount: ₹75,000
Reason: BANK_DECLINE
Recovery score: high
```

Expected:

```text
Policy → ESCALATE
```

The high score does not override the high-value guardrail.

---

## Scenario E — LLM override prevented

```text
LLM recommendation → ONE_TIME_RECOVERY
Amount → ₹80,000
Policy threshold → ₹50,000
```

Expected:

```text
Final policy decision → ESCALATE
```

This is one of the key demo scenarios for the project.

---

# 17. Policy Configuration

Do not bury business limits throughout the code.

Store them in one configuration object/file.

Example:

```yaml
max_automated_attempts: 3
high_value_threshold_inr: 50000
unknown_confidence_threshold: 0.60
monitor_score_threshold: 0.70
one_time_recovery_score_threshold: 0.55
```

These values are **project policy assumptions**, not Razorpay defaults.

Document why each was chosen.

---

# 18. Testing Strategy

Step 4 must be heavily unit-tested because its most important behavior is deterministic.

## Test categories

### A. Diagnosis tests

- known insufficient-funds signal;
- known expired-card signal;
- bank-decline signal;
- mandate cancellation;
- unknown signal;
- missing signal;
- conflicting signal.

### B. Scoring tests

- more successful history increases score appropriately;
- repeated failures decrease score;
- excessive attempt count penalizes score;
- no future/outcome fields are used.

### C. Policy tests

- opt-out always stops;
- cancelled mandate always stops;
- unknown always escalates;
- high-value transaction always escalates;
- ineligible manual charge cannot pass;
- already recovered produces no action;
- policy overrides advisory recommendation.

### D. Integration tests

Input record:

```text
Step 3 record
```

Output:

```text
DecisionPackage
```

Verify that the package contains all required fields and is serializable.

---

# 19. Evaluation of Step 4

Generate a **held-out synthetic evaluation subset** from Step 3.

Important:

The final decision score must not be evaluated only on the same examples used to tune every threshold.

Use a simple split such as:

```text
Development/tuning: 70–80%
Evaluation:          20–30%
```

Keep the evaluation subset fixed once chosen.

## Report

### Diagnosis

```text
Accuracy
Per-class precision
Per-class recall
UNKNOWN rate
Confusion matrix
```

### Decisioning

Because actual recovery outcomes are not yet being executed in Step 4, do **not** claim a real recovery rate here.

Instead report:

```text
MONITOR decisions: X%
ONE_TIME_RECOVERY recommendations: X%
MANUAL_CHARGE recommendations: X%
ESCALATE decisions: X%
STOP decisions: X%
NO_ACTION decisions: X%
Guardrail overrides: N
UNKNOWN diagnoses: N
```

These are **decision-engine metrics**, not money-recovered metrics.

Actual recovered revenue belongs to Step 6/7 after execution and verification.

---

# 20. Auditability Requirements

Every decision must be explainable from stored inputs and deterministic rules.

Minimum decision log:

```text
subscription_id
input_snapshot_id
diagnosed_reason
diagnosis_confidence
recovery_score
recommended_action
policy_decision
policy_reason
guardrails_triggered
llm_used
llm_explanation
engine_version
timestamp
```

Do not store secrets or raw payment credentials.

The `engine_version` field is important so later changes can be tied to the result that produced them.

---

# 21. Failure Handling

The engine itself must fail safely.

## Case: scoring exception

```text
Scoring fails
   ↓
Do not invent score
   ↓
ESCALATE
```

## Case: LLM unavailable

```text
LLM unavailable
   ↓
Continue without explanation
   ↓
Policy decision still runs
```

## Case: invalid input

```text
Invalid/missing required input
   ↓
Validation error
   ↓
ESCALATE / reject decision package
```

## Case: unsupported action

```text
Policy requests unsupported action
   ↓
ESCALATE
```

The system must never silently convert an unsupported action into an assumed successful recovery.

---

# 22. Demo-Critical Scenario

Build one explicit scenario that demonstrates **AI judgment + policy safety**.

Recommended flow:

```text
Subscription
₹80,000
        ↓
Bank decline
        ↓
High recovery score
        ↓
LLM recommends ONE_TIME_RECOVERY
        ↓
Policy checks amount threshold
        ↓
Automatic action NOT allowed
        ↓
FINAL = ESCALATE
```

Pitch line:

> "The AI recommended recovery, but our policy engine refused to let the model move money above the configured threshold."

This directly demonstrates where AI is used **and where it is intentionally not trusted with final authority**.

---

# 23. Definition of Done

Step 4 is complete only when all of the following are true:

- [ ] Raw evidence is converted to an internal diagnosis.
- [ ] `UNKNOWN` is supported and tested.
- [ ] Diagnosis does not read hidden ground truth.
- [ ] Recovery score is explainable.
- [ ] Policy rules are centralized/configurable.
- [ ] Customer opt-out always stops automation.
- [ ] Mandate cancellation always stops automation.
- [ ] Unknown evidence escalates.
- [ ] High-value transactions obey the configured threshold.
- [ ] Manual charge eligibility is enforced.
- [ ] LLM is optional and non-authoritative.
- [ ] Policy can override LLM recommendations.
- [ ] Decision package is serializable and complete.
- [ ] Unit tests cover all safety-critical rules.
- [ ] Held-out evaluation subset is used.
- [ ] No future/outcome fields leak into decision inputs.
- [ ] Decision logs include policy reason and engine version.
- [ ] Core engine still works when the LLM is unavailable.

---

# 24. Handoff to Step 5

Step 4 hands Step 5 a **decision package**, not an API call.

Example:

```text
Step 4
  ↓
DecisionPackage {
    subscription_id,
    policy_decision,
    policy_reason,
    diagnosis,
    recovery_score,
    guardrails_triggered,
    audit_context
  }
        ↓
Step 5
  ↓
Execute the permitted Razorpay/Test Mode action
```

Step 5 must never reinterpret or weaken the Step 4 policy decision merely to make the demo succeed.

---

# 25. Step 4 Hard Gate

Do **not** proceed to Step 5 until this works:

```text
Step 3 input
    ↓
Diagnose
    ↓
Recovery score
    ↓
LLM optional explanation
    ↓
Deterministic policy
    ↓
Decision package
```

And these safety scenarios must all pass:

```text
Opt-out              → STOP
Mandate cancelled    → STOP
Unknown evidence     → ESCALATE
High-value case      → ESCALATE
Already recovered    → NO_ACTION
LLM unavailable      → decision still works
LLM unsafe advice    → policy overrides
```

### The Step 4 success criterion

> **For every input, Vasooli can explain what it believes is happening, quantify the recovery opportunity with an explainable score, and produce a bounded final action that the policy engine—not the LLM—controls.**

Only after this gate passes should Step 5 connect those actions to real Razorpay Test Mode operations.
