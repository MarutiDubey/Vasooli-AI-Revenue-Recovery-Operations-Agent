import sqlite3
import json
import logging
from app.database import DB_PATH
from app.action_executor import execute_pending_actions

logger = logging.getLogger(__name__)

def evaluate_action(case_id: int):
    """
    Evaluates the AI's recommendation against hard policy rules.
    If the policy overrides the AI, it logs the reason.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT rc.amount_at_risk, rc.status, rc.ai_recommendation, 
                   c.opt_out, s.state
            FROM recovery_cases rc
            JOIN customers c ON rc.customer_id = c.id
            JOIN subscriptions s ON rc.subscription_id = s.id
            WHERE rc.id = ?
        ''', (case_id,))
        row = cursor.fetchone()
        if not row:
            logger.error(f"Case {case_id} not found.")
            return

        amount_at_risk, status, ai_rec_json, opt_out, sub_state = row
        
        if status != 'PLAN_READY':
            logger.warning(f"Case {case_id} is in {status}, expected PLAN_READY.")
            return

        ai_rec = {}
        if ai_rec_json:
            try:
                ai_rec = json.loads(ai_rec_json)
            except:
                pass
                
        ai_action = ai_rec.get("recommended_action", "ESCALATE")
        
        # Guardrail Checks
        final_decision = None
        override_reason = None
        
        if opt_out:
            final_decision = "STOP"
            override_reason = "Rule 1: customer_opt_out = True"
        elif sub_state == "cancelled":
            final_decision = "STOP"
            override_reason = "Rule 4: subscription_state = cancelled"
        elif amount_at_risk > 5000000: # 50,000 INR limit
            final_decision = "ESCALATE"
            override_reason = "Rule 6: amount > escalation_threshold (50k)"
        elif ai_action not in ["MONITOR", "ESCALATE", "STOP", "PAYMENT_METHOD_RECOVERY", "ONE_TIME_RECOVERY"]:
            final_decision = "ESCALATE"
            override_reason = f"Rule 7: unsupported_action_requested ({ai_action})"
        else:
            final_decision = ai_action
            
        new_status = "ACTION_APPROVED"
        
        cursor.execute('''
            UPDATE recovery_cases
            SET policy_decision = ?, policy_override_reason = ?, status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (final_decision, override_reason, new_status, case_id))
        
        # Also create a recovery_actions record
        cursor.execute('''
            INSERT INTO recovery_actions (case_id, action_type, status, ai_recommended, policy_approved, reason)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (case_id, final_decision, "PENDING", ai_action == final_decision, True, override_reason or "AI Recommendation Approved"))
        
        conn.commit()
        logger.info(f"Policy Engine evaluated case {case_id}: Final Decision = {final_decision}")
        
        # Trigger Action Executor
        execute_pending_actions()
        
    except Exception as e:
        logger.error(f"Policy Engine failed for case {case_id}: {e}")
    finally:
        conn.close()
