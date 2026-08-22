# Vasooli — Step 1: Setup & Foundation Proof

### Razorpay AI Buildathon — Track 03: AI Revenue Recovery

> **Status:** MUST / Foundation Gate  
> **Goal:** Prove that Vasooli can reach Razorpay Test Mode, create a test subscription, trigger a real test subscription failure, and receive the corresponding webhook.  
> **Do not build yet:** AI reasoning, synthetic batch engine, recovery policy, dashboard, production deployment, or full DB state reconciliation.

---

## 1. Step Objective

Step 1 exists to remove the highest-risk unknown before building the rest of Vasooli:

```text
Razorpay Test Mode
      ↓
API access works
      ↓
Test Plan exists
      ↓
Test Subscription exists and is authenticated
      ↓
Webhook endpoint is reachable
      ↓
Trigger a test charge failure
      ↓
subscription.pending webhook arrives
      ↓
Foundation proven
```

Razorpay's current Test Subscriptions documentation explicitly recommends configuring a test webhook before creating subscriptions, then creating a Plan and Subscription. It also supports simulating subsequent charges in Test Mode and choosing a failure result, which moves the subscription to `pending` and triggers `subscription.pending`. citeturn270340search0turn270340search6

**Step 1 is complete only when the webhook event is actually received by our endpoint.**

---

## 2. Scope

### MUST

- Razorpay account/dashboard accessible in **Test Mode**
- Test API Key ID + Secret generated
- Secrets stored locally, never committed
- One test webhook configured
- One test Plan created
- One test Subscription created
- Subscription authentication completed
- Local webhook receiver running
- Public/reachable tunnel configured for the local webhook
- One test subscription charge deliberately triggered as **Failure**
- `subscription.pending` received and visibly confirmed
- Basic evidence captured for the README/build log

### NOT part of Step 1

- Signature verification implementation — Step 2
- `x-razorpay-event-id` deduplication — Step 2
- Out-of-order state reconciliation — Step 2
- SQLite/SQLAlchemy schema — Step 2
- Synthetic 500–2,000 record generator — Step 3
- Recovery scoring — Step 4
- LLM — Step 4 (optional)
- Payment Link execution — Step 5
- Dashboard — Step 6
- Batch evaluation — Step 7

**Important:** Step 1 may receive a real Razorpay webhook before signature validation is implemented. Treat the endpoint as a temporary foundation proof, not as production-safe webhook ingestion.

---

## 3. Prerequisites

### Local machine

Required:

- Python 3.x
- `pip`
- Git
- Terminal / PowerShell
- A code editor

### Razorpay

- Razorpay account
- Dashboard access
- **Test Mode enabled**
- Test API keys

Razorpay's subscription test documentation says to use the Test `KEY_ID` and `KEY_SECRET` generated from the Dashboard while testing. citeturn270340search0

### Internet exposure for local webhook

Razorpay must be able to reach the webhook endpoint. For local development, use a supported tunnel. Razorpay's webhook validation/testing documentation currently points developers to **zrok** because many common tunneling services are blacklisted by Razorpay's security restrictions. citeturn270340search2

---

## 4. Create the Project Skeleton

Recommended minimal structure:

```text
vasooli/
├── app/
│   ├── __init__.py
│   └── main.py
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

For Step 1, keep this intentionally tiny.

### `requirements.txt`

```text
fastapi
uvicorn[standard]
python-dotenv
```

Do **not** add SQLAlchemy, ML libraries, LLM SDKs, React, or Razorpay business logic yet.

---

## 5. Create Environment Variables

### `.env`

```text
RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxxxxx
RAZORPAY_KEY_SECRET=xxxxxxxxxxxxxxxxxxxx
RAZORPAY_WEBHOOK_SECRET=change-me-after-webhook-creation
```

### `.env.example`

```text
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
RAZORPAY_WEBHOOK_SECRET=
```

### `.gitignore`

```text
.env
.venv/
__pycache__/
*.pyc
```

### Security rule

**Never commit the real `RAZORPAY_KEY_SECRET` or webhook secret to GitHub.**

Step 1 is local/test-only; do not use Live Mode credentials.

---

## 6. Generate Razorpay Test API Keys

In Razorpay Dashboard:

```text
Test Mode
   ↓
Account / API Keys
   ↓
Generate Test Keys
```

Store the resulting:

```text
KEY ID      → RAZORPAY_KEY_ID
KEY SECRET  → RAZORPAY_KEY_SECRET
```

### Checkpoint A

Confirm:

```text
RAZORPAY_KEY_ID starts with rzp_test_
```

Do not paste the secret into the terminal output, README, screenshots, GitHub, or chat.

---

## 7. Build the Smallest Possible Webhook Receiver

### `app/main.py`

```python
from fastapi import FastAPI, Request

app = FastAPI(title="Vasooli Step 1")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/webhooks/razorpay")
async def razorpay_webhook(request: Request) -> dict[str, str]:
    body = await request.body()

    print("\n--- Razorpay webhook received ---")
    print("bytes:", len(body))
    print("event_id:", request.headers.get("x-razorpay-event-id"))
    print("signature_present:", bool(request.headers.get("x-razorpay-signature")))
    print("---------------------------------\n")

    # Step 2 will add signature verification, parsing,
    # event deduplication, persistence, and state reconciliation.
    return {"status": "received"}
```

Run:

```bash
uvicorn app.main:app --reload --port 8000
```

Then verify:

```text
http://127.0.0.1:8000/health
```

Expected:

```json
{"status":"ok"}
```

---

## 8. Expose the Webhook Endpoint

Use a supported local tunnel such as **zrok**.

The exact zrok installation command depends on the current zrok release/platform, so use the current official zrok installation instructions rather than hard-coding an outdated command here.

Once zrok is configured, expose:

```text
http://127.0.0.1:8000
```

You need a public HTTPS URL equivalent to:

```text
https://<public-host>/webhooks/razorpay
```

### Checkpoint B

Open the public URL for `/health` and confirm it reaches your FastAPI application.

Expected:

```json
{"status":"ok"}
```

If the public health URL does not work, **stop here**. Do not continue to Razorpay webhook configuration yet.

Razorpay's current webhook testing docs state that Test Mode can use a staging/local endpoint exposed through a supported tunnel, and specifically mention zrok because many common tunneling services are blacklisted. citeturn270340search2

---

## 9. Configure a Razorpay Test Webhook

In Razorpay Dashboard, keep **Test Mode** enabled and configure a webhook for the public endpoint:

```text
https://<public-host>/webhooks/razorpay
```

Create a strong webhook secret and place the same value in:

```text
RAZORPAY_WEBHOOK_SECRET
```

For Step 1, configure the minimum subscription events needed for the foundation proof:

```text
subscription.activated
subscription.charged
subscription.pending
subscription.halted
```

Do not configure dozens of unrelated events yet.

### Important

Razorpay sends a signature in `X-Razorpay-Signature`. Signature verification will become mandatory in Step 2. Razorpay's current docs state that the signature is HMAC-SHA256 using the webhook secret and the **raw webhook request body**. citeturn270340search2

---

## 10. Create the Test Plan

Razorpay requires a Plan before a Subscription can be created. Plans can be created from the Dashboard or via the Subscriptions API. citeturn270340search1turn270340search3

### Recommended test plan

Keep the plan simple:

```text
Name: Vasooli Test Monthly
Frequency: Monthly
Amount: small test amount
Currency: INR
Description: Vasooli buildathon test plan
```

Use a small test amount. This is a Test Mode workflow; no live-money transaction should be used for this project.

### Save

Record the generated:

```text
plan_id
```

Example:

```text
plan_xxxxxxxxxxxxx
```

Do not put API secrets into the README.

---

## 11. Create the Test Subscription

Razorpay's official subscription flow is:

```text
Plan
 ↓
Subscription
 ↓
Authentication payment
 ↓
Active subscription
 ↓
Subsequent test charge
```

Razorpay's API supports creating the subscription through `POST /v1/subscriptions`. The test documentation notes that API-created subscriptions initially require an authentication transaction; after authentication, the subscription becomes active. citeturn270340search0turn270340search5

### For Step 1, prefer the simplest route

Use the Razorpay Dashboard/Test Subscription flow if it reduces setup complexity. If you create the Subscription through the API, follow Razorpay's documented checkout/authentication flow.

### Save

Record:

```text
subscription_id
plan_id
status
```

---

## 12. Complete Subscription Authentication

This checkpoint matters because a subscription must reach a usable state before you can meaningfully simulate a subsequent charge.

Razorpay's Test Subscriptions documentation describes the authentication payment and states that after successful authentication the subscription moves to `active`; a subsequent successful charge can produce `subscription.charged`. citeturn270340search0

### Checkpoint C

Dashboard/API should show something equivalent to:

```text
Subscription state: active
```

and you should have seen the appropriate activation/charge webhook events if applicable.

---

## 13. Trigger the Foundation Failure

This is the most important action in Step 1.

Razorpay's Test Mode allows a subsequent subscription charge to be simulated from the Dashboard using **Charge this now**, including choosing a failure result. Razorpay documents that when the test charge is simulated as a failure, the subscription moves from `active` to `pending` and a `subscription.pending` webhook is triggered. citeturn270340search0turn270340search6

### Procedure

```text
Active Test Subscription
        ↓
Charge this now
        ↓
Choose Failure
        ↓
Razorpay processes simulated failure
        ↓
Subscription → pending
        ↓
subscription.pending webhook
        ↓
FastAPI endpoint receives POST
```

### Checkpoint D — THE FOUNDATION GATE

Your terminal should show evidence similar to:

```text
--- Razorpay webhook received ---
bytes: <non-zero>
event_id: <non-empty>
signature_present: True
---------------------------------
```

And Razorpay Dashboard/API should show:

```text
subscription.status = pending
```

**Do not proceed to Step 2 until this works.**

---

## 14. What Counts as Success?

Step 1 is **PASS** only if all of these are true:

```text
[PASS] Test Mode enabled
[PASS] Test API keys generated
[PASS] Local FastAPI server running
[PASS] Public HTTPS tunnel reachable
[PASS] Razorpay test webhook configured
[PASS] Test Plan created
[PASS] Test Subscription created
[PASS] Subscription authenticated / usable for test charge
[PASS] Test charge failure triggered
[PASS] subscription.pending received by our endpoint
[PASS] Razorpay Dashboard/API confirms pending state
```

### Step 1 PASS condition

> **A real Razorpay Test Mode failure causes a `subscription.pending` webhook to reach Vasooli's endpoint.**

That single sentence is the foundation proof.

---

## 15. Evidence to Capture

Create:

```text
notes/
└── step-1-proof.md
```

Record:

```text
Date:
Test Mode:
Plan ID:
Subscription ID:
Webhook endpoint:
Triggered event:
Observed subscription state:
```

Do **not** record:

```text
API Secret
Webhook Secret
```

Recommended screenshots/evidence:

1. Razorpay Dashboard in Test Mode showing the test Plan.
2. Test Subscription showing its state.
3. Test charge failure action/result.
4. Terminal showing the received webhook.
5. Public health endpoint working.

Redact secrets from every screenshot.

---

## 16. Troubleshooting Order

When something fails, debug in this exact order.

### A. `/health` fails locally

Check:

```text
Python environment
FastAPI installation
uvicorn command
port 8000
```

### B. `/health` works locally but not publicly

Check:

```text
tunnel process
public HTTPS URL
port forwarding
firewall/network
```

### C. Razorpay webhook does not arrive

Check:

```text
Test Mode is enabled
webhook URL is public HTTPS
webhook event is configured
subscription is actually active/usable
failure was triggered on the same Test environment
```

### D. Subscription cannot be charged in Test Mode

Check:

```text
subscription authentication completed
subscription is active
within the documented test-token validity window
```

Razorpay's Test Subscription documentation notes that subsequent debits in test mode have a token-validity window, so do not leave an authenticated test subscription unused for too long before attempting the subsequent charge. citeturn270340search0

### E. Webhook arrives but looks wrong

For Step 1, only prove receipt.

Do **not** start changing event parsing or business logic yet. Step 2 will implement:

```text
raw body
 ↓
signature verification
 ↓
event ID dedup
 ↓
payload parsing
 ↓
state reconciliation
```

---

## 17. Common Mistakes to Avoid

### Mistake 1 — Starting with the AI

Do not build the LLM/recovery engine before the Razorpay foundation works.

### Mistake 2 — Using Live Mode

Never use production credentials for this project.

### Mistake 3 — Treating webhook receipt as verification

Step 1 only proves connectivity. Step 2 makes the webhook secure and idempotent.

### Mistake 4 — Hard-coding a T+3 assumption

The documented T+1/T+2/T+3 retry model is specifically part of the card retry model. Do not turn it into the application's universal retry logic. citeturn270340search0

### Mistake 5 — Adding every Razorpay event

Keep Step 1 deliberately small. Expand event handling in Step 2.

### Mistake 6 — Committing `.env`

Before the first Git commit, verify:

```bash
git status
```

and make sure `.env` is ignored.

---

## 18. Deliverables

At the end of Step 1, the repository should contain only the foundation:

```text
vasooli/
├── app/
│   ├── __init__.py
│   └── main.py
├── notes/
│   └── step-1-proof.md
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

### Step 1 deliverable statement

> **Vasooli successfully receives a real Razorpay Test Mode `subscription.pending` webhook generated by a deliberately failed test subscription charge.**

---

## 19. Exit Criteria Before Step 2

Do not begin Step 2 until:

```text
✅ Test API access works
✅ Plan exists
✅ Subscription exists
✅ Subscription reaches usable authenticated/active state
✅ Test failure can be triggered
✅ subscription.pending webhook reaches FastAPI
✅ Event ID is visible in the received request
✅ Signature header is visible
✅ Proof screenshots/logs are saved
✅ No secret has entered Git
```

Then freeze Step 1.

**Next step:** Webhook Ingestion & State Layer — signature verification, `x-razorpay-event-id` deduplication, persistent event/subscription records, and out-of-order-tolerant state reconciliation.

---

## Official References

- Razorpay — Test Subscriptions: https://razorpay.com/docs/payments/subscriptions/test/ citeturn270340search0
- Razorpay — Create and View Plans: https://razorpay.com/docs/payments/subscriptions/create-plans/ citeturn270340search1
- Razorpay — Create Subscriptions API: https://razorpay.com/docs/api/payments/subscriptions/create-subscription/ citeturn270340search5
- Razorpay — Validate and Test Webhooks: https://razorpay.com/docs/webhooks/validate-test/ citeturn270340search2
