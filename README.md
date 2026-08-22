# Vasooli - AI Revenue Recovery Operations Agent 🤖💸

**A Razorpay Buildathon Submission (Track 03 - AI/ML Integration)**

Vasooli is an autonomous, AI-driven backend engine designed to intercept failed payments and churn risks on subscriptions, instantly diagnose the problem using LLMs, and autonomously generate and dispatch Razorpay Payment Links to recover the revenue—all without human intervention.

## 🌟 The Problem
SaaS businesses and subscription models lose significant revenue to "involuntary churn"—when a subscription renewal fails due to insufficient funds, an expired card, or banking network issues. Operations teams waste countless hours manually following up with customers to recover these payments.

## 🎯 The Solution: Vasooli
Vasooli sits as an autonomous layer between Razorpay Webhooks and the Razorpay Payment REST APIs. 

1. **Ingestion**: Listens to Razorpay Webhooks (e.g., `payment.failed`, `subscription.pending`).
2. **State Mapping**: Identifies the customer, subscription, and amount at risk using a robust SQLite state machine.
3. **AI Diagnosis (Gemma via OpenRouter)**: Analyzes the failure reason and customer tenure to determine the best recovery strategy (e.g., generating a one-time link, escalating, or waiting).
4. **Policy Guardrails**: Enforces deterministic business rules to ensure the AI doesn't perform unauthorized actions (e.g., maximum recovery attempts).
5. **Execution**: Autonomously calls Razorpay APIs to generate a Recovery Payment Link and dispatches it.
6. **Control Tower**: A stunning React dashboard to visualize the entire autonomous pipeline.

---

## 🏗️ Architecture

- **Backend**: FastAPI (Python)
- **Database**: SQLite (transactional, relational state mapping)
- **AI Engine**: Google Gemma 4 (31b) via OpenRouter API
- **Frontend**: React + Vite + Vanilla CSS (Minimalist Razorpay Theme)
- **Payments**: Razorpay Webhooks & Payment Links API

---

## 🚀 How to Run Locally

### 1. Clone the repository
```bash
git clone https://github.com/MarutiDubey/Vasooli-AI-Revenue-Recovery-Operations-Agent.git
cd Vasooli-AI-Revenue-Recovery-Operations-Agent
```

### 2. Setup Backend (FastAPI)
```bash
# Create virtual environment
python -m venv .venv
source .venv/Scripts/activate  # On Windows

# Install dependencies
pip install -r requirements.txt

# Create .env file
# Add: RAZORPAY_WEBHOOK_SECRET, OPENROUTER_API_KEY, RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET

# Run the backend
uvicorn app.main:app --reload
```

### 3. Setup Frontend (React Control Tower)
```bash
cd frontend
npm install
npm run dev
```

### 4. Trigger a Simulation
Open a new terminal and simulate a Razorpay Webhook:
```bash
source .venv/Scripts/activate
python scripts/simulate_webhook.py payment.failed
```
Watch the AI diagnose the failure and instantly generate a recovery link in your React Dashboard!

---

## 🛡️ Built for Resilience
Vasooli is designed for enterprise reliability:
- **HMAC Signature Verification** on all incoming webhooks.
- **Idempotency**: Safely handles duplicate webhook deliveries using `x-razorpay-event-id`.
- **AI Fallbacks**: If the LLM API is rate-limited or goes down, the system gracefully falls back to a deterministic `ESCALATE` state without crashing.
