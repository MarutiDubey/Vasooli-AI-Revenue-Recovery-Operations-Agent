import sqlite3
import os
import json
import logging
import requests
from pydantic import BaseModel
from app.database import DB_PATH
from app.scoring import calculate_recovery_score

logger = logging.getLogger(__name__)

TOKENIN_BASE_URL = os.getenv("TOKENIN_BASE_URL", "https://tokenin.my.id/v1/chat/completions")
TOKENIN_MODEL = os.getenv("TOKENIN_MODEL", "nvidia/meta/llama-3.2-11b-vision-instruct")

OMNIROUTE_BASE_URL = os.getenv("OMNIROUTE_BASE_URL", "http://localhost:20128/v1/chat/completions")
OMNIROUTE_MODEL = os.getenv("OMNIROUTE_MODEL", "nvidia/nvidia/nemotron-3-super-120b-a12b")

OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1/chat/completions")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3.5-lightning:free")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "omniroute")


class RecoveryRecommendation(BaseModel):
    diagnosis: str
    priority: str
    recommended_action: str
    follow_up_hours: int
    stop_conditions: list[str]
    reason: str
    confidence: float


def _call_llm(prompt: str, max_tokens: int = 500) -> str | None:
    """
    Calls configured LLM provider (OpenRouter or TokenIn).
    Returns the raw text content or None on failure.
    """
    provider = os.getenv("LLM_PROVIDER", "openrouter").lower()

    if provider == "omniroute":
        url = os.getenv("OMNIROUTE_BASE_URL", "http://localhost:20128/v1/chat/completions")
        model = os.getenv("OMNIROUTE_MODEL", "nvidia/openai/gpt-oss-20b")
        headers = {
            "Content-Type": "application/json",
        }
    elif provider == "openrouter":
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            return None
        url = OPENROUTER_BASE_URL
        model = os.getenv("OPENROUTER_MODEL", OPENROUTER_MODEL)
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5173",
            "X-Title": "Vasooli AI",
        }
    else:
        api_key = os.getenv("TOKENIN_API_KEY")
        if not api_key:
            return None
        url = TOKENIN_BASE_URL
        model = os.getenv("TOKENIN_MODEL", TOKENIN_MODEL)
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": max_tokens,
    }
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=12)
        resp.raise_for_status()
        resp.encoding = "utf-8"
        
        # Handle Server-Sent Events (SSE) stream format
        if resp.text.startswith("data:"):
            full_content = ""
            for line in resp.text.splitlines():
                if line.startswith("data: ") and line.strip() != "data: [DONE]":
                    try:
                        chunk = json.loads(line[6:])
                        delta = chunk["choices"][0].get("delta", {})
                        full_content += delta.get("content", "")
                    except:
                        pass
            cleaned = full_content.strip().replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
            return cleaned
            
        raw = resp.json()["choices"][0]["message"]["content"].strip()
        return raw.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    except Exception as e:
        logger.error(f"LLM call to {provider} ({model}) failed: {e}")
        return None


def diagnose_case(case_id: int):
    """
    Step 1 of the AI pipeline:
    - Calculates recovery_score (deterministic, instant)
    - Calls LLM for structured diagnosis + recommended action
    - Saves both to DB
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT rc.amount_at_risk, rc.status, rc.diagnosis,
                   c.tenure_days, c.opt_out, s.state
            FROM recovery_cases rc
            JOIN customers c ON rc.customer_id = c.id
            JOIN subscriptions s ON rc.subscription_id = s.id
            WHERE rc.id = ?
        ''', (case_id,))
        row = cursor.fetchone()
        if not row:
            logger.error(f"Case {case_id} not found.")
            return

        amount_at_risk, status, diagnosis, tenure_days, opt_out, sub_state = row

        # --- Recovery Score (deterministic, no LLM) ---
        score = calculate_recovery_score(
            tenure_days=tenure_days or 0,
            diagnosis=diagnosis or "",
            amount_paise=amount_at_risk or 0,
            opt_out=bool(opt_out),
        )
        cursor.execute(
            "UPDATE recovery_cases SET recovery_score = ? WHERE id = ?",
            (score, case_id)
        )
        conn.commit()
        logger.info(f"Case {case_id}: recovery_score = {score}")

        # --- LLM Diagnosis ---
        prompt = f"""
You are the Vasooli AI Recovery Analyst. Diagnose the following failed payment case and recommend a recovery action.

Case Details:
- Amount at Risk (paise): {amount_at_risk}
- Subscription State: {sub_state}
- Current Diagnosis / Error: {diagnosis}
- Customer Tenure (days): {tenure_days}
- Customer Opt-Out Status: {bool(opt_out)}
- Recovery Probability Score: {score}/100

Available Actions:
- MONITOR: Self-recovery likely via Razorpay native retry.
- ESCALATE: High-value, complex, or unknown failure requiring manual review.
- STOP: Opted out or mandate cancelled. Do not contact.
- PAYMENT_METHOD_RECOVERY: Card or UPI issue requires a new mandate/update.
- ONE_TIME_RECOVERY: Subscription halted; one-off payment needed via Payment Link.
- ONE_TIME_RECOVERY_PARTIAL: Subscription halted; one-off payment needed but customer has insufficient funds, allow them to pay 30% to avoid churn.

Rules:
- If Customer Opt-Out Status is True, action MUST be STOP.
- If amount > 5000000 paise (50,000 INR) and reason is unclear, ESCALATE.
- If diagnosis indicates insufficient funds, strictly use ONE_TIME_RECOVERY_PARTIAL to allow the user to pay 30% now and keep the subscription active.
- If Recovery Score < 20, lean towards ESCALATE or STOP.

Output strictly valid JSON only (no markdown):
{{
    "diagnosis": "string",
    "priority": "HIGH|MEDIUM|LOW",
    "recommended_action": "MONITOR|ESCALATE|STOP|PAYMENT_METHOD_RECOVERY|ONE_TIME_RECOVERY|ONE_TIME_RECOVERY_PARTIAL",
    "follow_up_hours": 24,
    "stop_conditions": ["string"],
    "reason": "string",
    "confidence": 0.95
}}
"""
        content = _call_llm(prompt, max_tokens=2048)
        if not content:
            _fallback_escalate(case_id, "LLM call returned empty response")
            return

        # Strip markdown fences if present
        if "```" in content:
            parts = content.split("```")
            content = parts[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()

        parsed_rec = json.loads(content)
        RecoveryRecommendation(**parsed_rec)

        cursor.execute('''
            UPDATE recovery_cases
            SET ai_recommendation = ?, status = 'PLAN_READY', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (json.dumps(parsed_rec), case_id))
        conn.commit()
        logger.info(f"AI Analyst diagnosed case {case_id}: {parsed_rec.get('recommended_action')}")

    except Exception as e:
        logger.error(f"AI Analyst failed for case {case_id}: {e}")
        _fallback_escalate(case_id, str(e))
    finally:
        conn.close()


def generate_recovery_message(case_id: int):
    """
    Step 2 of the AI pipeline (runs after policy approval):
    - Generates a short, personalized WhatsApp/SMS-style recovery message
    - Only for non-STOP cases
    - Saves to recovery_cases.recovery_message
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT rc.amount_at_risk, rc.diagnosis, rc.policy_decision,
                   rc.recovery_score, c.name, c.tenure_days
            FROM recovery_cases rc
            JOIN customers c ON rc.customer_id = c.id
            WHERE rc.id = ?
        ''', (case_id,))
        row = cursor.fetchone()
        if not row:
            logger.error(f"Case {case_id} not found for message generation.")
            return

        amount_paise, diagnosis, policy_decision, score, customer_name, tenure_days = row

        # Don't generate messages for STOP cases
        if policy_decision == "STOP":
            return

        amount_inr = (amount_paise or 0) / 100
        first_name = (customer_name or "Customer").split()[0]
        tenure_years = round((tenure_days or 0) / 365, 1)

        prompt = f"""
You are Vasooli, a friendly AI recovery assistant for a SaaS payment platform.

Write a SHORT, warm, and helpful WhatsApp/SMS message (max 3 sentences) for a customer whose payment failed.
The message must feel personal, NOT like a spam template.

Customer Info:
- First Name: {first_name}
- Tenure with platform: {tenure_years} years
- Amount failed (INR): ₹{amount_inr:,.0f}
- Failure Reason: {diagnosis}
- Recovery Action Decided: {policy_decision}
- Recovery Score: {score}/100

Instructions:
- If action is ONE_TIME_RECOVERY: mention a secure payment link will be/has been sent
- If action is ONE_TIME_RECOVERY_PARTIAL: Explicitly state that we understand funds might be low, so we have enabled a "Partial Payment" option allowing them to pay just 30% of the amount for now to keep their service active.
- If action is MONITOR: reassure them, say it may resolve automatically, no action needed
- If action is PAYMENT_METHOD_RECOVERY: ask them to update their payment method
- If action is ESCALATE: tell them a team member will reach out
- Be warm, empathetic. Do NOT use marketing language or urgency pressure.
- Output ONLY the message text. No subject line. No greeting prefix.
"""
        # Dynamic message generation with robust context-aware messages
        try:
            llm_msg = _call_llm(prompt, max_tokens=1024)
            if llm_msg and len(llm_msg.strip()) > 10:
                message = llm_msg.strip().strip('"').strip("'")
            elif policy_decision == "ONE_TIME_RECOVERY_PARTIAL":
                message = f"Hi {first_name}, we noticed your payment failed due to low balance. We have enabled a partial payment option so you can pay 30% now and keep your account active."
            elif policy_decision == "MONITOR":
                message = f"Hi {first_name}, your payment of ₹{amount_inr:,.0f} had a temporary bank server issue. No action needed—we'll retry automatically."
            elif policy_decision == "PAYMENT_METHOD_RECOVERY":
                message = f"Hi {first_name}, your card on file has expired. Please tap the link to update your payment method and avoid service interruption."
            elif policy_decision == "ESCALATE":
                message = f"Hi {first_name}, your payment of ₹{amount_inr:,.0f} is being reviewed by our priority team who will contact you directly."
            else:
                message = f"Hi {first_name}, your payment of ₹{amount_inr:,.0f} failed. Our team is reviewing it and will help you resolve it shortly."
        except Exception:
            if policy_decision == "ONE_TIME_RECOVERY_PARTIAL":
                message = f"Hi {first_name}, we noticed your payment failed due to low balance. We have enabled a partial payment option so you can pay 30% now and keep your account active."
            elif policy_decision == "MONITOR":
                message = f"Hi {first_name}, your payment of ₹{amount_inr:,.0f} had a temporary bank server issue. No action needed—we'll retry automatically."
            elif policy_decision == "PAYMENT_METHOD_RECOVERY":
                message = f"Hi {first_name}, your card on file has expired. Please tap the link to update your payment method and avoid service interruption."
            elif policy_decision == "ESCALATE":
                message = f"Hi {first_name}, your payment of ₹{amount_inr:,.0f} is being reviewed by our priority team who will contact you directly."
            else:
                message = f"Hi {first_name}, your payment of ₹{amount_inr:,.0f} failed. Our team is reviewing it and will help you resolve it shortly."


        cursor.execute(
            "UPDATE recovery_cases SET recovery_message = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (message, case_id)
        )
        conn.commit()
        logger.info(f"Recovery message generated for case {case_id}")

    except Exception as e:
        logger.error(f"Message generation failed for case {case_id}: {e}")
    finally:
        conn.close()


def _fallback_escalate(case_id: int, reason: str = "Unknown"):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT rc.amount_at_risk, rc.diagnosis, c.opt_out 
            FROM recovery_cases rc
            JOIN customers c ON rc.customer_id = c.id
            WHERE rc.id = ?
        ''', (case_id,))
        row = cursor.fetchone()
        amount_at_risk = row[0] if row else 0
        diag = (row[1] if row else "").lower()
        opt_out = bool(row[2]) if row else False

        if opt_out:
            action = "STOP"
            priority = "LOW"
            diag_tag = "customer_opted_out"
            reason_msg = "Customer opted out. Halting all recovery attempts."
        elif "bank_decline" in diag or "outage" in diag or "bank" in diag:
            action = "MONITOR"
            priority = "LOW"
            diag_tag = "temporary_bank_outage"
            reason_msg = "Bank server decline detected. Recommend MONITOR to allow native retry without contacting customer."
        elif "insufficient_funds" in diag or "balance" in diag:
            action = "ONE_TIME_RECOVERY_PARTIAL"
            priority = "MEDIUM"
            diag_tag = "insufficient_funds_detected"
            reason_msg = "Low balance detected. Recommending 30% partial payment link to retain customer."
        elif "card_expired" in diag or "expired" in diag:
            action = "PAYMENT_METHOD_RECOVERY"
            priority = "HIGH"
            diag_tag = "card_expired_detected"
            reason_msg = "Mandate card expired. Requesting updated payment instrument."
        elif amount_at_risk > 5000000:
            action = "ESCALATE"
            priority = "HIGH"
            diag_tag = "high_value_transaction"
            reason_msg = "Transaction > ₹50,000 exceeds automated threshold. Routing to VIP ops."
        else:
            action = "ESCALATE"
            priority = "HIGH"
            diag_tag = "unknown_gateway_error"
            reason_msg = "Unmapped error code. Escalating for manual review."

        fallback_json = json.dumps({
            "diagnosis": diag_tag,
            "priority": priority,
            "recommended_action": action,
            "reason": reason_msg,
            "confidence": 0.95
        })
        cursor.execute('''
            UPDATE recovery_cases
            SET ai_recommendation = ?, status = 'PLAN_READY', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (fallback_json, case_id))
        conn.commit()
    finally:
        conn.close()
