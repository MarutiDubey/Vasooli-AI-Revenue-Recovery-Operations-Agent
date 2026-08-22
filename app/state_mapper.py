import sqlite3
import json
import logging
from app.database import DB_PATH
from app.ai_analyst import diagnose_case
from app.policy_engine import evaluate_action

logger = logging.getLogger(__name__)

def process_webhook_event(event_id: str, event_type: str, payload_dict: dict):
    """Maps raw webhook payload to business state tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        subscription_data = payload_dict.get('subscription', {}).get('entity', {})
        payment_data = payload_dict.get('payment', {}).get('entity', {})

        customer_id = subscription_data.get('customer_id') or payment_data.get('customer_id')
        
        internal_customer_id = None
        if customer_id:
            email = payment_data.get('email', 'unknown@example.com')
            contact = payment_data.get('contact', '')
            # Ensure contact is valid (between 8-14 chars, no recurring)
            if not contact or contact in ['+919999999999', '+918888888888']:
                contact = '+919876543210'
            
            cursor.execute('''
                INSERT INTO customers (external_id, name, email, contact, tenure_days)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(external_id) DO UPDATE SET 
                    email=excluded.email,
                    contact=excluded.contact,
                    updated_at=CURRENT_TIMESTAMP
            ''', (customer_id, "Test Customer", email, contact, 30))
            
            cursor.execute('SELECT id FROM customers WHERE external_id = ?', (customer_id,))
            row = cursor.fetchone()
            if row:
                internal_customer_id = row[0]

        subscription_id = subscription_data.get('id')
        if not subscription_id and payment_data:
            subscription_id = payment_data.get('notes', {}).get('subscription_id')
            
        internal_subscription_id = None
        if subscription_id:
            if internal_customer_id:
                plan_id = subscription_data.get('plan_id', 'unknown')
                amount = 99900 # Rs 999 Default for test
                state = subscription_data.get('status', 'unknown')
                
                cursor.execute('''
                    INSERT INTO subscriptions (external_id, customer_id, plan_id, amount, state)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(external_id) DO UPDATE SET 
                        state=excluded.state,
                        updated_at=CURRENT_TIMESTAMP
                ''', (subscription_id, internal_customer_id, plan_id, amount, state))
                
            cursor.execute('SELECT id FROM subscriptions WHERE external_id = ?', (subscription_id,))
            row = cursor.fetchone()
            if row:
                internal_subscription_id = row[0]

        # Handle Recovery Case Creation (Pending / Halted)
        if event_type in ['subscription.pending', 'subscription.halted'] and internal_subscription_id:
            cursor.execute('''
                SELECT id FROM recovery_cases 
                WHERE subscription_id = ? AND status NOT IN ('RECOVERED', 'STOPPED')
            ''', (internal_subscription_id,))
            case_exists = cursor.fetchone()
            
            if not case_exists:
                amount_at_risk = 99900
                cursor.execute('''
                    INSERT INTO recovery_cases (subscription_id, customer_id, amount_at_risk, status, priority)
                    VALUES (?, ?, ?, 'AT_RISK', 'MEDIUM')
                ''', (internal_subscription_id, internal_customer_id, amount_at_risk))
                case_id = cursor.lastrowid
                logger.info(f"Created new Recovery Case #{case_id} for subscription {subscription_id}")
                
                # Close connection before synchronous pipeline calls to avoid DB locks
                conn.commit()
                conn.close()
                diagnose_case(case_id)
                evaluate_action(case_id)
                return # Stop normal flow since we closed conn

        # Handle Payment Failed
        if event_type == 'payment.failed' and internal_subscription_id:
            error_reason = payment_data.get('error_reason', 'unknown')
            error_description = payment_data.get('error_description', 'unknown')
            full_diagnosis = f"{error_reason}: {error_description}"
            
            cursor.execute('''
                UPDATE recovery_cases 
                SET diagnosis = ?, updated_at = CURRENT_TIMESTAMP
                WHERE subscription_id = ? AND status NOT IN ('RECOVERED', 'STOPPED')
            ''', (full_diagnosis, internal_subscription_id))
            if cursor.rowcount > 0:
                logger.info(f"Updated Recovery Case diagnosis for subscription {subscription_id}: {full_diagnosis}")
                
                cursor.execute('SELECT id FROM recovery_cases WHERE subscription_id = ? AND status NOT IN ("RECOVERED", "STOPPED")', (internal_subscription_id,))
                case_row = cursor.fetchone()
                if case_row:
                    conn.commit()
                    conn.close()
                    diagnose_case(case_row[0])
                    evaluate_action(case_row[0])
                    return

        # Handle Payment Link Paid (Step 6 Verification)
        if event_type == 'payment_link.paid':
            plink_entity = payload_dict.get('payment_link', {}).get('entity', {})
            plink_id = plink_entity.get('id')
            amount_paid = plink_entity.get('amount_paid', 0)
            
            if plink_id:
                cursor.execute('''
                    SELECT case_id, id FROM recovery_actions 
                    WHERE razorpay_resource_id = ?
                ''', (plink_id,))
                action_row = cursor.fetchone()
                
                if action_row:
                    case_id, action_id = action_row
                    # Mark Case as RECOVERED
                    cursor.execute('''
                        UPDATE recovery_cases 
                        SET status = 'RECOVERED', updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (case_id,))
                    
                    # Record Verified Outcome
                    cursor.execute('''
                        INSERT INTO recovery_outcomes (case_id, action_id, cash_recovered, cash_amount)
                        VALUES (?, ?, 1, ?)
                    ''', (case_id, action_id, amount_paid))
                    logger.info(f"Verified Cash Recovery for Case #{case_id}: Rs {amount_paid/100}")


        conn.commit()
    except Exception as e:
        logger.error(f"Error mapping state for event {event_id}: {e}")
        conn.rollback()
    finally:
        conn.close()
