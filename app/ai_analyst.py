import sqlite3
import os
import json
import logging
import requests
from pydantic import BaseModel, ValidationError
from app.database import DB_PATH

logger = logging.getLogger(__name__)

class RecoveryRecommendation(BaseModel):
    diagnosis: str
    priority: str
    recommended_action: str
    follow_up_hours: int
    stop_conditions: list[str]
    reason: str
    confidence: float

def diagnose_case(case_id: int):
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        logger.error("OPENROUTER_API_KEY not found. Falling back to ESCALATE.")
        _fallback_escalate(case_id, "Missing API Key")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT rc.amount_at_risk, rc.status, rc.diagnosis, c.tenure_days, c.opt_out, s.state
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
        
        prompt = f"""
        You are the Vasooli AI Recovery Analyst. Diagnose the following failed payment case and recommend a recovery action.
        
        Case Details:
        - Amount at Risk (paise): {amount_at_risk}
        - Subscription State: {sub_state}
        - Current Diagnosis / Error: {diagnosis}
        - Customer Tenure (days): {tenure_days}
        - Customer Opt-Out Status: {bool(opt_out)}
        
        Available Actions:
        - MONITOR: Self-recovery likely via Razorpay native retry.
        - ESCALATE: High-value, complex, or unknown failure requiring manual review.
        - STOP: Opted out or mandate cancelled. Do not contact.
        - PAYMENT_METHOD_RECOVERY: Card or UPI issue requires a new mandate/update.
        - ONE_TIME_RECOVERY: Subscription halted; one-off payment needed via Payment Link.
        
        Rules:
        - If Customer Opt-Out Status is True, action MUST be STOP.
        - If amount is very large and reason is unclear, ESCALATE.
        Prompt:
        Output strictly valid JSON matching this schema:
        {{
            "diagnosis": "string",
            "priority": "HIGH|MEDIUM|LOW",
            "recommended_action": "MONITOR|ESCALATE|STOP|PAYMENT_METHOD_RECOVERY|ONE_TIME_RECOVERY",
            "follow_up_hours": 24,
            "stop_conditions": ["string"],
            "reason": "string",
            "confidence": 0.95
        }}
        Do not output any markdown formatting, only the JSON.
        """
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "Vasooli"
        }
        
        data = {
            "model": "google/gemma-4-31b-it:free",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1
        }
        
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=15)
        response.raise_for_status()
        
        result = response.json()
        recommendation_json = result['choices'][0]['message']['content'].strip()
        
        # Clean up markdown if present
        if recommendation_json.startswith("```json"):
            recommendation_json = recommendation_json.replace("```json", "", 1)
        if recommendation_json.endswith("```"):
            recommendation_json = recommendation_json[:-3]
        recommendation_json = recommendation_json.strip()
        
        # Validate schema
        parsed_rec = json.loads(recommendation_json)
        RecoveryRecommendation(**parsed_rec)
        
        cursor.execute('''
            UPDATE recovery_cases 
            SET ai_recommendation = ?, status = 'PLAN_READY', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (recommendation_json, case_id))
        conn.commit()
        logger.info(f"AI Analyst successfully diagnosed case {case_id}")
        
    except Exception as e:
        logger.error(f"AI Analyst failed for case {case_id}: {e}")
        _fallback_escalate(case_id, str(e))
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
