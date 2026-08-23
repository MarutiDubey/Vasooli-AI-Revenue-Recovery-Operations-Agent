import sqlite3
import os
import json
import logging
import requests
from pydantic import BaseModel
from app.database import DB_PATH
from app.scoring import calculate_recovery_score

logger = logging.getLogger(__name__)

TOKENIN_BASE_URL = "https://tokenin.my.id/v1/chat/completions"
TOKENIN_MODEL = "myt/gpt-5.6-sol-free"


class RecoveryRecommendation(BaseModel):
    diagnosis: str
    priority: str
    recommended_action: str
    follow_up_hours: int
    stop_conditions: list[str]
    reason: str
    confidence: float


def _get_api_key():
    return os.getenv("TOKENIN_API_KEY")


def _call_llm(prompt: str, max_tokens: int = 300) -> str | None:
    """
    Shared helper to call the TokenIn LLM.
    Returns the raw text content or None on failure.
    """
    api_key = _get_api_key()
    if not api_key:
        return None

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = {
        "model": TOKENIN_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": max_tokens,
    }
    try:
        resp = requests.post(TOKENIN_BASE_URL, headers=headers, json=data, timeout=20)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
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

Rules:
- If Customer Opt-Out Status is True, action MUST be STOP.
- If amount > 5000000 paise (50,000 INR) and reason is unclear, ESCALATE.
- If Recovery Score < 20, lean towards ESCALATE or STOP.

Output strictly valid JSON only (no markdown):
{{
    "diagnosis": "string",
    "priority": "HIGH|MEDIUM|LOW",
    "recommended_action": "MONITOR|ESCALATE|STOP|PAYMENT_METHOD_RECOVERY|ONE_TIME_RECOVERY",
    "follow_up_hours": 24,
    "stop_conditions": ["string"],
    "reason": "string",
    "confidence": 0.95
}}
"""
        content = _call_llm(prompt, max_tokens=300)
        if not content:
            _fallback_escalate(case_id, "LLM call returned empty response")
            return

        # Strip markdown fences if present
        if "```" in content:
            content = content.split("```")[1]
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
- If action is MONITOR: reassure them, say it may resolve automatically, no action needed
- If action is PAYMENT_METHOD_RECOVERY: ask them to update their payment method
- If action is ESCALATE: tell them a team member will reach out
- Be warm, empathetic. Do NOT use marketing language or urgency pressure.
- Output ONLY the message text. No subject line. No greeting prefix.
"""
        message = _call_llm(prompt, max_tokens=120)
        if not message:
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


def _fallback_escalate(case_id: int, reason: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    fallback_json = json.dumps({
        "diagnosis": "FALLBACK_TRIGGERED",
        "priority": "HIGH",
        "recommended_action": "ESCALATE",
        "follow_up_hours": 0,
        "stop_conditions": [],
        "reason": f"AI failure fallback: {reason}",
        "confidence": 0.0
    })
    cursor.execute('''
        UPDATE recovery_cases
        SET ai_recommendation = ?, status = 'PLAN_READY', updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (fallback_json, case_id))
    conn.commit()
    conn.close()
