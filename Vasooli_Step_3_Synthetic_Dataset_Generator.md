# Vasooli — Step 3: Synthetic Dataset Generator
### Detailed Build Plan | Track 03 — AI Revenue Recovery

---

## 1. Step Objective

Step 3 builds the **synthetic historical dataset** used by Vasooli for batch evaluation and development of the Diagnose + Decide layer.

The dataset must be:

- large enough to demonstrate batch-level revenue recovery evaluation;
- reproducible;
- configurable;
- internally consistent;
- realistic enough to support meaningful recovery decisions;
- strictly separated into **input features** and **system-generated outputs** to avoid target/data leakage.

### Hard boundary

This step does **not** implement:

- LLM reasoning;
- recovery scoring/model training;
- policy decisions;
- Razorpay API actions;
- Payment Links;
- webhooks;
- dashboard UI.

Those belong to later steps.

---

## 2. Deliverables

At the end of Step 3, the repository must contain:

```text
scripts/
└── generate_dataset.py

data/
├── synthetic_subscriptions.csv
└── dataset_metadata.json

tests/
└── test_dataset_generator.py

docs/
└── dataset-assumptions.md
```

### Required output

A configurable generator that can produce **500–2,000 synthetic subscription/payment-failure records** using a single command.

Example:

```bash
python scripts/generate_dataset.py \
  --records 1000 \
  --seed 42 \
  --output data/synthetic_subscriptions.csv
```

The same seed and parameters must generate the same dataset.

---

# 3. Dataset Philosophy

## 3.1 What the dataset represents

The dataset represents a merchant's historical subscription-payment population and failed recurring-payment situations that Vasooli could encounter.

It is a **simulation dataset**.

The project must never describe its generated proportions as real-world BFSI statistics unless an independently sourced statistic is explicitly cited elsewhere.

The README must state:

> Failure distributions are configurable simulation assumptions created for evaluation; they are not claims about real-world payment-failure prevalence.

---

## 3.2 Two datasets/concepts must not be mixed

There are two different kinds of data in the project:

### A. Synthetic batch data

Used for:

- large-scale evaluation;
- controlled edge cases;
- measuring the recovery workflow;
- reproducibility.

### B. Real Razorpay Test Mode data

Used later for:

- proving actual integration;
- validating webhook behavior;
- demonstrating a small number of real Test Mode flows.

Do **not** make the synthetic dataset depend on live Razorpay API calls.

---

# 4. Input Schema — No Leakage

These are the fields available to the Diagnose + Decide system **before it takes a recovery action**.

```text
subscription_id
customer_id
plan_id
amount
currency
due_date
subscription_age_days
customer_tenure_days
previous_success_count
previous_failure_count
days_since_last_success
attempt_count
failure_signal
subscription_state
customer_opt_out
```

## Field definitions

| Field | Type | Meaning |
|---|---|---|
| `subscription_id` | string | Unique synthetic subscription identifier |
| `customer_id` | string | Synthetic customer identifier |
| `plan_id` | string | Synthetic plan identifier |
| `amount` | integer | Recurring amount in smallest currency unit or normalized rupee value; choose one convention and document it |
| `currency` | string | `INR` for this project |
| `due_date` | datetime/date | Scheduled recurring charge date |
| `subscription_age_days` | integer | Days since subscription creation |
| `customer_tenure_days` | integer | Days associated with the merchant |
| `previous_success_count` | integer | Number of previous successful recurring collections |
| `previous_failure_count` | integer | Number of previous failed recurring collections |
| `days_since_last_success` | integer | Days since the customer's latest successful payment |
| `attempt_count` | integer | Number of attempts represented by this record |
| `failure_signal` | string | Raw/simulated evidence available to the diagnostic layer |
| `subscription_state` | enum | `pending`, `halted`, or `active` |
| `customer_opt_out` | boolean | Whether the customer has explicitly opted out / cancelled recovery contact |

---

# 5. Output Schema — Generated After Decision

The following values must **not** be generated as input features for the Diagnose + Decide system.

They belong to later pipeline stages:

```text
diagnosed_reason
recovery_score
recommended_action
policy_decision
execution_result
recovered_amount
exception_reason
```

## Why this matters

Incorrect:

```text
failure_reason = CARD_EXPIRED
        ↓
model sees failure_reason
        ↓
model predicts CARD_EXPIRED
```

That is leakage / trivial classification.

Correct:

```text
raw evidence
 + subscription history
 + current state
        ↓
Diagnose
        ↓
normalized reason
```

The generator should therefore produce **raw evidence**, not a pre-labeled answer that the model can simply read.

---

# 6. Failure Signal Design

`failure_signal` should represent evidence rather than the normalized diagnosis.

Example simulated values:

```text
insufficient_balance_signal
expired_card_signal
bank_decline_signal
mandate_cancel_signal
unknown_gateway_signal
```

However, do not make the mapping perfectly trivial.

A better dataset can include supporting metadata inside the signal payload, for example as structured JSON:

```json
{
  "gateway_code": "BANK_TEMP_UNAVAILABLE",
  "attempt_number": 2,
  "source": "payment_failure_event"
}
```

Another:

```json
{
  "gateway_code": "CARD_EXPIRED",
  "attempt_number": 1,
  "source": "payment_failure_event"
}
```

For the first implementation, JSON strings inside a CSV column are acceptable. If parsing becomes awkward, keep the normalized internal structure in Python and serialize it when writing the CSV.

---

# 7. Failure Categories

Use the internal categories defined by the overall project:

```text
INSUFFICIENT_FUNDS
CARD_EXPIRED
BANK_DECLINE
MANDATE_CANCELLED
UNKNOWN
```

### Important

The generator may internally know the intended ground-truth category so that later evaluation can compare the Diagnose stage against it.

But that ground truth must be stored separately from the input features.

Recommended approach:

```text
data/
├── synthetic_subscriptions.csv          # model-facing inputs
└── synthetic_ground_truth.csv           # evaluation-only labels
```

This is preferable to putting `ground_truth_reason` inside the model input file.

---

# 8. Ground-Truth File

Create a separate evaluation-only file:

```text
subscription_id
true_failure_category
true_recovery_eligibility
synthetic_scenario_id
```

Example:

```text
sub_000001,CARD_EXPIRED,RECOVERABLE,scenario_04
sub_000002,MANDATE_CANCELLED,NOT_RECOVERABLE,scenario_09
sub_000003,UNKNOWN,ESCALATE,scenario_12
```

### Critical rule

This file must **never be loaded into the runtime decision pipeline**.

It exists only for evaluation.

---

# 9. Scenario-Based Generation

Do not generate every field independently at random.

That would create contradictory records such as:

```text
subscription_state = halted
attempt_count = 0
previous_failure_count = 0
```

Instead, generate records through coherent scenarios.

Recommended scenario families:

```text
SCENARIO_01  Fresh temporary failure
SCENARIO_02  Repeated insufficient-funds failure
SCENARIO_03  Expired-card failure
SCENARIO_04  Temporary bank decline
SCENARIO_05  Explicit mandate/customer cancellation
SCENARIO_06  Unknown/insufficient evidence
SCENARIO_07  High-value subscription
SCENARIO_08  Long-tenure customer with strong history
SCENARIO_09  New customer with weak history
SCENARIO_10  Recovery already likely via existing retry cycle
```

Each scenario should have internally consistent ranges and fields.

---

# 10. Recommended Synthetic Generation Logic

## 10.1 Customer

Generate:

```text
customer_id
customer_tenure_days
customer_opt_out
```

Use deterministic IDs:

```text
cust_000001
cust_000002
...
```

Avoid generating or storing real people's PII.

Use synthetic names only if the UI later requires names; names should not be necessary for the core model.

---

## 10.2 Plan

Create a small set of reusable plans.

Example:

```text
BASIC_MONTHLY      ₹499
STANDARD_MONTHLY   ₹999
PRO_MONTHLY        ₹2499
BUSINESS_MONTHLY   ₹9999
```

Do not claim these represent Razorpay's actual plans.

They are synthetic project plans.

---

## 10.3 Amount distribution

Use a weighted distribution rather than uniform random values.

Example simulation assumptions:

```text
₹499    common
₹999    common
₹2499   medium
₹4999   medium
₹9999   less common
₹25000+ rare/high-value
```

The exact weights should be configurable or documented as simulation assumptions.

---

## 10.4 Payment history

Generate history coherently.

Examples:

### Loyal customer

```text
previous_success_count = 18
previous_failure_count = 1
```

### New customer

```text
previous_success_count = 0
previous_failure_count = 1
```

### Repeated failure

```text
previous_success_count = 7
previous_failure_count = 4
attempt_count = 3
```

Make sure:

```text
previous_success_count >= 0
previous_failure_count >= 0
attempt_count >= 1 for failed-event records
```

---

# 11. Scenario Consistency Rules

The generator must enforce constraints such as:

```text
IF customer_opt_out = true
    THEN scenario may be MANDATE_CANCELLED
    AND recommended recovery must later be STOP/ESCALATE

IF mandate is explicitly cancelled
    THEN subscription_state should not be generated as a normal active recovery case

IF subscription_state = halted
    THEN attempt_count should indicate prior failures

IF previous_failure_count > 0
    THEN attempt_count/history must be plausible

IF scenario = CARD_EXPIRED
    THEN failure_signal must contain evidence consistent with card expiry
```

These are **data-generation invariants**, not the final policy engine.

The policy engine remains Step 4.

---

# 12. Configurable Failure Distribution

The generator should accept configurable probabilities.

Example CLI:

```bash
python scripts/generate_dataset.py \
  --records 1000 \
  --seed 42 \
  --insufficient-funds 0.35 \
  --expired-card 0.20 \
  --bank-decline 0.25 \
  --mandate-cancel 0.10 \
  --unknown 0.10
```

Before generation, validate:

```text
sum(probabilities) == 1.0
```

Allow a small floating-point tolerance, e.g. `abs(sum - 1.0) < 1e-9`.

If invalid:

```text
exit non-zero
show clear error
```

---

# 13. Randomness and Reproducibility

Every generation command must support:

```bash
--seed 42
```

Use one deterministic RNG source throughout the generator.

Do not mix multiple uncontrolled random libraries.

The metadata file should record:

```json
{
  "records": 1000,
  "seed": 42,
  "generated_at": "...",
  "distribution": {
    "INSUFFICIENT_FUNDS": 0.35,
    "CARD_EXPIRED": 0.20,
    "BANK_DECLINE": 0.25,
    "MANDATE_CANCELLED": 0.10,
    "UNKNOWN": 0.10
  }
}
```

`generated_at` can differ between runs, but the actual record content should remain deterministic for the same seed and configuration.

---

# 14. Dataset Validation

After generation, run an automated validator.

### Required checks

#### Structural

- correct column set;
- no missing required fields;
- correct data types;
- unique `subscription_id`.

#### Numeric

- `amount > 0`;
- counts `>= 0`;
- age/tenure `>= 0`.

#### State

```text
subscription_state ∈ {active, pending, halted}
```

#### Currency

```text
currency = INR
```

#### Boolean

```text
customer_opt_out ∈ {true, false}
```

#### Distribution

Verify actual proportions are close to requested proportions for reasonably large datasets.

Do not require exact percentages because random sampling naturally varies.

---

# 15. Edge Cases Must Be Intentionally Included

A good dataset should not consist only of easy records.

Add a small deterministic set of edge scenarios, for example:

```text
EDGE_01  brand-new subscription
EDGE_02  zero previous successful payments
EDGE_03  repeated failures at retry limit
EDGE_04  high-value subscription
EDGE_05  explicit customer opt-out
EDGE_06  unknown failure signal
EDGE_07  previously successful long-term customer
EDGE_08  contradictory/insufficient evidence requiring UNKNOWN
```

Keep edge-case generation controlled so it does not distort the main distribution.

Recommended:

```text
~2–5% of the batch
```

or a fixed configurable count.

---

# 16. Train/Validation/Test Split — Important Boundary

Step 3 does **not** need to train a model.

However, prepare the data so Step 4 can split it correctly.

Preferred approach:

```text
synthetic dataset
      ↓
fixed seed
      ↓
train / validation / test split in Step 4
```

Do not create a split based on future information such as `recovered_amount`.

The evaluation split must remain untouched by any future decision-rule tuning.

---

# 17. Preventing Evaluation Leakage

The following are forbidden as model inputs:

```text
recovered_amount
execution_result
policy_decision
recommended_action
exception_reason
true_failure_category
```

The model/decision engine should only see what would actually be available when the recovery decision is being made.

This is one of the most important technical-integrity requirements of the project.

---

# 18. Suggested File Format

### Primary input dataset

Use CSV first because it is:

- easy to inspect;
- easy to load into pandas;
- GitHub-friendly;
- easy to debug.

Example:

```text
subscription_id,customer_id,plan_id,amount,currency,due_date,...
sub_000001,cust_000001,PRO_MONTHLY,2499,INR,2026-08-21,...
```

### Metadata

Use JSON for:

- seed;
- generator version;
- record count;
- distribution assumptions;
- timestamp;
- schema version.

---

# 19. Generator CLI

Minimum CLI:

```text
--records
--seed
--output
--ground-truth-output
```

Recommended:

```text
--insufficient-funds
--expired-card
--bank-decline
--mandate-cancel
--unknown
--edge-cases
```

Example:

```bash
python scripts/generate_dataset.py \
  --records 1500 \
  --seed 42 \
  --output data/synthetic_subscriptions.csv \
  --ground-truth-output data/synthetic_ground_truth.csv \
  --edge-cases 40
```

---

# 20. Testing Strategy

Create automated tests for the generator.

### Test 1 — deterministic output

Run twice with the same seed:

```text
seed=42
```

Expected:

```text
identical generated records
```

### Test 2 — different seeds differ

```text
seed=42
vs
seed=43
```

Expected:

```text
not identical
```

### Test 3 — row count

```text
--records 1000
```

Expected:

```text
1000 input records
```

### Test 4 — unique IDs

Expected:

```text
1000 unique subscription IDs
```

### Test 5 — probability validation

Invalid distribution:

```text
0.5 + 0.5 + 0.5 = 1.5
```

Expected:

```text
clear validation error
```

### Test 6 — required columns

Expected schema must be present exactly.

### Test 7 — invariant checks

Generate hundreds of records and assert the scenario/state consistency rules.

---

# 21. Data Quality Report

After generation, print a summary to stdout.

Example:

```text
Vasooli Synthetic Dataset Generator
-----------------------------------
Records:              1500
Seed:                 42
Currency:             INR

Failure scenarios:
INSUFFICIENT_FUNDS     35.1%
CARD_EXPIRED           19.8%
BANK_DECLINE           25.4%
MANDATE_CANCELLED       9.9%
UNKNOWN                 9.8%

States:
PENDING                71.3%
HALTED                 21.4%
ACTIVE                  7.3%

Opt-out:                6.2%

Validation: PASS
```

The exact percentages are generated values, not claimed real-world statistics.

---

# 22. What NOT to Build in Step 3

Do not add:

```text
❌ LLM API
❌ Groq integration
❌ Razorpay API calls
❌ webhook processing
❌ Payment Link generation
❌ recovery policy
❌ recovery scoring model
❌ dashboard
❌ React UI
❌ hosting
```

The goal is a reliable data foundation, not feature creep.

---

# 23. Success Criteria — Step 3 Hard Gate

Step 3 is complete only when all are true:

```text
[ ] 500–2,000 synthetic records can be generated
[ ] Same seed produces reproducible data
[ ] Input and ground-truth data are physically separated
[ ] No output field is used as an input feature
[ ] Failure distribution is configurable
[ ] Distribution values are validated
[ ] Dataset has coherent scenario/state relationships
[ ] UNKNOWN and edge cases exist
[ ] Required schema validation passes
[ ] Automated generator tests pass
[ ] Metadata file records seed/schema/distribution
[ ] Dataset can be loaded successfully by Python/pandas
```

### Final gate command

The exact command should be documented in the README, for example:

```bash
python scripts/generate_dataset.py \
  --records 1000 \
  --seed 42 \
  --output data/synthetic_subscriptions.csv \
  --ground-truth-output data/synthetic_ground_truth.csv
```

Expected:

```text
Generation complete.
Validation: PASS.
Input dataset: data/synthetic_subscriptions.csv
Ground truth:  data/synthetic_ground_truth.csv
Records: 1000
```

---

# 24. Step 3 → Step 4 Handoff

Step 4 receives:

```text
synthetic_subscriptions.csv
        ↓
feature extraction / diagnosis
        ↓
recovery scoring
        ↓
policy engine
```

and separately:

```text
synthetic_ground_truth.csv
        ↓
EVALUATION ONLY
```

### Step 4 must NOT receive

```text
recovered_amount
execution_result
policy_decision
```

because those do not exist at decision time.

---

# 25. Recommended Repository Structure After Step 3

```text
vasooli/
├── app/
│   └── ...
├── scripts/
│   └── generate_dataset.py
├── data/
│   ├── synthetic_subscriptions.csv
│   ├── synthetic_ground_truth.csv
│   └── dataset_metadata.json
├── tests/
│   └── test_dataset_generator.py
├── docs/
│   └── dataset-assumptions.md
├── requirements.txt
├── .env.example
└── README.md
```

Do not commit secrets. The synthetic dataset contains no real payment/customer data and is safe to commit unless the repository later contains sensitive derived data.

---

# 26. Definition of Done

Step 3 is considered **DONE** when Vasooli can produce a clean, reproducible, leakage-free synthetic evaluation dataset with a controlled failure distribution and a separately stored ground-truth file, and all automated validation tests pass.

At that point, move to:

> **Step 4 — Diagnose + Decide Engine**

Do not start Step 4 until the Step 3 hard gate passes.
