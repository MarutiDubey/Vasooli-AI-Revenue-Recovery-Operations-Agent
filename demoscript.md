# Vasooli AI — Master Video Demo Script (15–18 Minutes)
### Razorpay AI Buildathon 2026 — Track 03: AI Revenue Recovery

> **Recording Strategy:** 
> Do not try to memorize or record all 18 minutes in one go. 
> Record **Clip by Clip (Clip 1 to Clip 6)**. If you make a mistake in any clip, simply pause, retake that specific clip, and later stitch them together using Windows Clipchamp or CapCut.

---

## Pre-Recording Checklist
1. **Frontend Running:** `http://localhost:5173` (Zoom set to 110–115% for crisp visibility).
2. **Backend Running:** FastAPI Uvicorn server running on `http://127.0.0.1:8000`.
3. **Browser Tabs Prepared:**
   - Tab 1: Vasooli AI Dashboard (`http://localhost:5173`)
   - Tab 2: Razorpay Dashboard (Test Mode) or Architecture Diagram / Slides
4. **Audio Check:** Use earphones/headset mic. Speak at a steady, calm, conversational pace.

---

## CLIP 1: Problem Statement, Market Pain & Vasooli AI Vision
**Target Duration:** ~2.5 – 3 Minutes  
**On Screen:** Vasooli AI Dashboard (Header showing "Revenue at Risk" and stats bar) OR clean presentation slide.

### [Screen Action]
*Start on the Dashboard. Point your mouse cursor to the top KPI cards: "Total Revenue at Risk" and "Cases Evaluated".*

### [Spoken Script]
> "Hello everyone, and welcome to our demonstration of **Vasooli AI** — an Autonomous Revenue Recovery Operations Agent built for **Razorpay AI Buildathon 2026, Track 03: AI Revenue Recovery**."
>
> "Before we look at the live code and demo, let’s talk about the real-world financial bleeding that merchants face every single day: **Involuntary Churn**."
>
> "When a merchant runs a recurring subscription business on Razorpay — such as a SaaS platform, an EdTech company, or a digital media platform — recurring revenue is collected via automated mandates. However, industry benchmarks show that between **10% to 15% of all recurring payments fail**."
>
> "These failures happen for a variety of reasons: temporary bank outages, expired cards, or simply temporary insufficient funds in the customer's account."
>
> "Now, here is the fundamental problem with existing generic systems: default retry mechanisms operate as a **blunt, fixed-rule machine**. If an automatic debit fails, the system repeatedly attempts to debit the full amount — say, ₹999 — at standard intervals, and sends generic, impersonal failure emails. If the customer is facing a temporary liquidity crunch, asking them for the full ₹999 repeatedly achieves nothing. The retries exhaust, the subscription moves to a `HALTED` state, and the merchant loses a high-value customer permanently."
>
> "This is where **Vasooli AI** changes the paradigm. Vasooli AI is **not** an internal feature of Razorpay, and it does not replace Razorpay’s payment rail. Rather, Vasooli AI is an **Intelligent Merchant-Side Revenue Operations Agent**."
>
> "Razorpay acts as the execution infrastructure — the engine and wheels. Vasooli AI acts as the intelligent driver sitting on the merchant's side, analyzing failure metadata, evaluating customer tenure and lifetime value, and dynamically choosing the most bounded, empathetic, and effective recovery intervention."
>
> "Let’s take a look at the technical architecture that powers this decision engine."

---

## CLIP 2: Technical Architecture & Core Engineering Depth
**Target Duration:** ~2.5 – 3 Minutes  
**On Screen:** Architecture Diagram / README flowchart / Terminal showing FastAPI backend startup.

### [Screen Action]
*Click the **"Architecture & Docs"** tab in the navbar. The embedded System Blueprint and 7-step pipeline cards appear right inside the app! Highlight the flow from Razorpay Webhook -> Ingestion -> AI Analyst -> Policy Engine -> Execution.*

### [Spoken Script]
> "Our architecture is engineered as a robust, 7-step closed loop, built strictly to the high safety standards demanded by financial workflows."
>
> "Let’s walk through the key architectural layers:"
>
> "First, **Webhook Ingestion and Security**: Our endpoint `/webhook/razorpay` receives real-time failure events from Razorpay. Because this endpoint is public, we implement strict cryptographic security: every payload is validated using **HMAC-SHA256 signature verification** against our configured `RAZORPAY_WEBHOOK_SECRET` using constant-time comparison to prevent timing attacks. Unauthenticated requests are immediately rejected."
>
> "Second, **Event Idempotency**: Payment networks can deliver the same webhook multiple times due to retries or network latency. We extract the unique `x-razorpay-event-id` and persist it in our SQLite database with a `UNIQUE` constraint. Duplicate events trigger an integrity catch, returning an instant `200 OK` without executing redundant recovery workflows."
>
> "Third, **State Reconciliation and Out-of-Order Tolerance**: Webhooks can arrive out of chronological order. Our state machine never assumes arrival sequence is business truth. It cross-checks local state and, when ambiguous, reconciles directly with authoritative provider resources before updating projections."
>
> "Fourth, **Database Concurrency Optimization**: In our backend (`app/state_mapper.py`), we explicitly close the SQLite database connection (`conn.close()`) immediately after persisting the event, *before* triggering the LLM inference. Because SQLite locks the entire database file during writes, closing the connection early ensures our webhook listener never freezes or times out during the 2-second LLM call."
>
> "Fifth, and most importantly: **The Non-Authoritative AI Philosophy**. We use **Gemini 3.7 Flash** as an advisory analyst. The LLM evaluates failure evidence and proposes a structured JSON recommendation. However, the LLM is given **zero direct authority** over financial actions. Every recommendation must pass through our deterministic, hardcoded **Policy Engine**."
>
> "Let’s now jump into the live dashboard and see these decisions in action."

---

## CLIP 3: Live Demo — Intelligent Diagnosis & Strategic Recovery Actions
**Target Duration:** ~3 – 3.5 Minutes  
**On Screen:** Vasooli AI React Dashboard (`http://localhost:5173`).

### [Screen Action]
*Click on the "Simulate Payment Failure" button. Watch the new case appear in the table with its badge, diagnosis, action, and AI-generated recovery message.*

### [Spoken Script]
> "Here we are on the **Vasooli AI Operations Dashboard**. This interface is designed for the merchant's revenue operations and finance teams to monitor at-risk revenue in real time."
>
> "Let’s trigger our first scenario by simulating a failed recurring subscription charge."
>
> *(Click Simulate button)*
>
> "Look at what happened instantly: A subscription payment of ₹999 failed. Let's look at the Diagnosis column."
>
> "In Scenario 1, the failure reason returned by the bank is `bank_decline` — indicating a temporary core banking server outage. Notice what the AI decided: the Recommended Action is **`MONITOR`**."
>
> "Why `MONITOR`? Because a smart agent understands context. The customer did not cause this failure, and their account is healthy. Sending an aggressive payment reminder would only irritate the customer. Vasooli AI intelligently chooses to wait and allows Razorpay’s native retry schedule to collect the funds when the bank recovers."
>
> "Now, let’s simulate a different failure: **`insufficient_funds`**."
>
> *(Click Simulate button again)*
>
> "Look at this second case: The customer has a tenure of over 12 months, but the auto-debit failed due to low balance. Standard systems would repeatedly attempt to charge ₹999 and fail."
>
> "Vasooli AI took a completely different approach: It recommended **`ONE_TIME_RECOVERY_PARTIAL`**."
>
> "Because our backend operates with the Merchant's API credentials, it has the commercial authority to offer flexible terms. Vasooli AI commanded Razorpay’s Payment Links API to generate a link with `accept_partial=True` and set the `first_min_partial_amount` to 33% — exactly ₹333."
>
> "Furthermore, look at the AI-generated customer message: it is empathetic, highly personalized, mentions the customer's loyalty, and clearly communicates that they can pay just 30% now to maintain uninterrupted access."
>
> "Instead of a blunt sledgehammer, Vasooli AI uses a precise, empathetic scalpel to save the customer relationship."

---

## CLIP 4: Live Demo — Safety Guardrails & The Deterministic Policy Engine
**Target Duration:** ~2.5 – 3 Minutes  
**On Screen:** Dashboard showing an Escalated or Stopped case, or code inspection of `app/policy_engine.py`.

### [Screen Action]
*Scroll down to highlight a case where the Action is marked as `ESCALATE` (orange badge) or `STOP` (red badge). Show the guardrail explanation in the table.*

### [Spoken Script]
> "One of the most critical questions judges and enterprise merchants ask is: **'How do you prevent an AI from going rogue with money actions?'**"
>
> "This brings us to our **Deterministic Policy Engine** (`app/policy_engine.py`). In our architecture, the LLM is strictly advisory. The Policy Engine enforces non-negotiable business rules that override any AI hallucination."
>
> "Let’s demonstrate three key guardrails:"
>
> "First, **The High-Value Threshold**: If a failed transaction exceeds ₹50,000, automated intervention is deemed too risky for autonomous execution. Even if the AI recommends immediate recovery, the Policy Engine catches the threshold, overrides the recommendation, and sets the decision to **`ESCALATE`** for human review."
>
> "Second, **Customer Opt-Out & Mandate Cancellation**: If the customer has explicitly cancelled their mandate or opted out of communications, the Policy Engine triggers a hard **`STOP`**. No payment link is ever generated. This guarantees complete regulatory compliance and prevents customer harassment."
>
> "Third, **Unknown Signals**: If the failure metadata is contradictory or unmapped, the system refuses to invent a reason. It tags the diagnosis as `UNKNOWN` and routes the case to human escalation."
>
> "By separating probabilistic AI reasoning from deterministic financial policy, we ensure enterprise-grade safety."

---

## CLIP 5: Real Razorpay Payment Link & Verification Loop
**Target Duration:** ~3 Minutes  
**On Screen:** Click on the generated Payment Link URL -> Opens Razorpay Checkout page (`https://rzp.io/...`) -> Complete test payment -> Return to Dashboard and show updated metrics.

### [Screen Action]
*Click on the Razorpay Link URL in the dashboard table. A new tab opens showing the official Razorpay test payment interface with the partial payment option.*

### [Spoken Script]
> "Now, let’s close the loop by demonstrating actual cash recovery through the real Razorpay integration."
>
> "In the dashboard row for our partial recovery case, you can see the generated Razorpay Payment Link. Let’s click on it."
>
> *(Click the link — Razorpay test checkout page opens)*
>
> "Notice the checkout page: It is hosted on Razorpay's infrastructure (`rzp.io`). Because Vasooli AI enabled partial payments, the customer has the option to pay the minimum amount of ₹333 instead of the full ₹999."
>
> "Let’s complete this test payment using standard Razorpay test credentials."
>
> *(Type in test card details: 4111 1111 1111 1111, any future date, CVV 123, click Pay, and click Success on the bank OTP page)*
>
> "The payment is successful! Razorpay now fires a `payment_link.paid` webhook back to our Vasooli AI server."
>
> *(Switch back to the Vasooli Dashboard tab and click Refresh / observe auto-update)*
>
> "Look at the dashboard now: The case status has transitioned to **`RECOVERED`**."
>
> "More importantly, look at our top metric cards: **Cash Recovered** has increased by the exact collected amount!"
>
> "Here is a vital nuance that sets our project apart: **Honest Recovery Accounting**. We strictly separate **₹ Cash Recovered** from **₹ Subscription Revenue Reactivated**."
>
> "A one-time payment link settles outstanding cash, but it does not automatically re-establish the recurring subscription mandate in Razorpay. We do not conflate these metrics, maintaining complete accounting honesty."

---

## CLIP 6: Batch Evaluation, Honest Exceptions & Conclusion
**Target Duration:** ~2 – 2.5 Minutes  
**On Screen:** Exception List section of the Dashboard / Terminal showing batch evaluation statistics.

### [Screen Action]
*Scroll to the Exception List / Audit Log section at the bottom of the dashboard. Then, click on the **"Interview FAQ"** tab in the navbar to show the embedded FAQ section. Click on a question (like Q4 or Q10) to expand the answer with the animated '+' icon.*

### [Spoken Script]
> "Finally, let’s look at how Vasooli AI handles scale and exceptions."
>
> "Track 03 explicitly states: *'Don't just identify the problem. Show measured money recovered across a batch, with compliant escalation, stopping rules, and an audit trail.'*"
>
> "Because Razorpay Test Mode imposes a limit of 30 payment links per business, we built a reproducible **Synthetic Dataset Generator** that evaluates our decision and policy pipeline across a batch of hundreds of varied cases."
>
> "Look at our **Exception List**: A mature financial operations system is measured not by claiming a fake 100% recovery rate, but by how transparently it handles cases it could not automate."
>
> "Here, our dashboard clearly itemizes every unrecovered case: cases escalated due to high value, cases halted due to mandate cancellation, and cases where payment links expired."
>
> "Every state transition, webhook ID, and policy rule is logged in an immutable audit trail."
>
> "To conclude:"
>
> "Vasooli AI bridges the crucial gap between a failed payment signal and a recovered rupee. By combining **Razorpay’s powerful payment infrastructure** with an **intelligent, bounded, and context-aware decision layer**, we empower merchants to automatically safeguard recurring revenue and eliminate involuntary churn."
>
> "Thank you for watching, and we look forward to your questions!"

---

## Post-Recording Assembly Instructions (Windows Clipchamp)
1. Open **Clipchamp** (pre-installed on Windows 11).
2. Drag and drop all 6 recorded `.mp4` clips into the media library.
3. Place them sequentially on the timeline: `Clip 1` -> `Clip 2` -> `Clip 3` -> `Clip 4` -> `Clip 5` -> `Clip 6`.
4. Trim any awkward pauses at the start and end of each clip.
5. Add a simple fade-in and fade-out transition between clips.
6. Export as **1080p MP4**. Your final video will be clean, professional, and well within the 15–18 minute timeframe!
