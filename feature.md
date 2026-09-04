# Vasooli AI — The Ultimate Master Guide
**Complete Playbook and Architecture Guide for Razorpay AI Buildathon 2026 (Track 03: AI Revenue Recovery)**

This in-depth document is designed specifically to prepare you. After reading this, you will be able to explain the **vision, architecture, and business impact** of your project with 100% confidence to any judge, interviewer, or tech lead. This document goes far beyond the code—it deeply covers the core business problem, the Razorpay ecosystem, and the strict rules of the hackathon.

---

## Part 1: The Core Business Problem (Why Was This Built?)

Before explaining the code to anyone, you must explain the problem that Track 03 is built upon. If you jump straight into the technical details, the business impact gets lost.

### What is "Involuntary Churn"?
When a merchant runs a business using Razorpay Subscriptions (like a SaaS platform, EdTech, or OTT platform), money is deducted automatically from the customer's card or bank account every month (via e-mandate). 
However, the bitter truth of the industry is that **around 10% to 15% of these automatic payments fail**.
The reasons for these failures vary widely:
- The customer's bank server is temporarily down (`bank_decline`).
- The customer doesn't have enough balance (`insufficient_funds`).
- The card has expired (`card_expired`).
- The customer cancelled the mandate (auto-pay permission) from their bank.

When this payment fails, the subscription halts. The merchant loses money. The tragedy here is that the customer didn't actually want to leave, but the system kicked them out due to a technical/financial hiccup. This is called **Involuntary Churn**.

### How do generic systems handle this today?
Right now, most default retry engines act as a **"Standard, Fixed-Rule"** system.
- If a payment fails, the system blindly sends a generic email without checking the reason: *"Payment failed, click here to pay full ₹999."*
- If the payment failed because the bank server was down (which is not the customer's fault), sending this email is just irritating.
- If the payment failed because the customer is out of cash, asking them for ₹999 again is foolish. They will ignore the link, and the merchant will lose a loyal customer forever.

### The "Smart" Orchestration of Vasooli AI
Vasooli AI does not replace an existing retry engine; rather, it sits on top of it as a **Context-Aware, Intelligent Agent**.
Vasooli first reads the **evidence of the failure**, checks the **customer's history (tenure)**, and then applies a **bounded decision (a calculated strategy)**:
- **Bank Down?** -> The AI says: *"MONITOR this. The standard system will automatically retry when the bank is back up. Do not bother the customer right now."*
- **Low Balance?** -> The AI says: *"They don't have ₹999 in their account. Let's send them a 'Partial Payment Link' so they can pay just 30% (₹333) right now, clear their pending cash, and continue enjoying the service."* (Note: According to the playbook, we must be honest—paying a link recovers cash, but does not automatically reactivate the subscription. These are two separate metrics).

This is Real Revenue Recovery. It’s not just about sending emails; it’s about using intelligence to retain the customer and win the money back.

### Core Fact: Who Are We Building For? (Merchant vs Razorpay)
This is the single most important architectural insight to remember:
- **Our user is NOT Razorpay!**
- Our user is the **Merchant (SaaS Founder, EdTech company, or their Finance/Operations team)** who uses Razorpay for recurring billing.
- **Razorpay is purely the Payment Rail / Cashier:** Razorpay is legally and operationally a neutral processor. Razorpay cannot unilaterally alter a merchant's contract or discount a ₹999 plan to ₹333 on its own.
- **Vasooli AI is the Merchant's Autonomous Revenue Manager:** Vasooli AI operates using the merchant's private API credentials (`RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`). The merchant owns the business and possesses the full legal and commercial authority to offer a 30% partial payment to retain a valuable customer. Vasooli AI makes this strategic decision on behalf of the merchant and commands Razorpay's APIs to execute it.

---

## Part 2: The 7-Step Technical Architecture (Under the Hood)

Vasooli AI is not a simple chatbot. It is an enterprise-grade recovery orchestrator built in 7 strict steps. You must know these 7 steps by heart:

### Step 1: Detect (Setup & Foundation Proof)
- First, a subscription is created in Razorpay Test Mode and a simulated failure is triggered.
- As soon as the payment fails, Razorpay sends a Webhook to our server (`/webhook/razorpay`). This is our starting point.

### Step 2: Ingest (Webhook Security, Idempotency & State Reconciliation)
This step showcases massive engineering depth.
- **Security Check:** To prevent hackers from sending fake data, we extract the `x-razorpay-signature` header from the incoming request. We then create an HMAC-SHA256 hash using our secret webhook key. We only accept the request if the signatures match perfectly.
- **Idempotency (Preventing Duplicates):** Due to network lags, Razorpay might send the exact same failure event twice. We extract the `x-razorpay-event-id` from the payload and store it in our SQLite database (which has a `UNIQUE` constraint). If the event already exists, the database catches the error, and we ignore it. This prevents the business logic from running twice.
- **State Reconciliation (Out-of-order tolerance):** A major rule in the playbook is that webhooks can arrive out of order. Therefore, our code does not blindly trust the sequence of arriving events. It first checks the current state in the database and, if needed, reconciles with the Razorpay API to fetch the absolute latest state.
- **Pro-Tip for Interviews:** We intentionally close the database connection (`conn.close()`) *before* calling the AI. SQLite locks the entire database when open, and an AI network call can take 2-3 seconds. Closing it prevents our webhook listener from freezing and allows us to instantly return a `200 OK` to Razorpay.

### Step 3: Synthetic Dataset Generator
- Razorpay Test Mode has strict limits on generating "Subscription Links" and "Payment Links" (max 30 per business). Because of this, we cannot send thousands of real test webhooks.
- We built a Synthetic Dataset generator that simulates hundreds of cases (with different states like new customer, long tenure, opt-out, etc.). This allows us to perform "Batch Evaluation," which is a major requirement of the hackathon.

### Step 4: Diagnose & Decide (The AI Analyst + Bounded Policy Engine)
This step is the "Brain" of the project. It is split into two parts:
1. **The Advisory AI (Llama 3.2):** 
   - A math formula calculates a `recovery_score` based on the customer's tenure and the amount at risk.
   - We then provide a strict prompt to Llama 3.2 (vision-instruct model). We tell it to read the failure evidence and choose exactly one of these allowed actions: `MONITOR`, `ESCALATE`, `STOP`, `ONE_TIME_RECOVERY`, or `ONE_TIME_RECOVERY_PARTIAL`.
   - **Why Llama 3.2 via Omniroute?** Because GPT-4 is too slow (3-5 seconds) and expensive. Llama 3.2 running locally/via Omniroute provides the exact JSON format in milliseconds, keeping our webhook processing pipeline real-time.
2. **The Deterministic Policy Engine (The Guardrail):** 
   - You cannot blindly trust an AI with money. AI can hallucinate. 
   - Therefore, the AI's decision is never executed directly. It is first sent to the **Policy Engine (a strict Python Manager)**.
   - If the AI says "Recover this", but the amount is over ₹50,000, the Policy Engine will block the action and `ESCALATE` it for human review.
   - If the customer has Opted-Out, the Policy Engine will `STOP` it. This ensures **100% safe and bounded AI execution**.

### Step 5: Execute (Razorpay API Integration)
- Once the Policy Engine approves the action, `action_executor.py` does the real work.
- If the action is `ONE_TIME_RECOVERY`, it calls the Razorpay Payment Links API to generate a link for the full amount.
- **The Game-Changer:** If the action is `ONE_TIME_RECOVERY_PARTIAL`, it sends `accept_partial=True` and sets `first_min_partial_amount` to 33% in the Razorpay API. This officially forces the system to allow the customer to clear their pending dues by paying a much smaller amount.
- Finally, the AI generates a highly empathetic and personal message text (e.g., *"Hi Demo, we noticed a low balance..."*) which is displayed on the Dashboard for the agent to use. (Note: According to the project scope, we are not integrating a real WhatsApp API; we are only generating a smart draft).

### Step 6: Verify & Measure (Dashboard Metrics)
- A core requirement of Track 03 was "Measured Money Recovered". Just generating a link is not recovery.
- When the customer pays via that Payment Link, Razorpay sends a `payment_link.paid` webhook.
- Our system catches this webhook, marks the case as `RECOVERED` in the database, and increments the "Cash Recovered" counter on the React Dashboard.
- **Hackathon Golden Rule:** "Cash Recovered" ₹ and "Subscription Revenue Reactivated" ₹ are two completely different metrics. Paying a link recovers cash, but it does not mean the subscription is automatically reactivated. We have honestly kept these two metrics completely separate.

### Step 7: Batch Evaluation & Exceptions
- The dashboard honestly displays all "Exceptions" (like cases that were `ESCALATE`d or where the evidence was UNKNOWN). We do not hide our failures; we trace them and report them.

---

## Part 3: In-Depth Interview Q&A (Solid Defense for Razorpay Judges)

**Q1: "Razorpay has its own Smart Routing and Retry engine. What is Vasooli AI doing differently?"**
*Your Answer:* "Razorpay's retry engine focuses on blindly attempting the payment again. But for some failures (like Low Balance or Expired Card), retrying is completely pointless because the transaction will keep failing until funds are added. Vasooli AI does not *replace* Razorpay's retry engine; it sits above it and *orchestrates* it. If the bank is temporarily down, Vasooli intentionally chooses `MONITOR` and lets Razorpay's default retry do its job. But where a retry won't work (like low balance), Vasooli intervenes and creates a 'Partial Payment Link' so the customer can clear their cash dues according to their current capacity."

**Q2: "How could you give an LLM control over financial actions? That is highly unsafe, what if it hallucinates?"**
*Your Answer:* "That is exactly the beauty of this architecture—we have NOT given the LLM financial authority. Our architecture is based on a **'Non-Authoritative LLM'**. The LLM is purely an advisory analyst. It reads the data and generates a JSON recommendation. The absolute authority lies with our hardcoded **Deterministic Policy Engine**. If the transaction is of high value (e.g., 50k+) or the customer has cancelled their mandate (opted out), the Policy Engine overrides the LLM's recommendation and blocks the action (Escalate/Stop). It is 100% safe and bounded."

**Q3: "How many cases did you test for the demo? The hackathon required evaluating a batch, showing 2-3 hand-picked successes is not enough."**
*Your Answer:* "We used a dual-approach for evaluation. First, because Razorpay Test mode has strict limits on link generation, we built a Synthetic Dataset generator that simulates hundreds of cases to test edge cases (like unknown errors or high values). Second, we use the actual Razorpay Test Mode to capture real webhooks and generate real Payment Links. Our dashboard honestly reports the aggregate metrics and the Exception list from all of this."

**Q4: "What is your mechanism for Idempotency (Duplicate prevention)? If network lag causes Razorpay to send a webhook 3 times, will the customer get 3 payment links?"**
*Your Answer:* "Absolutely not. We solved this rigorously at the Database layer. Every Razorpay webhook comes with an `x-razorpay-event-id`. We placed a `UNIQUE` constraint on this column in our SQLite `webhook_events` table. If Razorpay sends the exact same event again, the database throws an `IntegrityError`. Our ingestion layer silently catches this error, refuses to run the business logic again, and immediately returns a `200 OK` so Razorpay stops retrying."

**Q5: "You mentioned webhooks don't always arrive in order. How did you handle that?"**
*Your Answer:* "That is our State Reconciliation logic. We do not blindly trust the sequence of incoming events. When a webhook arrives, we first check if it is older than our local database's projection. If the state seems ambiguous, we fetch the absolute latest truth from the Razorpay API and only then update our system. This guarantees that out-of-order events cannot corrupt our system state."

**Q6: "What is a Webhook and why don't we use standard API polling?"**
*Your Answer:* "A Webhook is an event-driven 'Call Me Back' mechanism (Reverse API):
- **Drawback of Polling:** If our server continuously polls the Razorpay API every few seconds asking 'Did any payment fail?', it creates immense, wasteful network load on both servers.
- **Webhook Efficiency (The Pizza Delivery Analogy):** Just as Domino's sends you an automated SMS when your pizza is out for delivery instead of you calling them every minute, Razorpay automatically pushes a POST request to our `/webhook/razorpay` endpoint the exact millisecond a payment fails."

**Q7: "Webhook Security: How does HMAC-SHA256 signature verification work?"**
*Your Answer:* "Because our webhook endpoint is exposed to the public internet, malicious actors could attempt to inject fake failure payloads. We prevent this using cryptographic signature verification:
1. **Shared Secret:** A secret key known only to Razorpay and our backend environment (`RAZORPAY_WEBHOOK_SECRET`).
2. **Signature Calculation:** Razorpay passes the raw request bytes and secret key through an `HMAC-SHA256` hashing algorithm and attaches the digest in the `x-razorpay-signature` header.
3. **Constant-time Comparison:** Our backend recomputes the HMAC digest over the raw incoming bytes and uses `hmac.compare_digest` to verify authenticity. If the digests do not match perfectly, the request is immediately rejected with HTTP 400 Bad Request."

**Q8: "Engineering Detail: Why explicitly close the database connection (`conn.close()`) before calling the AI?"**
*Your Answer:* "This is a critical concurrency optimization for SQLite. SQLite locks the entire database file during write operations. An external LLM call (Llama 3.2) typically takes 2–3 seconds. If we keep the database connection open during the AI call, the entire database remains locked. If subsequent webhooks arrive during that window, SQLite throws `OperationalError: database is locked`, causing ingestion failure and webhook timeouts. By explicitly calling `conn.close()` immediately after persisting the event, we release the write lock, return an instant `200 OK` to Razorpay, and allow the AI inference to run asynchronously in the background."

**Q9: "Deep-Dive: If Vasooli AI didn't exist, couldn't a merchant do the exact same thing with Razorpay's default tools?"**
*Your Answer:* "This distinction is fundamental. Razorpay is the **Execution Layer (Payment Rail)**, while Vasooli AI is the **Intelligent Decision Layer (Orchestrator)**:
- **Analogy:** Razorpay provides the car's engine and wheels; Vasooli AI is the driver steering the vehicle.
- **Default Engine Limitation:** If a customer has ₹200 and a ₹999 subscription fails, Razorpay's auto-retry blindly retries ₹999 at 24h and 48h intervals. Once exhausted, the subscription becomes `HALTED` and the customer is permanently lost. Razorpay never automatically decomposes ₹999 into a ₹333 partial recovery link.
- **Operational Scale:** A merchant with 10,000 subscriptions faces 1,500 failures monthly. No human team can manually inspect 1,500 webhooks to construct bespoke partial links. Vasooli AI autonomously evaluates tenure, failure reasons, and financial guardrails in real time."

**Q10: "Critical Question: How do we know a customer has a low balance? Do we inspect their bank account balance?"**
*Your Answer:* "Absolutely not. In strict accordance with banking privacy and BFSI compliance: **'We never access or infer the customer's exact bank balance.'** We do not know whether the customer has ₹10 or ₹500.
However, when an auto-debit fails, the issuing bank returns structured failure metadata in the transaction payload (`error_source`, `error_step`, `error_reason`, and `error_description`: e.g. *'Payment failed due to insufficient funds in customer bank account'*). Our normalizer parses this decline code into an internal diagnosis of `INSUFFICIENT_FUNDS`. We do not query account balances; we evaluate the bank's authoritative decline metadata alongside customer tenure and merchant policies to formulate a recovery offer."

**Q11: "Can Razorpay send partial payment offers itself? If Razorpay is restricted, how can Vasooli AI generate a ₹333 link?"**
*Your Answer:* "Razorpay is a neutral payment gateway.
1. **Why Razorpay cannot do this:** If Razorpay unilaterally discounted a merchant's ₹999 subscription to ₹333, the merchant would sue Razorpay for altering contractual pricing without consent. Therefore, Razorpay's default engine is strictly bound to the full subscription amount.
2. **How Vasooli AI does this:** Because Vasooli AI operates **on behalf of the Merchant** using the merchant's authorized API keys (`RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`). The merchant owns the business and has the full legal authority to offer partial payment terms. Vasooli AI passes `accept_partial=True` and `first_min_partial_amount=33300` to Razorpay's Payment Links API, which Razorpay obediently generates under the merchant's command."

---

## Part 4: Winning Demo Masterclass (The 5-Minute Pitch)

Razorpay explicitly asks for a 5-minute demo video. You must follow this script strictly:

1. **(0:00 - 0:30) Start with the Pain (The Problem):** 
   Immediately open the dashboard and say: *"Vasooli AI is not an internal feature of Razorpay. It is a Merchant-Side Revenue Operations Agent built for businesses running recurring subscriptions on Razorpay. This dashboard reflects the 'Revenue at Risk' merchants face every month from involuntary churn. Generic systems rely on blind retries and blunt emails, but Vasooli AI understands context and acts on the merchant's behalf."*
2. **(0:30 - 2:00) Show The Intelligence (The Demo):** 
   Click the Simulate button on the UI and show the AI making two completely different decisions for two different situations.
   - **Example 1 (`bank_decline`):** Show that the action was `MONITOR`. Say: *"Look, the AI didn't spam the customer. It understood it was a bank issue and correctly decided to wait."*
   - **Example 2 (`insufficient_funds`):** Show that the action was `ONE_TIME_RECOVERY_PARTIAL`. Say: *"In a low balance scenario, the AI generated a 30% partial link. We didn't use a sledgehammer; we used a scalpel."*
3. **(2:00 - 3:00) Show The Policy Guardrail (The Trust Factor):** 
   Simulate a case above 50,000 INR or an "Opt-Out" case, showing the Policy Engine blocking the AI and moving it to `ESCALATE`. Say: *"This is our safety net. An LLM might hallucinate, but our Deterministic Policy Engine never compromises on financial rules."*
4. **(3:00 - 4:00) Close the Loop (The Verification):** 
   Actually open a generated Razorpay Payment Link and complete a mock test payment. Then go back to the dashboard, refresh, and show the "Cash Recovered" counter going up. Say: *"We don't just detect problems; we honestly recover cash. And we never conflate cash recovered with subscription reactivated."*
5. **(4:00 - 5:00) Exception List & Wrap Up:** 
   Show the Exceptions list (unresolved cases) on the dashboard. Say: *"A great system knows its limits. We don't artificially mark unrecovered cases as successes; we honestly display them as exceptions."* 

Read this guide 2-3 times. If you confidently present this terminology (Idempotency, State Reconciliation, Bounded AI), the judges will be incredibly impressed!
