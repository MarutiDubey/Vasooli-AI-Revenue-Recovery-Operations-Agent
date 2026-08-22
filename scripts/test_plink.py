import sys
sys.path.insert(0, '.')

import sqlite3
import json
from dotenv import load_dotenv
load_dotenv()

# Inject ONE_TIME_RECOVERY action
conn = sqlite3.connect('vasooli.db')
cursor = conn.cursor()
cursor.execute('UPDATE recovery_cases SET status=? WHERE id=?', ('PLAN_READY', 1))
cursor.execute(
    'INSERT INTO recovery_actions (case_id, action_type, status, ai_recommended, policy_approved, reason) VALUES (?,?,?,?,?,?)',
    (1, 'ONE_TIME_RECOVERY', 'PENDING', 1, 1, 'Recovery via Payment Link')
)
conn.commit()
conn.close()

from app.action_executor import execute_pending_actions
print('Executing ONE_TIME_RECOVERY...')
execute_pending_actions()

conn = sqlite3.connect('vasooli.db')
rows = conn.execute('SELECT id, action_type, status, razorpay_resource_id FROM recovery_actions ORDER BY id DESC LIMIT 3').fetchall()
conn.close()
print('Results:', rows)
