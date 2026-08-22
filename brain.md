# Vasooli - Project Brain
sk-50a6fcc525cb6b4b-900df9-71de3132
This document serves as the core context and memory for AI agents working on the Vasooli project. Read this to understand the project architecture, goals, and constraints.

## Project Overview
- **Name**: Vasooli
- **Track**: Razorpay AI Buildathon - Track 03: AI Revenue Recovery
- **Goal**: Detect failed recurring subscription payments, diagnose the cause, decide on a recovery action (using policy + AI), execute, verify, and measure.
- **Environment**: Razorpay Test Mode only.

## Core Architecture
```text
WEBHOOK (Verify Signature + Dedup) -> DETECT -> DIAGNOSE -> DECIDE (Policy Engine + LLM) -> EXECUTE (MONITOR / ONE_TIME_RECOVERY / MANUAL_CHARGE / ESCALATE / STOP) -> VERIFY -> MEASURE -> AUDIT
```

## Non-Negotiable Rules
1. **Razorpay is the source of truth**: Vasooli orchestrates recovery around Razorpay's retry engine, it does not replace it.
2. **UNKNOWN is a valid diagnosis**: Escalate instead of hallucinating reasons.
3. **LLM is NON-AUTHORITATIVE**: The LLM explains/scores, but the deterministic Policy Engine always makes the final decision on actions.
4. **Cash Recovered ≠ Subscription Reactivated**: Track one-time recovery (cash) separately from subscription reactivation.
5. **State Reconciliation**: Reconcile state from the DB, not from webhook arrival order (webhooks can be out of order).

## Execution Steps
1. **Setup & Foundation Proof**: Test Mode account, Plan, Subscription, dummy webhook hit (MUST).
2. **Webhook Ingestion**: Signature verification, dedup (`x-razorpay-event-id`), out-of-order tolerance (MUST).
3. **Synthetic Dataset**: Generate 500-2000 records for evaluation (MUST).
4. **Diagnose + Decide Engine**: Policy engine for decision-making (MUST).
5. **Execute Recovery**: Call Razorpay Test API for the selected action (MUST).
6. **Verify + Measure**: Check payment state, show ₹ recovered (MUST).
7. **Batch Eval & Prep**: Pitch video, cleanup, submission answers (MUST).

## Developer Notes
- Ensure no AI assistant names (like Claude, Gemini) appear in git commits or documentation files.
- Stick to the 7-step plan. Do not build features out of order.
