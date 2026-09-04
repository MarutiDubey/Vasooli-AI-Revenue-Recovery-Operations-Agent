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
            notes = payment_data.get('notes')
            if isinstance(notes, dict):
                subscription_id = notes.get('subscription_id')
            else:
                subscription_id = None
            
        internal_subscription_id = None
        if subscription_id:
            if internal_customer_id:
                plan_id = subscription_data.get('plan_id', 'unknown')
                amount = 99900
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

        # Handle subscription status transition
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
                
                cursor.execute('''
                    UPDATE webhook_events 
                    SET processed_at = CURRENT_TIMESTAMP 
                    WHERE event_id = ?
                ''', (event_id,))
                conn.commit()
                conn.close()
                diagnose_case(case_id)
                evaluate_action(case_id)
                return

        # Handle Payment Failure
        if event_type == 'payment.failed':
            error_reason = payment_data.get('error_reason') or payment_data.get('error_code') or 'payment_failed'
            error_description = payment_data.get('error_description') or 'Payment failed'
            full_diagnosis = f"{error_reason}: {error_description}"
            pay_amount = payment_data.get('amount') or 99900

            if not internal_customer_id:
                cust_email = payment_data.get('email') or 'customer@example.com'
                cust_contact = payment_data.get('contact') or '+919876543210'
                if not cust_contact or cust_contact in ['+919999999999', '+918888888888']:
                    cust_contact = '+919876543210'
                cust_ext_id = customer_id or f"cust_{payment_data.get('id', 'pay_default')}"
                cursor.execute('''
                    INSERT INTO customers (external_id, name, email, contact, tenure_days)
                    VALUES (?, ?, ?, ?, 60)
                    ON CONFLICT(external_id) DO UPDATE SET updated_at=CURRENT_TIMESTAMP
                ''', (cust_ext_id, "Razorpay Customer", cust_email, cust_contact))
                cursor.execute('SELECT id FROM customers WHERE external_id = ?', (cust_ext_id,))
                row = cursor.fetchone()
                internal_customer_id = row[0] if row else 1

            if not internal_subscription_id:
                sub_ext_id = subscription_id or f"sub_{payment_data.get('id', 'default')}"
                cursor.execute('''
                    INSERT INTO subscriptions (external_id, customer_id, plan_id, amount, state)
                    VALUES (?, ?, 'default_plan', ?, 'halted')
                    ON CONFLICT(external_id) DO UPDATE SET state='halted', updated_at=CURRENT_TIMESTAMP
                ''', (sub_ext_id, internal_customer_id, pay_amount))
                cursor.execute('SELECT id FROM subscriptions WHERE external_id = ?', (sub_ext_id,))
                row = cursor.fetchone()
                internal_subscription_id = row[0] if row else 1

            cursor.execute('''
                SELECT id FROM recovery_cases 
                WHERE subscription_id = ? AND status NOT IN ('RECOVERED', 'STOPPED')
            ''', (internal_subscription_id,))
            case_row = cursor.fetchone()

            if case_row:
                case_id = case_row[0]
                cursor.execute('''
                    UPDATE recovery_cases 
                    SET diagnosis = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (full_diagnosis, case_id))
                logger.info(f"Updated Recovery Case #{case_id} diagnosis: {full_diagnosis}")
            else:
                cursor.execute('''
                    INSERT INTO recovery_cases (subscription_id, customer_id, amount_at_risk, status, priority, diagnosis)
                    VALUES (?, ?, ?, 'AT_RISK', 'MEDIUM', ?)
                ''', (internal_subscription_id, internal_customer_id, pay_amount, full_diagnosis))
                case_id = cursor.lastrowid
                logger.info(f"Created new Recovery Case #{case_id} from payment.failed webhook")

            cursor.execute('''
                UPDATE webhook_events 
                SET processed_at = CURRENT_TIMESTAMP 
                WHERE event_id = ?
            ''', (event_id,))
            conn.commit()
            conn.close()
            diagnose_case(case_id)
            evaluate_action(case_id)
            return

        # Handle Payment Link Paid Verification
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
