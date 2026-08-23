import sqlite3
import logging
from app.database import DB_PATH
from app.razorpay_client import create_payment_link

logger = logging.getLogger(__name__)

def execute_pending_actions():
    """
    Finds all PENDING actions in recovery_actions and executes them.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT ra.id, ra.action_type, rc.amount_at_risk, c.name, c.email, c.contact, rc.id as case_id
            FROM recovery_actions ra
            JOIN recovery_cases rc ON ra.case_id = rc.id
            JOIN customers c ON rc.customer_id = c.id
            WHERE ra.status = 'PENDING'
        ''')
        pending_actions = cursor.fetchall()
        
        for action in pending_actions:
            action_id, action_type, amount, name, email, contact, case_id = action
            logger.info(f"Executing action {action_id} ({action_type}) for Case {case_id}")
            
            if action_type == 'ONE_TIME_RECOVERY':
                desc = f"Vasooli Revenue Recovery for Case {case_id}"
                plink_response = create_payment_link(amount, name, email, contact, desc)
                
                if plink_response:
                    plink_id = plink_response.get('id')
                    cursor.execute('''
                        UPDATE recovery_actions
                        SET status = 'COMPLETED', razorpay_resource_id = ?, executed_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (plink_id, action_id))
                    logger.info(f"Payment Link {plink_id} created for Case {case_id}")
                else:
                    cursor.execute('''
                        UPDATE recovery_actions
                        SET status = 'FAILED', executed_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (action_id,))
                    logger.error(f"Failed to create Payment Link for Case {case_id}")
                    
            elif action_type == 'ONE_TIME_RECOVERY_PARTIAL':
                desc = f"Vasooli Partial Revenue Recovery for Case {case_id}"
                # minimum partial amount set to roughly 33%
                min_partial = amount // 3
                plink_response = create_payment_link(amount, name, email, contact, desc, accept_partial=True, first_min_partial_amount=min_partial)
                
                if plink_response:
                    plink_id = plink_response.get('id')
                    cursor.execute('''
                        UPDATE recovery_actions
                        SET status = 'COMPLETED', razorpay_resource_id = ?, executed_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (plink_id, action_id))
                    logger.info(f"Partial Payment Link {plink_id} created for Case {case_id} (Min: {min_partial})")
                else:
                    cursor.execute('''
                        UPDATE recovery_actions
                        SET status = 'FAILED', executed_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (action_id,))
                    logger.error(f"Failed to create Partial Payment Link for Case {case_id}")

            elif action_type in ['ESCALATE', 'STOP', 'MONITOR', 'PAYMENT_METHOD_RECOVERY']:
                cursor.execute('''
                    UPDATE recovery_actions
                    SET status = 'COMPLETED', executed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (action_id,))
                logger.info(f"Action {action_type} for Case {case_id} marked as COMPLETED.")
                
            else:
                logger.warning(f"Unsupported action type: {action_type}")
                
        conn.commit()
    except Exception as e:
        logger.error(f"Error executing pending actions: {e}")
    finally:
        conn.close()
