import sqlite3
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from app.database import DB_PATH

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
        
        total_risk_paise = conn.execute("SELECT SUM(amount_at_risk) FROM recovery_cases").fetchone()[0] or 0
        total_risk = total_risk_paise / 100

        success_links = conn.execute("SELECT COUNT(*) FROM recovery_actions WHERE status = 'COMPLETED' AND action_type = 'ONE_TIME_RECOVERY'").fetchone()[0]
        
        total_cash_recovered_paise = conn.execute("SELECT SUM(cash_amount) FROM recovery_outcomes WHERE cash_recovered = 1").fetchone()[0] or 0
        total_cash_recovered = total_cash_recovered_paise / 100

        return {
            "total_cases": total_cases,
            "total_risk_inr": total_risk,
            "success_links": success_links,
            "total_cash_recovered_inr": total_cash_recovered
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
                c.name as customer_name,
                c.email as customer_email,
                s.external_id as subscription_id,
                ra.razorpay_resource_id as payment_link_id,
                ra.status as action_status
            FROM recovery_cases rc
            JOIN customers c ON rc.customer_id = c.id
            JOIN subscriptions s ON rc.subscription_id = s.id
            LEFT JOIN recovery_actions ra ON ra.case_id = rc.id
            ORDER BY rc.id DESC
        '''
        cases = conn.execute(query).fetchall()
        
        result = []
        for case in cases:
            case_dict = dict(case)
            case_dict['amount_inr'] = case_dict['amount_at_risk'] / 100
            result.append(case_dict)
            
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
