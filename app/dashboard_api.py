import sqlite3
import json
import logging
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from app.database import DB_PATH

logger = logging.getLogger(__name__)
router = APIRouter()


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@router.get("/api/stats")
async def get_stats():
    conn = get_db_connection()
    try:
        total_cases = conn.execute("SELECT COUNT(*) FROM recovery_cases").fetchone()[0]

        total_risk_paise = conn.execute(
            "SELECT SUM(amount_at_risk) FROM recovery_cases"
        ).fetchone()[0] or 0
        total_risk = total_risk_paise / 100

        success_links = conn.execute(
            "SELECT COUNT(*) FROM recovery_actions WHERE status = 'COMPLETED' AND action_type = 'ONE_TIME_RECOVERY'"
        ).fetchone()[0]

        total_cash_recovered_paise = conn.execute(
            "SELECT SUM(cash_amount) FROM recovery_outcomes WHERE cash_recovered = 1"
        ).fetchone()[0] or 0
        total_cash_recovered = total_cash_recovered_paise / 100

        # Average recovery score across all cases
        avg_score = conn.execute(
            "SELECT AVG(recovery_score) FROM recovery_cases"
        ).fetchone()[0] or 0

        return {
            "total_cases": total_cases,
            "total_risk_inr": total_risk,
            "success_links": success_links,
            "total_cash_recovered_inr": total_cash_recovered,
            "avg_recovery_score": round(avg_score, 1),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("/api/cases")
async def get_cases():
    conn = get_db_connection()
    try:
        query = '''
            SELECT
                rc.id as case_id,
                rc.status as case_status,
                rc.amount_at_risk,
                rc.priority,
                rc.diagnosis,
                rc.policy_decision,
                rc.recovery_score,
                rc.recovery_message,
                c.name as customer_name,
                c.email as customer_email,
                c.tenure_days,
                s.external_id as subscription_id,
                ra.razorpay_resource_id as payment_link_id,
                ra.status as action_status
            FROM recovery_cases rc
            JOIN customers c ON rc.customer_id = c.id
            JOIN subscriptions s ON rc.subscription_id = s.id
            LEFT JOIN recovery_actions ra ON ra.id = (
                SELECT id FROM recovery_actions
                WHERE case_id = rc.id
                ORDER BY id DESC LIMIT 1
            )
            ORDER BY rc.id DESC
        '''
        cases = conn.execute(query).fetchall()

        result = []
        for case in cases:
            case_dict = dict(case)
            case_dict['amount_inr'] = (case_dict['amount_at_risk'] or 0) / 100
            case_dict['recovery_score'] = case_dict.get('recovery_score') or 0
            case_dict['recovery_message'] = case_dict.get('recovery_message') or ""
            result.append(case_dict)

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.post("/api/simulate")
async def simulate_payment_failure():
    """
    Live E2E demo endpoint.
    Creates a synthetic failed payment case and runs it through
    the complete pipeline: Score → AI Diagnosis → Policy → Message.
    Returns the new case_id so the frontend can highlight it.
    """
    import random
    import time
    from app.database import init_db
    from app.ai_analyst import diagnose_case
    from app.policy_engine import evaluate_action

    init_db()  # Ensure columns exist

    FAILURE_SCENARIOS = [
        ("insufficient_funds: The customer's bank account does not have enough balance.", 99900),
        ("bank_decline: Temporary bank server outage.", 199900),
        ("card_expired: The card used for the mandate has expired.", 49900),
        ("unknown_error: Unrecognized gateway code 9982.", 999900),
        ("bank_decline: Temporary bank server outage.", 49900),
    ]
    diagnosis, amount = random.choice(FAILURE_SCENARIOS)
    ts = int(time.time())

    raw_conn = sqlite3.connect(DB_PATH)
    raw_conn.row_factory = sqlite3.Row
    cursor = raw_conn.cursor()
    try:
        # Create a demo customer
        cursor.execute('''
            INSERT OR IGNORE INTO customers (external_id, name, email, contact, tenure_days, opt_out)
            VALUES (?, ?, ?, ?, ?, 0)
        ''', (f"demo_{ts}", f"Demo User {ts}", f"demo_{ts}@vasooli.test", "9999999999", random.randint(30, 900)))
        raw_conn.commit()

        cursor.execute("SELECT id FROM customers WHERE external_id = ?", (f"demo_{ts}",))
        customer_id = cursor.fetchone()[0]

        # Create subscription
        cursor.execute('''
            INSERT OR IGNORE INTO subscriptions (external_id, customer_id, plan_id, amount, state)
            VALUES (?, ?, 'demo_plan', ?, 'halted')
        ''', (f"sub_demo_{ts}", customer_id, amount))
        raw_conn.commit()

        cursor.execute("SELECT id FROM subscriptions WHERE external_id = ?", (f"sub_demo_{ts}",))
        subscription_id = cursor.fetchone()[0]

        # Create recovery case
        cursor.execute('''
            INSERT INTO recovery_cases (subscription_id, customer_id, amount_at_risk, status, priority, diagnosis)
            VALUES (?, ?, ?, 'NEW', 'MEDIUM', ?)
        ''', (subscription_id, customer_id, amount, diagnosis))
        raw_conn.commit()
        case_id = cursor.lastrowid

    finally:
        raw_conn.close()

    # Run the full pipeline
    try:
        diagnose_case(case_id)
        evaluate_action(case_id)
    except Exception as e:
        logger.error(f"Simulate pipeline error: {e}")

    return {"success": True, "case_id": case_id, "message": f"New recovery case #{case_id} created and processed through full pipeline."}
