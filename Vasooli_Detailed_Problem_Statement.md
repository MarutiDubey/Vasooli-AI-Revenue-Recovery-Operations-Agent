# Vasooli — Detailed Problem Statement
## Razorpay AI Buildathon 2026 — Track 03: AI Revenue Recovery

---

## 1. Track Context

### AI Revenue Recovery

**Find revenue that's slipping away and win it back.**

Razorpay's AI Buildathon Track 03 asks builders to create an agent that detects revenue at risk, determines the right intervention, and executes a bounded recovery workflow. The track explicitly includes payment failures, checkout abandonment, failed subscriptions, overdue receivables, mandate retry, and related recovery workflows.

### Why this problem matters

Revenue loss rarely happens in one clean step. A payment can fail, a recurring subscription can stop collecting, a checkout can be abandoned, or an invoice can become overdue. The merchant may know that revenue was lost, but the difficult part is closing the loop:

```text
Revenue at risk
      ↓
Detect the problem
      ↓
Diagnose the cause
      ↓
Choose the right intervention
      ↓
Execute a bounded recovery workflow
      ↓
Verify the outcome
      ↓
Measure recovered revenue
```

The buildathon's requirement is not merely to identify a problem. The system must demonstrate measurable recovery across a batch, while handling escalation, stopping rules, and auditability.

---

## 2. Problem We Are Solving

### Problem statement

Merchants using recurring payments can lose revenue when subscription charges fail or recurring payment collection is interrupted. A failed charge does not necessarily mean the customer is permanently lost; the correct next step depends on the available evidence, payment state, customer history, previous failures, and the merchant's recovery policy.

Today, a merchant-side recovery workflow can involve several disconnected decisions:

1. Detect that recurring revenue is at risk.
2. Determine why the collection failed, when evidence is available.
3. Decide whether any intervention is appropriate.
4. Select a bounded recovery path instead of repeatedly attempting the same action.
5. Escalate cases that are ambiguous, high-value, or outside automated policy.
6. Verify whether the intervention actually resulted in collected revenue.
7. Report both successful recoveries and unresolved exceptions.

The challenge is to turn these decisions into a single, explainable, auditable AI-assisted recovery workflow.

---

## 3. Vasooli's Narrow Scope

Vasooli deliberately focuses on **failed recurring subscription payments on Razorpay Subscriptions in Test Mode**.

The system will not attempt to solve every revenue-loss problem in Track 03. It will focus deeply on one concrete workflow:

> **When a recurring subscription payment fails, determine whether revenue is recoverable, diagnose the available evidence, choose a bounded recovery intervention, execute the appropriate test-mode workflow, verify the result, and measure the revenue recovered.**

This narrow scope is intentional. It allows the project to demonstrate a complete loop rather than implementing several shallow recovery features.

---

## 4. Who Is the User?

### Primary user

**Merchant / merchant operations team** using Razorpay for recurring payments.

The merchant needs to answer questions such as:

- Which subscriptions are currently putting revenue at risk?
- Why did the collection fail, based on available evidence?
- Should the merchant do anything now, or should the existing payment retry lifecycle be allowed to continue?
- Which cases require a recovery intervention?
- Which cases should be escalated to a human?
- How much money has actually been recovered?
- Which cases remain unresolved and why?

### What Vasooli provides

Vasooli acts as an **AI-assisted recovery orchestrator** around the payment lifecycle. It does not replace Razorpay's own subscription retry engine and does not give an LLM unrestricted authority over money actions.

---

## 5. Core User Journey

```text
Razorpay Test Mode
       ↓
Subscription payment failure
       ↓
Webhook received by Vasooli
       ↓
DETECT
Revenue becomes at risk
       ↓
DIAGNOSE
Normalize available failure evidence
       ↓
DECIDE
Recovery score + AI explanation
       ↓
POLICY ENGINE
Apply deterministic guardrails
       ↓
EXECUTE
 ┌──────────┬──────────────────┬──────────────┬──────────┐
 │ MONITOR  │ ONE_TIME_RECOVERY│ MANUAL_CHARGE│ ESCALATE │
 │          │                  │              │ STOP     │
 └──────────┴──────────────────┴──────────────┴──────────┘
       ↓
VERIFY
Did the intended outcome actually happen?
       ↓
MEASURE
Cash recovered vs subscription recovered
       ↓
AUDIT TRAIL + EXCEPTION LIST
```

---

## 6. Core Functional Requirements

### 6.1 Detect revenue at risk

Vasooli must identify relevant subscription events, especially failed/pending/halted states, and create a recoverable case for evaluation.

The detection layer must be event-driven and should not assume that webhook arrival order is the same as business-state order.

### 6.2 Diagnose the recovery situation

The system should normalize the available Razorpay payment/subscription evidence into an internal diagnosis such as:

- `INSUFFICIENT_FUNDS`
- `CARD_EXPIRED`
- `BANK_DECLINE`
- `MANDATE_CANCELLED`
- `UNKNOWN`

`UNKNOWN` is a valid outcome. When evidence is insufficient, Vasooli must not invent a reason; the case should be escalated or otherwise handled by policy.

### 6.3 Decide the intervention

The system must determine whether an action is necessary and, when appropriate, select the most suitable bounded recovery path.

Potential actions:

- `MONITOR` — allow the normal Razorpay-managed retry lifecycle to continue.
- `ONE_TIME_RECOVERY` — create a one-time Payment Link when a one-time collection is appropriate.
- `MANUAL_CHARGE` — use only when an eligible issued invoice and supported payment method allow it.
- `ESCALATE` — route uncertain, high-value, unsupported, or policy-sensitive cases for human handling.
- `STOP` — hard-stop recovery for explicit cancellation/opt-out or other policy-defined conditions.

### 6.4 Execute safely

Every action must be bounded by deterministic policies such as:

- maximum automated attempt threshold;
- no automated recovery after explicit customer opt-out or mandate cancellation;
- human escalation above a merchant-defined amount threshold;
- no manual charge when the invoice/payment method is ineligible;
- no action when the subscription is already recovered;
- no repeated action caused by a duplicate webhook.

### 6.5 Verify the result

An action request is not a recovery result.

Vasooli must verify the appropriate evidence for the action that was executed.

For example:

```text
ONE_TIME_RECOVERY
      ↓
Payment Link created
      ↓
Customer pays
      ↓
payment/payment-link evidence confirms success
      ↓
Cash recovered
```

For subscription recovery, the subscription state must be checked separately. A one-time Payment Link payment must never be represented as automatic subscription reactivation.

### 6.6 Measure recovery

The batch evaluation must report measurable outcomes, including at minimum:

- total revenue at risk;
- number of recovery cases;
- recovered cash;
- unrecovered amount;
- recovery rate;
- action distribution;
- exception count;
- exception reasons.

Where applicable, Vasooli will separately report:

- **₹ Cash Recovered**
- **₹ Subscription Revenue Reactivated**

These metrics must not be conflated.

---

## 7. AI Requirement

AI must be used meaningfully, but Vasooli will not use an LLM for every step.

### Intended architecture

```text
Razorpay event
      ↓
Feature Engine
      ↓
Recovery Score
      ↓
Optional LLM Explanation
      ↓
Deterministic Policy Engine
      ↓
Final Action
```

The LLM can provide natural-language reasoning or contextual explanation, but it is **non-authoritative** for money actions.

The deterministic policy engine has final authority.

Example:

```text
LLM:
"Recovery appears likely; retry recommended."

Policy:
maximum automated attempts already reached

Final:
STOP / ESCALATE
```

This demonstrates deliberate AI judgment: the system uses AI where it adds value and intentionally does not use an LLM as an unrestricted payment controller.

---

## 8. Safety, Compliance and Trust Requirements

Because the workflow concerns money recovery, the system must be bounded and auditable.

### Required controls

1. **Webhook signature verification** before accepting an event as trusted.
2. **Event deduplication** using Razorpay's event identifier.
3. **Out-of-order tolerance** through state reconciliation rather than event-sequence assumptions.
4. **Hard stopping rules** for cancellation/opt-out and retry limits.
5. **Human escalation** for uncertain or high-risk cases.
6. **Action-specific verification** before declaring money recovered.
7. **Audit trail** for every decision and action.
8. **Exception reporting** for cases the system cannot resolve.

---

## 9. Batch-Level Evaluation Requirement

The project must not rely on a few hand-picked successful examples.

Vasooli will use a synthetic batch of approximately **500–2,000 subscription recovery cases** for evaluation.

The synthetic data will be explicitly labeled as simulation data. Failure distributions will be configurable assumptions, not claims about real-world BFSI prevalence.

A smaller set of actual Razorpay Test Mode flows will demonstrate the real integration.

### Evaluation example

```text
1,500 synthetic subscription cases
          ↓
320 revenue-at-risk cases
          ↓
Agent diagnoses + policy decisions
          ↓
Recovery workflows
          ↓
Measured outcomes

Revenue at risk       ₹X
Cash recovered        ₹Y
Subscription recovery ₹Z
Unrecovered            ₹A
Exceptions             N
```

The exact numbers will only be reported after the system is built and evaluated.

---

## 10. Honest Exception Handling

A strong result is not one where every case is artificially classified as recovered.

Vasooli must explicitly show what it could not resolve.

Example:

```text
Case: sub_1042
Amount: ₹2,999
Diagnosis: CARD_EXPIRED
Action: ONE_TIME_RECOVERY
Result: Customer did not complete payment
Recovered: ₹0
```

Another:

```text
Case: sub_1088
Amount: ₹14,999
Diagnosis: UNKNOWN
Action: ESCALATE
Result: Awaiting human intervention
Recovered: ₹0
```

These exceptions are part of the product's evidence, not merely debugging output.

---

## 11. What Makes Vasooli Different

Vasooli is not positioned as a generic chatbot and not as another payment retry script.

Its differentiation is the **closed-loop recovery workflow**:

```text
Detect
  +
Diagnose
  +
Decide
  +
Bounded execution
  +
Verification
  +
Measured revenue recovery
  +
Auditability
```

Specific differentiators:

### 1. Recovery, not just detection

The system is evaluated on money recovered rather than simply identifying failed payments.

### 2. AI with bounded authority

The LLM can explain or assist with reasoning, while deterministic guardrails control money actions.

### 3. Honest recovery accounting

Cash collected through a one-time recovery flow is separated from actual subscription reactivation.

### 4. Explicit uncertainty

Unknown cases are escalated rather than hallucinated into confident diagnoses.

### 5. Batch-level evidence

The project demonstrates performance across a complete synthetic batch instead of cherry-picked examples.

### 6. Auditability

Each recovery decision has a traceable reason, policy decision, action, result, and exception status.

---

## 12. What Vasooli Is Not

To keep the project technically honest and tightly scoped:

- It is **not** a replacement for Razorpay's own subscription retry engine.
- It is **not** an unrestricted autonomous payment agent.
- It does **not** claim that a Payment Link reactivates a subscription automatically.
- It does **not** claim that synthetic failure distributions represent real BFSI statistics.
- It does **not** process real customer money.
- It does **not** depend on thousands of real Razorpay test transactions.
- It does **not** force an AI-generated diagnosis when the underlying evidence is insufficient.

---

## 13. Buildathon Success Criteria

Vasooli should be considered successful only if the final system demonstrates all of the following:

### MUST

- Detect a real failed subscription event in Razorpay Test Mode.
- Receive and securely process the corresponding webhook.
- Diagnose available failure evidence with an `UNKNOWN` fallback.
- Apply deterministic recovery guardrails.
- Execute at least one real Test Mode recovery workflow.
- Verify whether that workflow actually resulted in collection.
- Measure recovery across a batch of synthetic records.
- Show recovered revenue and unresolved exceptions.
- Maintain an audit trail.
- Demonstrate at least one failure/edge case and how the system handled it.

### SHOULD

- Recovery scoring beyond simple hardcoded rules.
- Optional LLM explanation layer.
- Exception-list dashboard.
- Dual cash-recovery vs subscription-recovery metrics.
- Strong state-reconciliation handling.

### NICE TO HAVE

- More polished dashboard.
- Multiple recovery strategies.
- Advanced scoring model.
- Hosted demo.
- Additional analytics and visualizations.

---

## 14. Final Problem Statement — Pitch Version

> **Merchants lose recurring revenue every time a subscription payment fails, but a failed payment is not always a lost customer. The real problem is deciding what to do next. Vasooli is an AI-assisted revenue recovery agent that detects failed subscription payments, diagnoses the available failure evidence, chooses a bounded recovery intervention, verifies the actual outcome, and measures how much revenue was recovered across a batch. It uses AI for reasoning where useful, deterministic policies for money-action safety, and maintains a full audit trail with honest exception reporting.**

---

## 15. Razorpay Buildathon Alignment

This project directly maps to Track 03:

| Razorpay Track 03 requirement | Vasooli implementation |
|---|---|
| Detect revenue at risk | Detect failed/pending/halted subscription cases |
| Determine the right intervention | Recovery scoring + diagnosis + policy engine |
| Execute bounded recovery workflow | Monitor, one-time recovery, eligible manual charge, escalate, stop |
| Payment-failure use case | Failed recurring subscription payment recovery |
| Measured money recovered | Batch-level ₹ recovery metrics |
| Compliant escalation | Human escalation + hard stop rules |
| Stopping rules | Policy engine with deterministic limits |
| Audit trail | Immutable event/action/decision history |
| Honest exception handling | First-class unresolved-case list |
| Meaningful AI | Recovery reasoning/explanation without giving the LLM unrestricted money authority |

Razorpay's official Buildathon page defines Track 03 as **AI Revenue Recovery** and sets the bar at measured money recovered across a batch with compliant escalation, stopping rules, and an audit trail. citehttps://razorpay.com/buildathon/

---

## 16. One-Sentence Product Definition

> **Vasooli is an AI-assisted recovery orchestrator that turns failed recurring-payment events into bounded, verified, and measurable revenue-recovery workflows.**
